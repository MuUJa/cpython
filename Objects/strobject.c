#include "Python.h"
#include "strobject.h"
#include "pycore_object.h"
#include "pycore_bytesobject.h"   // _PyBytes_Repeat()
#include "pycore_modsupport.h"    // _PyArg_CheckPositional()


#if (SIZEOF_SIZE_T == 8)
/* Mask to quickly check whether a C 'size_t' contains a
   non-ASCII, UTF8-encoded char. */
# define ASCII_CHAR_MASK 0x8080808080808080ULL
// used to count codepoints in UTF-8 string.
# define VECTOR_0101     0x0101010101010101ULL
# define VECTOR_00FF     0x00ff00ff00ff00ffULL
#elif (SIZEOF_SIZE_T == 4)
# define ASCII_CHAR_MASK 0x80808080U
# define VECTOR_0101     0x01010101U
# define VECTOR_00FF     0x00ff00ffU
#else
# error C 'size_t' size should be either 4 or 8!
#endif

/* helper macro to fixup start/end slice values */
#define ADJUST_INDICES(start, end, len) \
    do {                                \
        if (end > len) {                \
            end = len;                  \
        }                               \
        else if (end < 0) {             \
            end += len;                 \
            if (end < 0) {              \
                end = 0;                \
            }                           \
        }                               \
        if (start < 0) {                \
            start += len;               \
            if (start < 0) {            \
                start = 0;              \
            }                           \
        }                               \
    } while (0)

// StringZilla like
int export_string_like(PyObject *object, const char **data, Py_ssize_t *byte_count) {
    if (PyUnicode_Check(object)) {
        // Handle Python `str` object
        *data = PyUnicode_AsUTF8AndSize(object, byte_count);
        if (*data == NULL) {
            return 0;
        }
        return 1;
    }
    else if (PyBytes_Check(object)) {
        // Handle Python `bytes` object
        // https://docs.python.org/3/c-api/bytes.html
        if (PyBytes_AsStringAndSize(object, (char **)data, byte_count) == -1) {
            PyErr_SetString(PyExc_ValueError, "Couldn't access `bytes` buffer internals");
            return 0;
        }
        return 1;
    }
    else if (PyByteArray_Check(object)) {
        // Handle Python mutable `bytearray` object
        // https://docs.python.org/3/c-api/bytearray.html
        *data = PyByteArray_AS_STRING(object);
        *byte_count = PyByteArray_GET_SIZE(object);
        return 1;
    }
    else if (PyObject_TypeCheck(object, &PyUTF8Str_Type)) {
        *data = PyUTF8Str_DATA(object);
        *byte_count = PyUTF8Str_BYTE_COUNT(object);
        return 1;
    }
    else if (PyMemoryView_Check(object)) {
        // Handle Python `memoryview` object
        // https://docs.python.org/3/c-api/memoryview.html
        // https://docs.python.org/3/c-api/buffer.html#c.Py_buffer
        Py_buffer *view = PyMemoryView_GET_BUFFER(object);
        // Make sure we are dealing with single-byte integral representations
        if (view->itemsize != 1) {
            PyErr_SetString(PyExc_ValueError, "Only single-byte integral types are supported");
            return 0;
        }
        // Let's make sure the data is contiguous.
        // This can be a bit trickier for high-dimensional arrays, but CPython has a built-in function for that.
        // The flag 'C' stands for C-style-contiguous, which means that the last dimension is contiguous.
        // The flag 'F' stands for Fortran-style-contiguous, which means that the first dimension is contiguous.
        // The flag 'A' stands for any-contiguous, which only means there are no gaps between elements.
        // For byte-level processing that's all we need.
        if (!PyBuffer_IsContiguous(view, 'A')) {
            PyErr_SetString(PyExc_ValueError, "The array must be contiguous");
            return 0;
        }

        *data = (char *)view->buf;
        *byte_count = view->len;
        return 1;
    }
    else {
        PyErr_SetString(PyExc_TypeError, "Unsupported argument type");
        return 0;
    }
}

