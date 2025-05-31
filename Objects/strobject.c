#include "Python.h"

#include "pycore_abstract.h"      // _PyIndex_Check()
#include "pycore_bytesobject.h"   // _PyBytes_Repeat()
#include "pycore_critical_section.h" // Py_*_CRITICAL_SECTION_SEQUENCE_FAST
#include "pycore_modsupport.h"    // _PyArg_CheckPositional()
#include "pycore_object.h"

#include "strobject.h"


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

// Forward declarations
Py_ssize_t PyUTF8Str_Length(PyObject *self);
PyObject * PyUTF8Str_FromData(unsigned char * s, Py_ssize_t byte_count);
PyObject * _PyUTF8Str_Empty(void);
PyObject * PyUTF8Str_New(Py_ssize_t size);

int utf8_make_index(PyObject * self) {
    if (_PyUTF8Str_Validate(self) < 0) {
        PyErr_SetString(PyExc_ValueError, "String is malformed");
        return -1;
    }
    Py_ssize_t len = PyUTF8Str_Length(self);
    Py_ssize_t blocks = len / INDEX_BLOCK_SIZE + 1;
    PyUTF8Index *index = (PyUTF8Index *)PyMem_Malloc(sizeof(PyUTF8Index) +
                                                blocks * sizeof(index_entry));
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

#define FIND_MODE 0
#define RFIND_MODE 1
#define COUNT_MODE 2
#define GET_ALL_MODE 3
/* Template must be valid (0xff is used as a separator)
   Or think about how to separate these strings in another way */
/* mode 0-2: return find result. find_indexes is unused
   mode 3: return len of the find. find_indexes is result, must be free after */
Py_ssize_t _knuth_morris_pratt(const unsigned char *text, Py_ssize_t text_len,
                        const unsigned char *template, Py_ssize_t template_len,
                        int mode, Py_ssize_t **find_indexes) {
    assert(0 <= mode && mode <= 3);

    Py_ssize_t len = text_len + template_len + 1;
    unsigned char *s = PyMem_Malloc(len + 1);
    if (s == NULL) {
        PyErr_NoMemory();
        return -1;
    }
    memcpy(s, template, template_len);
    s[template_len] = 0xff;
    memcpy(s + template_len + 1, text, text_len);
    s[len] = 0;

    Py_ssize_t *pfunc = PyMem_Calloc(len, SIZEOF_SIZE_T);
    if (pfunc == NULL) {
        PyErr_NoMemory();
        PyMem_Free((void *)s);
        return -1;
    }
    prefix_function(s, pfunc, len);


    Py_ssize_t result = -1;
    if (mode == 0) {
        for (int i = template_len; i < len; i++) {
            if (pfunc[i] == template_len) {
                result = i - 2 * template_len; // i - (n + 1) - n + 1
                break;
            }
        }
    } else if (mode == 1) {
        for (int i = len - 1; i >= template_len; i--) {
            if (pfunc[i] == template_len) {
                result = i - 2 * template_len; // i - (n + 1) - n + 1
                break;
            }
        }
    } else if (mode == 2 || mode == 3) {
        result = 0;
        for (int i = template_len; i < len; i++) {
            if (pfunc[i] == template_len) {
                result++;
                i += Py_MAX(1, template_len) - 1;
            }
        }
    }

    if (mode == 3) {
        assert(find_indexes != NULL);
        *find_indexes = PyMem_Calloc(result, SIZEOF_SIZE_T);
        if (*find_indexes == NULL) {
            PyErr_NoMemory();
            PyMem_Free(s);
            PyMem_Free(pfunc);
            return -1;
        }

        int j = 0;
        for (int i = template_len; i < len; i++) {
            if (pfunc[i] == template_len) {
                i += Py_MAX(1, template_len) - 1;
                *find_indexes[j++] = i - 2 * template_len; // i - (n + 1) - n + 1
            }
        }
    }

    PyMem_Free((void *)s);
    PyMem_Free((void *)pfunc);
    return result;
}

Py_ssize_t byteindex2codepoint(unsigned char *s, Py_ssize_t len, Py_ssize_t index) {
    // TODO: If index != NULL (index from PyUTF8StrObject), binary search
    assert(index <= len);
    return utf8_count_codepoints(s, s + index);
}

static Py_ssize_t
knuth_morris_pratt(PyObject* str, PyObject* substr,
                   Py_ssize_t start, Py_ssize_t end,
                   int mode, Py_ssize_t **find_indexes) {
    assert(0 <= mode && mode <= 3);

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
    Py_ssize_t kmp_result = _knuth_morris_pratt(data + start_byte, end_byte - start_byte,
                            (unsigned char *)PyUTF8Str_DATA(substr), substr_byte_count,
                            mode, find_indexes);
    if (kmp_result == -1)
        return -1;
    if (mode == FIND_MODE || mode == RFIND_MODE) {
        return byteindex2codepoint(data, byte_count, start_byte + kmp_result);
    } else if (mode == COUNT_MODE) {
        return kmp_result;
    } else if (mode == GET_ALL_MODE) {
        for (Py_ssize_t i = 0; i < kmp_result; i++) {
            Py_ssize_t byte_index = *find_indexes[i];
            Py_ssize_t index = utf8_count_codepoints(data, data + byte_index);
            *find_indexes[i] = index;
            if (i != 0) {
                *find_indexes[i] += *find_indexes[i - 1];
            }
            data += index;
        }
    }

    Py_UNREACHABLE();
    return -1;
}

PyObject *
_PyUTF8Str_JoinArray(PyObject *separator, PyObject *const *items, Py_ssize_t seqlen)
{
    PyObject *res = NULL;
    PyObject *sep = NULL;
    Py_ssize_t seplen; // byte len

    if (seqlen == 0) {
        return _PyUTF8Str_Empty();
    }

    /* Set up sep and seplen */
    // I think it is for CAPI, usually separator can't be NULL
    if (separator == NULL) {
        /* fall back to a blank space separator */
        // Not sure here.
        sep = PyUTF8Str_FromData((unsigned char *)" ", 1);
        if (sep == NULL)
            goto onError;
        seplen = 1;
    } else {
        if (!PyUTF8Str_Check(separator)) {
            PyErr_Format(PyExc_TypeError,
                        "separator: expected str instance,"
                        " %.80s found", Py_TYPE(separator)->tp_name);
            goto onError;
        }
        sep = separator;
        seplen = PyUTF8Str_BYTE_COUNT(separator);
        /* inc refcount to keep this code path symmetric with the
            above case of a blank separator */
        Py_INCREF(sep);
    }

    Py_ssize_t sz = 0;
    for (Py_ssize_t i = 0; i < seqlen; i++) {
        PyObject * item = items[i];
        if (!PyUTF8Str_Check(item)) {
            PyErr_Format(PyExc_TypeError,
                         "sequence item %zd: expected str instance,"
                         " %.80s found", i, Py_TYPE(item)->tp_name);
            goto onError;
        }

        size_t add_sz = PyUTF8Str_BYTE_COUNT(item);
        if (i != 0) {
            add_sz += seplen;
        }
        if (add_sz > (size_t)(PY_SSIZE_T_MAX - sz)) {
            PyErr_SetString(PyExc_OverflowError,
                            "join() result is too long for a Python string");
            goto onError;
        }
        sz += add_sz;
    }

    res = PyUTF8Str_New(sz);
    if (res == NULL) {
        goto onError;
    }

    uint8_t *res_data = (uint8_t *)PyUTF8Str_DATA(res);
    uint8_t *sep_data = (uint8_t *)PyUTF8Str_DATA(sep);

    for (Py_ssize_t i = 0; i < seqlen; i++) {
        PyObject * item = items[i];

        if (i != 0 && seplen != 0) {
            memcpy(res_data, sep_data, seplen);
            res_data += seplen;
        }

        Py_ssize_t item_len = PyUTF8Str_BYTE_COUNT(item);
        if (item_len != 0) {
            memcpy(res_data, PyUTF8Str_DATA(item), item_len);
            res_data += item_len;
        }
    }
    assert(res_data == (uint8_t *)PyUTF8Str_DATA(res) + PyUTF8Str_BYTE_COUNT(res));
    Py_XDECREF(sep);
    return res;

onError:
    Py_XDECREF(sep);
    Py_XDECREF(res);
    return NULL;
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

PyObject * PyUTF8Str_FromData(unsigned char * s, Py_ssize_t byte_count) {
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

PyObject * _PyUTF8Str_Empty() {
    return PyUTF8Str_FromData((unsigned char *)"", 0);
}

PyObject *_PyUTF8Str_Copy(PyObject * str) {
    if (!PyUTF8Str_Check(str)) {
        PyErr_BadInternalCall();
        return NULL;
    }

    return PyUTF8Str_FromData((unsigned char *)PyUTF8Str_DATA(str),
                              PyUTF8Str_BYTE_COUNT(str));
}

PyObject* utf8_result_unchanged(PyObject *str)
{
    if (PyUTF8Str_CheckExact(str)) {
        return Py_NewRef(str);
    }
    else
        /* Subtype -- return genuine unicode string with the same value. */
        return _PyUTF8Str_Copy(str);
}

PyObject*
PyUTF8Str_Substring(PyObject *self, Py_ssize_t start, Py_ssize_t end)
{
    Py_ssize_t length = PyUTF8Str_Length(self);
    end = Py_MIN(end, length);

    if (start == 0 && end == length)
        return utf8_result_unchanged(self);

    if (start < 0 || end < 0) {
        PyErr_SetString(PyExc_IndexError, "string index out of range");
        return NULL;
    }

    if (start >= length || end < start)
        return _PyUTF8Str_Empty();

    Py_ssize_t start_byte = 0;
    Py_ssize_t end_byte = PyUTF8Str_BYTE_COUNT(self);
    if (start != 0 || end != length) {
        start_byte = utf8_index2byte(self, start);
        end_byte = utf8_index2byte(self, end);
    }
    unsigned char * data = (unsigned char *)PyUTF8Str_DATA(self);
    return PyUTF8Str_FromData(data + start_byte, end_byte - start_byte);
}

static PyObject *
utf8str_subtype_new(PyTypeObject *type, PyObject *str)
{
    assert(PyType_IsSubtype(type, &PyUTF8Str_Type));
    PyObject *self = type->tp_alloc(type, 0);
    Py_ssize_t byte_count = PyUTF8Str_BYTE_COUNT(str);
    char * data = PyMem_Malloc(byte_count);
    if (data == NULL) {
        PyErr_NoMemory();
        Py_DECREF(self);
        return NULL;
    }
    memcpy(data, PyUTF8Str_DATA(str), byte_count + 1);

    _PyUTF8StrObject_CAST(self)->data = data;
    _PyUTF8StrObject_CAST(self)->byte_count = byte_count;
    _PyUTF8StrObject_CAST(self)->ascii = _PyUTF8StrObject_CAST(str)->ascii;
    _PyUTF8StrObject_CAST(self)->valid_utf8 =
        _PyUTF8StrObject_CAST(str)->valid_utf8;

    return self;
}

static PyObject *
utf8str_new_impl(PyTypeObject *type, PyObject *x)
{
    PyObject *str;
    if (x == NULL) {
        str = _PyUTF8Str_Empty();
    } else {
        // TODO: like original. Where PyObject_Str calls __str__ methods
        // unicode = PyObject_Str(x);
        const char *data;
        Py_ssize_t byte_count;
        if (!export_string_like(x, &data, &byte_count)) {
            return NULL;
        }
        str = PyUTF8Str_FromData((unsigned char *)data, byte_count);
    }

    if (str != NULL && type != &PyUTF8Str_Type) {
        Py_SETREF(str, utf8str_subtype_new(type, str));
    }
    return str;
}

static PyObject *
utf8str_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    // TODO: change, may be _PyArg_Parser or _PyArg_UnpackKeywords.
    // Add encoding and errors args if understand how to use them
    Py_ssize_t nargs = PyTuple_Size(args);
    if (nargs > 1) {
        PyErr_SetString(PyExc_TypeError, "Invalid number of arguments");
        return NULL;
    }
    PyObject *s = nargs >= 1 ? PyTuple_GET_ITEM(args, 0) : NULL;

    return utf8str_new_impl(type, s);
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

PyDoc_STRVAR(utf8str_find__doc__,
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
    _return_value = knuth_morris_pratt(str, substr, start, end, FIND_MODE, NULL);
    if ((_return_value == -1) && PyErr_Occurred()) {
        goto exit;
    }
    return_value = PyLong_FromSsize_t(_return_value);

exit:
    return return_value;
}

PyDoc_STRVAR(utf8str_rfind__doc__,
"rfind($self, sub[, start[, end]], /)\n"
"--\n"
"\n"
"Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].\n"
"\n"
"Optional arguments start and end are interpreted as in slice notation.\n"
"Return -1 on failure.");

static PyObject *
utf8str_rfind(PyObject *str, PyObject *const *args, Py_ssize_t nargs)
{
    PyObject *return_value = NULL;
    PyObject *substr;
    Py_ssize_t start = 0;
    Py_ssize_t end = PY_SSIZE_T_MAX;
    Py_ssize_t _return_value;

    if (!_PyArg_CheckPositional("rfind", nargs, 1, 3)) {
        goto exit;
    }
    if (!PyUTF8Str_Check(args[0])) {
        _PyArg_BadArgument("rfind", "argument 1", "str", args[0]);
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
    _return_value = knuth_morris_pratt(str, substr, start, end, RFIND_MODE, NULL);
    if ((_return_value == -1) && PyErr_Occurred()) {
        goto exit;
    }
    return_value = PyLong_FromSsize_t(_return_value);

exit:
    return return_value;
}

PyDoc_STRVAR(utf8str_count__doc__,
"count($self, sub[, start[, end]], /)\n"
"--\n"
"\n"
"Return the number of non-overlapping occurrences of substring sub in string S[start:end].\n"
"\n"
"Optional arguments start and end are interpreted as in slice notation.");

static PyObject *
utf8str_count(PyObject *str, PyObject *const *args, Py_ssize_t nargs)
{
    PyObject *return_value = NULL;
    PyObject *substr;
    Py_ssize_t start = 0;
    Py_ssize_t end = PY_SSIZE_T_MAX;
    Py_ssize_t _return_value;

    if (!_PyArg_CheckPositional("count", nargs, 1, 3)) {
        goto exit;
    }
    if (!PyUTF8Str_Check(args[0])) {
        _PyArg_BadArgument("count", "argument 1", "str", args[0]);
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
    _return_value = knuth_morris_pratt(str, substr, start, end, COUNT_MODE, NULL);
    if ((_return_value == -1) && PyErr_Occurred()) {
        goto exit;
    }
    return_value = PyLong_FromSsize_t(_return_value);

exit:
    return return_value;
}

PyDoc_STRVAR(utf8str_index__doc__,
"index($self, sub[, start[, end]], /)\n"
"--\n"
"\n"
"Return the lowest index in S where substring sub is found, such that sub is contained within S[start:end].\n"
"\n"
"Optional arguments start and end are interpreted as in slice notation.\n"
"Raises ValueError when the substring is not found.");

static PyObject *
utf8str_index(PyObject *str, PyObject *const *args, Py_ssize_t nargs)
{
    PyObject *return_value = NULL;
    PyObject *substr;
    Py_ssize_t start = 0;
    Py_ssize_t end = PY_SSIZE_T_MAX;
    Py_ssize_t _return_value;

    if (!_PyArg_CheckPositional("index", nargs, 1, 3)) {
        goto exit;
    }
    if (!PyUTF8Str_Check(args[0])) {
        _PyArg_BadArgument("index", "argument 1", "str", args[0]);
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
    _return_value = knuth_morris_pratt(str, substr, start, end, FIND_MODE, NULL);
    if ((_return_value == -1) && PyErr_Occurred()) {
        goto exit;
    }
    if (_return_value == -1) {
        PyErr_SetString(PyExc_ValueError, "substring not found");
        goto exit;
    }
    return_value = PyLong_FromSsize_t(_return_value);

exit:
    return return_value;
}

PyDoc_STRVAR(utf8str_rindex__doc__,
"rindex($self, sub[, start[, end]], /)\n"
"--\n"
"\n"
"Return the highest index in S where substring sub is found, such that sub is contained within S[start:end].\n"
"\n"
"Optional arguments start and end are interpreted as in slice notation.\n"
"Raises ValueError when the substring is not found.");

static PyObject *
utf8str_rindex(PyObject *str, PyObject *const *args, Py_ssize_t nargs)
{
    PyObject *return_value = NULL;
    PyObject *substr;
    Py_ssize_t start = 0;
    Py_ssize_t end = PY_SSIZE_T_MAX;
    Py_ssize_t _return_value;

    if (!_PyArg_CheckPositional("rindex", nargs, 1, 3)) {
        goto exit;
    }
    if (!PyUTF8Str_Check(args[0])) {
        _PyArg_BadArgument("rindex", "argument 1", "str", args[0]);
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
    _return_value = knuth_morris_pratt(str, substr, start, end, RFIND_MODE, NULL);
    if ((_return_value == -1) && PyErr_Occurred()) {
        goto exit;
    }
    if (_return_value == -1) {
        PyErr_SetString(PyExc_ValueError, "substring not found");
        goto exit;
    }
    return_value = PyLong_FromSsize_t(_return_value);

exit:
    return return_value;
}

PyDoc_STRVAR(utf8str_join__doc__,
"join($self, iterable, /)\n"
"--\n"
"\n"
"Concatenate any number of strings.\n"
"\n"
"The string whose method is called is inserted in between each given string.\n"
"The result is returned as a new string.\n"
"\n"
"Example: \'.\'.join([\'ab\', \'pq\', \'rs\']) -> \'ab.pq.rs\'");

PyObject *
PyUTF8Str_Join(PyObject *separator, PyObject *seq)
{
    PyObject *res;
    PyObject *fseq;
    Py_ssize_t seqlen;
    PyObject **items;

    fseq = PySequence_Fast(seq, "can only join an iterable");
    if (fseq == NULL) {
        return NULL;
    }

    // I don't fully understand it yet
    Py_BEGIN_CRITICAL_SECTION_SEQUENCE_FAST(seq);

    items = PySequence_Fast_ITEMS(fseq);
    seqlen = PySequence_Fast_GET_SIZE(fseq);
    res = _PyUTF8Str_JoinArray(separator, items, seqlen);

    Py_END_CRITICAL_SECTION_SEQUENCE_FAST();

    Py_DECREF(fseq);
    return res;
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
        return _PyUTF8Str_Empty();

    /* no repeat, return original string */
    if (n == 1)
        return utf8_result_unchanged(str);

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

static PyObject*
utf8str_subscript(PyObject* self, PyObject* item)
{
    if (_PyIndex_Check(item)) {
        Py_ssize_t i = PyNumber_AsSsize_t(item, PyExc_IndexError);
        if (i == -1 && PyErr_Occurred())
            return NULL;
        if (i < 0)
            i += PyUTF8Str_Length(self);
        return PyUTF8Str_GetItem(self, i);
    } else if (PySlice_Check(item)) {
        Py_ssize_t start, stop, step;
        if (PySlice_Unpack(item, &start, &stop, &step) < 0) {
            return NULL;
        }
        Py_ssize_t len = PyUTF8Str_Length(self);
        Py_ssize_t slicelength = PySlice_AdjustIndices(len, &start, &stop, step);

        if (slicelength <= 0) {
            return _PyUTF8Str_Empty();
        } else if (start == 0 && step == 1 && slicelength == len) {
            return utf8_result_unchanged(self);
        } else if (step == 1) {
            return PyUTF8Str_Substring(self, start, start + slicelength);
        }

        /* General case */
        unsigned char * data = (unsigned char *)PyUTF8Str_DATA(self);
        Py_ssize_t sz = 0;
        for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
            Py_ssize_t byte_index = utf8_index2byte(self, cur);
            sz += utf8_char_len(data[byte_index]);
        }

        PyObject *result = PyUTF8Str_New(sz);
        if (result == NULL)
            return NULL;
        unsigned char * res_data = (unsigned char *)PyUTF8Str_DATA(result);
        for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
            Py_ssize_t byte_index = utf8_index2byte(self, cur);
            Py_ssize_t ch_len = utf8_char_len(data[byte_index]);
            memcpy(res_data, data + byte_index, ch_len);
            res_data += ch_len;
        }

        return result;
    } else {
        PyErr_Format(PyExc_TypeError, "string indices must be integers, not '%.200s'",
                     Py_TYPE(item)->tp_name);
        return NULL;
    }
}

int PyUTF8Str_Contains(PyObject *str, PyObject *substr) {
    if (!PyUTF8Str_Check(substr)) {
        PyErr_Format(PyExc_TypeError,
                     "'in <string>' requires string as left operand, not %.100s",
                     Py_TYPE(substr)->tp_name);
        return -1;
    }

    // TODO: May be make fast search single character (may be only ASCII)

    return knuth_morris_pratt(str, substr, 0, PY_SSIZE_T_MAX, FIND_MODE, NULL) != -1;
}

static PyMethodDef utf8str_methods[] = {
    {"find", _PyCFunction_CAST(utf8str_find), METH_FASTCALL, utf8str_find__doc__},
    {"rfind", _PyCFunction_CAST(utf8str_rfind), METH_FASTCALL, utf8str_rfind__doc__},
    {"count", _PyCFunction_CAST(utf8str_count), METH_FASTCALL, utf8str_count__doc__},
    {"index", _PyCFunction_CAST(utf8str_index), METH_FASTCALL, utf8str_index__doc__},
    {"rindex", _PyCFunction_CAST(utf8str_rindex), METH_FASTCALL, utf8str_rindex__doc__},
    {"isascii", _PyCFunction_CAST(utf8str_isascii), METH_NOARGS, utf8str_isascii__doc__},
    {"join", (PyCFunction)PyUTF8Str_Join, METH_O, utf8str_join__doc__},
    {NULL, NULL}
};

static PySequenceMethods utf8str_as_sequence = {
    .sq_concat = PyUTF8Str_Concat,
    .sq_repeat = PyUTF8Str_Repeat,
    .sq_length = PyUTF8Str_Length,
    .sq_item = PyUTF8Str_GetItem,
    .sq_contains = PyUTF8Str_Contains,
};

static PyMappingMethods utf8str_as_mapping = {
    .mp_length = PyUTF8Str_Length,
    .mp_subscript = utf8str_subscript,
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
    .tp_as_mapping = &utf8str_as_mapping,
    .tp_methods = utf8str_methods,
};
