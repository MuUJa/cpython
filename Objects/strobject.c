#include "Python.h"
#include "strobject.h"
#include "pycore_object.h"
#include "pycore_bytesobject.h"   // _PyBytes_Repeat()


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
        *byte_count = PyUTF8Str_GET_BYTE_COUNT(object);
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
    Py_ssize_t len = PyUTF8Str_GET_BYTE_COUNT(self);
    _PyUTF8StrObject_CAST(self)->ascii = utf8_is_ascii(data, data + len);
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
    // result->length = -1;
    // result->interned = 0;
    // result->valid_utf8 = 1;

    return obj;
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

    PyObject *self = PyUTF8Str_New(byte_count);
    if (!self)
        return NULL;
    memcpy(PyUTF8Str_DATA(self), data, byte_count);
    _PyUTF8Str_Setup_IsASCII(self);

    return self;
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
    Py_ssize_t len = PyUTF8Str_GET_BYTE_COUNT(self);
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

    Py_ssize_t left_len = PyUTF8Str_GET_BYTE_COUNT(left);
    Py_ssize_t right_len = PyUTF8Str_GET_BYTE_COUNT(right);
    Py_ssize_t min_len = Py_MIN(left_len, right_len);

    if ((op == Py_EQ || op == Py_NE) && left_len != right_len) {
        return PyBool_FromLong(op == Py_NE);
    }

    int result = memcmp(PyUTF8Str_DATA(left), PyUTF8Str_DATA(right), min_len + 1);
    Py_RETURN_RICHCOMPARE(result, 0, op);
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

    left_len = PyUTF8Str_GET_BYTE_COUNT(left);
    right_len = PyUTF8Str_GET_BYTE_COUNT(right);
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

    len = PyUTF8Str_GET_BYTE_COUNT(str);

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

static PyMethodDef utf8str_methods[] = {
    {"isascii", _PyCFunction_CAST(utf8str_isascii), METH_NOARGS, utf8str_isascii__doc__},
    {NULL, NULL}
};

static PySequenceMethods utf8str_as_sequence = {
    .sq_concat = PyUTF8Str_Concat,
    .sq_repeat = PyUTF8Str_Repeat,
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
    .tp_as_sequence = &utf8str_as_sequence,
    .tp_methods = utf8str_methods,
};