int utf8_is_ascii(const unsigned char * start, const unsigned char * end) {
    if (end - start >= SIZEOF_SIZE_T) {
        while (!_Py_IS_ALIGNED(start, ALIGNOF_SIZE_T)) {
            if (0x80 & (*(start++))) {
                return 0;
            }
        }
        while (start + SIZEOF_SIZE_T <= end) {
            size_t v = *(size_t*)start;
            if (v & ASCII_CHAR_MASK) {
                return 0;
            }
            start += SIZEOF_SIZE_T;
        }
    }
    while (start < end) {
        if (0x80 & (*(start++))) {
            return 0;
        }
    }
    return 1;
}

void _PyUTF8Str_Setup_IsASCII(PyObject * self) {
    assert(PyUTF8Str_Check(self));
    unsigned char * data = (unsigned char *)PyUTF8Str_DATA(self);
    Py_ssize_t len = PyUTF8Str_BYTE_COUNT(self);
    _PyUTF8StrObject_CAST(self)->ascii = utf8_is_ascii(data, data + len);
}

int utf8_validate(const unsigned char * s, const unsigned char * end) {
    while (s < end) {
        unsigned char ch1 = *(s++);
        // 0b0xxxxxxx ASCII
        if ((~ch1 >> 7) & 1) continue;
        // 0b10xxxxxx Continuation byte
        if ((~ch1 >> 6) & 1) {
            // Leading byte can't be a continuation byte
            return -1;
        }
        // 0b110xxxxx 2-Byte
        if ((~ch1 >> 5) & 1) {
            if (s + 1 > end) {
                // Too short: ch1 must be followed with a continuation byte
                return -2;
            }
            unsigned char ch2 = *(s++);
            if ((~ch2 >> 7) & (ch2 >> 6) & 1) {
                // Too short: ch1 must be followed with a continuation byte
                return -2;
            }

            if (ch1 < 0b11000010) {
                // Overlong: decoded 2-Byte character must be above U+7F
                return -3;
            }
            continue;
        }

        // 0b1110xxxx 3-Byte
        if ((~ch1 >> 4) & 1) {
            if (s + 2 > end) {
                // Too short: ch1 must be followed with two continuation bytes
                return -2;
            }
            unsigned char ch2 = *(s++);
            unsigned char ch3 = *(s++);
            if (((~ch2 >> 7) & (ch2 >> 6) & 1) | ((~ch3 >> 7) & (ch3 >> 6) & 1)) {
                // Too short: ch1 must be followed with two continuation bytes
                return -2;
            }

            if (ch2 < 0b10100000) {
                // Overlong: decoded 3-Byte character must be above U+7FF
                return -3;
            }
            
            if ((ch1 == 0b11101101) && ((ch2 >> 7) & 1)) {
                // Surrogate: The decoded character must be not be in U+D800...DFFF
                return -4;
            }
            continue;
        }

        // 0b11110xxx 4-Byte
        if ((~ch1 >> 3) & 1) {
            if (s + 3 > end) {
                // Too short: ch1 must be followed with three continuation bytes
                return -2;
            }
            unsigned char ch2 = *(s++);
            unsigned char ch3 = *(s++);
            unsigned char ch4 = *(s++);
            if (((~ch2 >> 7) & (ch2 >> 6) & 1) | ((~ch3 >> 7) & (ch3 >> 6) & 1) | ((~ch4 >> 7) & (ch4 >> 6) & 1)) {
                // Too short: ch1 must be followed with three continuation bytes
                return -2;
            }

            if (ch2 < 0b10010000) {
                // Overlong: decoded 4-Byte character must be above U+FFFF
                return -3;
            }

            if (ch1 > 0b11110100 || (ch1 == 0b11110100 && ch2 > 0b10010000)) {
                // Too Large: The decoded character must be less than or equal to U+10FFFF
                return -5;
            }
            continue;
        }

        // Impossible leading byte
        return -6;
    }

    return 0;
}

int _PyUTF8Str_Validate(PyObject * self) {
    assert(PyUTF8Str_Check(self));
    unsigned char * data = (unsigned char *)PyUTF8Str_DATA(self);
    Py_ssize_t len = PyUTF8Str_BYTE_COUNT(self);
    int err = utf8_validate(data, data + len);
    _PyUTF8StrObject_CAST(self)->valid_utf8 = (err == 0);
    return err;
}

Py_ssize_t utf8_char_len(unsigned char ch) {
    // 0b0xxxxxxx
    if ((~ch >> 7) & 1) return 1;
    // 0b10xxxxxx
    if ((~ch >> 6) & 1) return -1;
    // 0b110xxxxx
    if ((~ch >> 5) & 1) return 2;
    // 0b1110xxxx
    if ((~ch >> 4) & 1) return 3;
    // 0b11110xxx
    if ((~ch >> 3) & 1) return 4;
    return -1;
}

// Forward declaration
Py_ssize_t PyUTF8Str_Length(PyObject *self);

int utf8_make_index(PyObject * self) {
    if (_PyUTF8Str_Validate(self) < 0) {
        PyErr_SetString(PyExc_ValueError, "String is malformed");
        return -1;
    }
    Py_ssize_t len = PyUTF8Str_Length(self);
    Py_ssize_t blocks = len / INDEX_BLOCK_SIZE + 1;
    PyUTF8Index *index = (PyUTF8Index *)PyMem_Malloc(sizeof(PyUTF8Index) + blocks * sizeof(index_entry));
    if (index == NULL) {
        PyErr_NoMemory();
        return -1;
    }
    PyUTF8Str_SET_INDEX(self, index);
    index->entries = (index_entry *)(index + 1);
    index_entry *entry = index->entries;
    entry->base_offset = 0;
    entry->additional_offset[0] = 0;
    int i = 0;

    Py_ssize_t byte_count = PyUTF8Str_BYTE_COUNT(self);
    unsigned char *s = (unsigned char *)PyUTF8Str_DATA(self);
    unsigned char *end = s + byte_count;
    while(s < end) {
        Py_ssize_t ch_len = utf8_char_len(*s);
        // string must be valid
        assert(ch_len != -1);

        if (i < INDEX_BLOCK_SIZE - 1) {
            entry->additional_offset[i + 1] = entry->additional_offset[i] + ch_len;
            i++;
        } else {
            index_entry *next_entry = entry + 1;
            next_entry->base_offset = entry->additional_offset[i] + ch_len;
            next_entry->additional_offset[0] = 0;
            i = 0;
        }

        s += ch_len;
    }
    return 0;
}

Py_ssize_t utf8_index2byte(PyObject *self, Py_ssize_t index) {
    if (PyUTF8Str_IS_ASCII(self)) {
        return index;
    }
    if (PyUTF8Str_INDEX(self) == NULL) {
        if (utf8_make_index(self) < 0) {
            return -1;
        }
    }
    PyUTF8Index *utf8index = PyUTF8Str_INDEX(self);
    index_entry *entry = utf8index->entries + (index / INDEX_BLOCK_SIZE);
    return entry->base_offset + entry->additional_offset[index % INDEX_BLOCK_SIZE]; 
}

// Paste utf8_count_codepoints from unicodeobejct.c
static inline int
scalar_utf8_start_char(unsigned int ch)
{
    // 0xxxxxxx or 11xxxxxx are first byte.
    return (~ch >> 7 | ch >> 6) & 1;
}

static inline size_t
vector_utf8_start_chars(size_t v)
{
    return ((~v >> 7) | (v >> 6)) & VECTOR_0101;
}


// Count the number of UTF-8 code points in a given byte sequence.
static Py_ssize_t
utf8_count_codepoints(const unsigned char *s, const unsigned char *end)
{
    Py_ssize_t len = 0;

    if (end - s >= SIZEOF_SIZE_T) {
        while (!_Py_IS_ALIGNED(s, ALIGNOF_SIZE_T)) {
            len += scalar_utf8_start_char(*s++);
        }

        while (s + SIZEOF_SIZE_T <= end) {
            const unsigned char *e = end;
            if (e - s > SIZEOF_SIZE_T * 255) {
                e = s + SIZEOF_SIZE_T * 255;
            }
            Py_ssize_t vstart = 0;
            while (s + SIZEOF_SIZE_T <= e) {
                size_t v = *(size_t*)s;
                size_t vs = vector_utf8_start_chars(v);
                vstart += vs;
                s += SIZEOF_SIZE_T;
            }
            vstart = (vstart & VECTOR_00FF) + ((vstart >> 8) & VECTOR_00FF);
            vstart += vstart >> 16;
#if SIZEOF_SIZE_T == 8
            vstart += vstart >> 32;
#endif
            len += vstart & 0x7ff;
        }
    }
    while (s < end) {
        len += scalar_utf8_start_char(*s++);
    }
    return len;
}

// Knuth–Morris–Pratt algorithm
void prefix_function(const unsigned char *s, Py_ssize_t *p, Py_ssize_t len) {
    p[0] = 0;
    for (int i = 1; i < len; i++) {
        Py_ssize_t k = p[i - 1];
        while (k > 0 && s[i] != s[k]) {
            k = p[k - 1];
        }
        if (s[i] == s[k]) {
            k++;
        }
        p[i] = k;
    }
}

// Template must be valid (0xff is used as a separator)
// Or think about how to separate these strings in another way
Py_ssize_t knuth_morris_pratt(const unsigned char *text, Py_ssize_t text_len, 
                        const unsigned char *template, Py_ssize_t template_len) {
    Py_ssize_t len = text_len + template_len + 1;
    unsigned char *s = PyMem_Malloc(len + 1);
    memcpy(s, template, template_len);
    s[template_len] = 0xff;
    memcpy(s + template_len + 1, text, text_len);
    s[len] = 0;

    Py_ssize_t *pfunc = PyMem_Calloc(len, SIZEOF_SIZE_T);
    prefix_function(s, pfunc, len);
    Py_ssize_t result = -1;
    for (int i = template_len; i < len; i++) {
        if (pfunc[i] == template_len) {
            result = i - 2 * template_len; // i - (n + 1) - n + 1
            break;
        }
    }
    PyMem_Free((void *)s);
    PyMem_Free((void *)pfunc);
    return result;
}

Py_ssize_t byteindex2codepoint(unsigned char *s, Py_ssize_t len, Py_ssize_t index) {
    // TODO: If index != NULL, binary search
    assert(index <= len);
    return utf8_count_codepoints(s, s + index);
}

static Py_ssize_t
find_kmp(PyObject* str, PyObject* substr, Py_ssize_t start, Py_ssize_t end) {
    Py_ssize_t len = PyUTF8Str_Length(str);
    ADJUST_INDICES(start, end, len);
    if (end - start < 0)
        return -1;

    Py_ssize_t start_byte = 0;
    Py_ssize_t end_byte = PyUTF8Str_BYTE_COUNT(str);
    if (start != 0 || end != len) {
        start_byte = utf8_index2byte(str, start);
        end_byte = utf8_index2byte(str, end);
    }
    Py_ssize_t substr_byte_count = PyUTF8Str_BYTE_COUNT(substr);
    if (end_byte - start_byte < substr_byte_count) {
        return -1;
    }

    unsigned char *data = (unsigned char *)PyUTF8Str_DATA(str);
    Py_ssize_t byte_count = PyUTF8Str_BYTE_COUNT(str);
    Py_ssize_t kmp_result = knuth_morris_pratt(data + start_byte, end_byte - start_byte, 
                            (unsigned char *)PyUTF8Str_DATA(substr), substr_byte_count);
    if (kmp_result == -1) 
        return -1;
    return byteindex2codepoint(data, byte_count, start_byte + kmp_result);
}


PyObject * PyUTF8Str_New(Py_ssize_t size)
{
    /* Optimization for empty strings */
    // if (size == 0) {
    //     return unicode_get_empty();
    // }

    PyObject *obj;
    PyUTF8StrObject *utf8;
    Py_ssize_t struct_size;

    struct_size = sizeof(PyUTF8StrObject);
    

    /* Ensure we won't overflow the size. */
    if (size < 0) {
        PyErr_SetString(PyExc_SystemError,
                        "Negative size passed to PyUnicode_New");
        return NULL;
    }
    if (size > (PY_SSIZE_T_MAX) - struct_size) {
        return PyErr_NoMemory();
    }

    /* Duplicated allocation code from _PyObject_New() instead of a call to
     * PyObject_New() so we are able to allocate space for the object and
     * it's data buffer.
     */
    obj = (PyObject *) PyObject_Malloc(struct_size + (size + 1));
    if (obj == NULL) {
        return PyErr_NoMemory();
    }
    _PyObject_Init(obj, &PyUTF8Str_Type);

    utf8 = (PyUTF8StrObject *)obj;
    utf8->data = (char *)(utf8 + 1);
    utf8->data[size] = 0;
    utf8->byte_count = size;
    utf8->hash = -1;
    utf8->length = 0;
    utf8->valid_utf8 = 0;
    utf8->index = NULL;
    // utf8->interned = 0;

    return obj;
}

static PyObject *
PyUTF8Str_FromData(unsigned char * s, Py_ssize_t byte_count) {
    PyObject *self = PyUTF8Str_New(byte_count);
    if (!self)
        return NULL;
    memcpy(PyUTF8Str_DATA(self), s, byte_count);
    _PyUTF8Str_Setup_IsASCII(self);
    _PyUTF8Str_Validate(self);
    // DEBUG:
    // int err = _PyUTF8Str_Validate(self);
    // if (!PyUTF8Str_VALID(self)) {
    //     PyErr_Format(PyExc_ValueError, "Failed to validate UTF-8 string. Err: %d", err);
    //     return NULL;
    // }
    return self;
}

static PyObject *
utf8str_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    // TODO: change, may be _PyArg_Parser
    Py_ssize_t nargs = PyTuple_Size(args);
    if (nargs > 1) {
        PyErr_SetString(PyExc_TypeError, "Invalid number of arguments");
        return NULL;
    }
    PyObject *s = nargs >= 1 ? PyTuple_GET_ITEM(args, 0) : NULL;

    const char *data;
    Py_ssize_t byte_count;
    if (s == NULL) {
        data = NULL;
        byte_count = 0;
    } else if (!export_string_like(s, &data, &byte_count)) {
        return NULL;
    }

    return PyUTF8Str_FromData((unsigned char *)data, byte_count);
}

static void
utf8str_dealloc(PyUTF8StrObject *self)
{
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
utf8str_str(PyObject *self)
{
    return PyUnicode_FromString(((PyUTF8StrObject *)self)->data);
}

// debug version
static PyObject *
utf8str_repr(PyObject *self)
{
    Py_ssize_t len = PyUTF8Str_BYTE_COUNT(self);
    PyObject * repr = PyUTF8Str_New(len + 8);
    char * data = PyUTF8Str_DATA(repr);
    memcpy(data, "_str('", 6);
    memcpy(data + 6, PyUTF8Str_DATA(self), len);
    memcpy(data + len + 6, "')", 2);

    _PyUTF8Str_Setup_IsASCII(repr);

    return PyUnicode_FromString(data);
}

PyObject *
PyUTF8Str_RichCompare(PyObject *left, PyObject *right, int op)
{
    if (!PyUTF8Str_Check(left) || !PyUTF8Str_Check(right))
        Py_RETURN_NOTIMPLEMENTED;

    if (left == right) {
        switch (op) {
        case Py_EQ:
        case Py_LE:
        case Py_GE:
            Py_RETURN_TRUE;
        case Py_NE:
        case Py_LT:
        case Py_GT:
            Py_RETURN_FALSE;
        default:
            PyErr_BadArgument();
            return NULL;
        }
    }

    Py_ssize_t left_len = PyUTF8Str_BYTE_COUNT(left);
    Py_ssize_t right_len = PyUTF8Str_BYTE_COUNT(right);
    Py_ssize_t min_len = Py_MIN(left_len, right_len);

    if ((op == Py_EQ || op == Py_NE) && left_len != right_len) {
        return PyBool_FromLong(op == Py_NE);
    }

    int result = memcmp(PyUTF8Str_DATA(left), PyUTF8Str_DATA(right), min_len + 1);
    Py_RETURN_RICHCOMPARE(result, 0, op);
}

static Py_hash_t
utf8str_hash(PyObject *self)
{
    Py_uhash_t x;  /* Unsigned for defined overflow behavior. */

#ifdef Py_DEBUG
    assert(_Py_HashSecret_Initialized);
#endif
    Py_hash_t hash = PyUTF8Str_HASH(self);
    if (hash != -1) {
        return hash;
    }
    x = Py_HashBuffer(PyUTF8Str_DATA(self), PyUTF8Str_BYTE_COUNT(self));

    PyUTF8Str_SET_HASH(self, x);
    return x;
}

PyDoc_STRVAR(utf8str_isascii__doc__,
"isascii($self, /)\n"
"--\n"
"\n"
"Return True if all characters in the string are ASCII, False otherwise.\n"
"\n"
"ASCII characters have code points in the range U+0000-U+007F.\n"
"Empty string is ASCII too.");

static PyObject *
utf8str_isascii(PyObject *self) {
    return PyBool_FromLong(PyUTF8Str_IS_ASCII(self));
}

PyDoc_STRVAR(unicode_find__doc__,
"find($self, sub[, start[, end]], /)\n"
"--\n"
"\n"
"Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].\n"
"\n"
"Optional arguments start and end are interpreted as in slice notation.\n"
"Return -1 on failure.");

static PyObject *
utf8str_find(PyObject *str, PyObject *const *args, Py_ssize_t nargs)
{
    PyObject *return_value = NULL;
    PyObject *substr;
    Py_ssize_t start = 0;
    Py_ssize_t end = PY_SSIZE_T_MAX;
    Py_ssize_t _return_value;

    if (!_PyArg_CheckPositional("find", nargs, 1, 3)) {
        goto exit;
    }
    if (!PyUTF8Str_Check(args[0])) {
        _PyArg_BadArgument("find", "argument 1", "str", args[0]);
        goto exit;
    }
    substr = args[0];
    if (nargs < 2) {
        goto skip_optional;
    }
    if (!_PyEval_SliceIndex(args[1], &start)) {
        goto exit;
    }
    if (nargs < 3) {
        goto skip_optional;
    }
    if (!_PyEval_SliceIndex(args[2], &end)) {
        goto exit;
    }
skip_optional:
    _return_value = find_kmp(str, substr, start, end);
    if ((_return_value == -1) && PyErr_Occurred()) {
        goto exit;
    }
    return_value = PyLong_FromSsize_t(_return_value);

exit:
    return return_value;
}

PyObject *
PyUTF8Str_Concat(PyObject *left, PyObject *right)
{
    Py_ssize_t left_len, right_len, new_len;

    if (!PyUTF8Str_Check(left)) {
        PyErr_Format(PyExc_TypeError,
                     "must be _str not \"%.200s\"",
                     Py_TYPE(right)->tp_name);
        return NULL;
    }

    if (!PyUTF8Str_Check(right)) {
        PyErr_Format(PyExc_TypeError,
                     "can only concatenate _str (not \"%.200s\") to _str",
                     Py_TYPE(right)->tp_name);
        return NULL;
    }

    // TODO ? shortcuts: left == empty or right == empty

    left_len = PyUTF8Str_BYTE_COUNT(left);
    right_len = PyUTF8Str_BYTE_COUNT(right);
    if (left_len > PY_SSIZE_T_MAX - right_len) {
        PyErr_SetString(PyExc_OverflowError,
                        "strings are too large to concat");
        return NULL;
    }
    new_len = left_len + right_len;

    PyObject *result = PyUTF8Str_New(new_len);
    if (!result)
        return NULL;
    memcpy(PyUTF8Str_DATA(result), PyUTF8Str_DATA(left), left_len);
    memcpy(PyUTF8Str_DATA(result) + left_len, PyUTF8Str_DATA(right), right_len);
    _PyUTF8Str_Setup_IsASCII(result);

    return (PyObject *)result;
}

static PyObject*
PyUTF8Str_Repeat(PyObject *str, Py_ssize_t n)
{
    PyObject *result;
    Py_ssize_t len, new_len;

    if (n < 1)
        return PyUTF8Str_New(0);

    /* no repeat, return original string */
    if (n == 1)
        return Py_NewRef(str);

    len = PyUTF8Str_BYTE_COUNT(str);

    if (len > PY_SSIZE_T_MAX / n) {
        PyErr_SetString(PyExc_OverflowError,
                        "repeated string is too long");
        return NULL;
    }
    new_len = len * n;

    result = PyUTF8Str_New(new_len);
    if (!result)
        return NULL;
    _PyBytes_Repeat(PyUTF8Str_DATA(result), new_len, PyUTF8Str_DATA(str), len);
    _PyUTF8Str_Setup_IsASCII(result);

    return result;
}

Py_ssize_t PyUTF8Str_Length(PyObject *self)
{
    Py_ssize_t len = PyUTF8Str_LENGTH(self);
    if (len != 0 || PyUTF8Str_BYTE_COUNT(self) == 0) {
        return len;
    }
    unsigned char * data = (unsigned char *)PyUTF8Str_DATA(self);
    Py_ssize_t x = utf8_count_codepoints(data, data + PyUTF8Str_BYTE_COUNT(self));

    PyUTF8Str_SET_LENGTH(self, x);
    return x;
}

static PyObject *
PyUTF8Str_GetItem(PyObject *self, Py_ssize_t index)
{
    if (!PyUTF8Str_Check(self)) {
        PyErr_BadArgument();
        return NULL;
    }
    if (index < 0 || index >= PyUTF8Str_Length(self)) {
        PyErr_SetString(PyExc_IndexError, "string index out of range");
        return NULL;
    }

    Py_ssize_t byte_index = utf8_index2byte(self, index);
    if (byte_index < 0) {
        return NULL;
    }

    unsigned char * ch = (unsigned char *)PyUTF8Str_DATA(self) + byte_index;
    Py_ssize_t ch_len = utf8_char_len(*ch);
    
    return PyUTF8Str_FromData(ch, ch_len);
}

static PyMethodDef utf8str_methods[] = {
    {"find", _PyCFunction_CAST(utf8str_find), METH_FASTCALL, unicode_find__doc__},
    {"isascii", _PyCFunction_CAST(utf8str_isascii), METH_NOARGS, utf8str_isascii__doc__},
    {NULL, NULL}
};

static PySequenceMethods utf8str_as_sequence = {
    .sq_concat = PyUTF8Str_Concat,
    .sq_repeat = PyUTF8Str_Repeat,
    .sq_length = PyUTF8Str_Length,
    .sq_item = PyUTF8Str_GetItem,
};

PyTypeObject PyUTF8Str_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name = "_str",
    .tp_basicsize = sizeof(PyUTF8StrObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)utf8str_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = utf8str_new,
    .tp_str = utf8str_str,
    .tp_repr = utf8str_repr,
    .tp_richcompare = PyUTF8Str_RichCompare,
    .tp_hash = utf8str_hash,
    .tp_as_sequence = &utf8str_as_sequence,
    .tp_methods = utf8str_methods,
};
