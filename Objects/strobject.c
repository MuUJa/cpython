#include "Python.h"
#include "strobject.h"
#include "pycore_object.h"


// StringZilla like
int export_string_like(PyObject *object, const char **data, Py_ssize_t *length) {
    if (PyUnicode_Check(object)) {
        // Handle Python `str` object
        *data = PyUnicode_AsUTF8AndSize(object, length);
        if (*data == NULL) {
            return 0;
        }
        return 1;
    }
    else if (PyBytes_Check(object)) {
        // Handle Python `bytes` object
        // https://docs.python.org/3/c-api/bytes.html
        if (PyBytes_AsStringAndSize(object, (char **)data, length) == -1) {
            PyErr_SetString(PyExc_ValueError, "Couldn't access `bytes` buffer internals");
            return 0;
        }
        return 1;
    }
    else if (PyByteArray_Check(object)) {
        // Handle Python mutable `bytearray` object
        // https://docs.python.org/3/c-api/bytearray.html
        *data = PyByteArray_AS_STRING(object);
        *length = PyByteArray_GET_SIZE(object);
        return 1;
    }
    else if (PyObject_TypeCheck(object, &PyUTF8Str_Type)) {
        *data = PyUTF8Str_GET_DATA(object);
        *length = PyUTF8Str_GET_LENGTH(object);
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
        *length = view->len;
        return 1;
    }
    else {
        PyErr_SetString(PyExc_TypeError, "Unsupported argument type");
        return 0;
    }
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
    Py_ssize_t length;
    if (s == NULL) {
        data = NULL;
        length = 0;
    } else if (!export_string_like(s, &data, &length)) {
        return NULL;
    }

    Py_ssize_t struct_size = sizeof(PyUTF8StrObject);
    PyUTF8StrObject *self = PyObject_Malloc(struct_size + length + 1);
    _PyObject_Init((PyObject *)self, &PyUTF8Str_Type);
    if (self == NULL) {
        return PyErr_NoMemory();
    }

    self->length = length;
    self->data = (char *)(self + 1);
    memcpy(self->data, data, length);
    self->data[length] = 0;
    return (PyObject *)self;
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

    Py_ssize_t left_len = PyUTF8Str_GET_LENGTH(left);
    Py_ssize_t right_len = PyUTF8Str_GET_LENGTH(right);

    if ((op == Py_EQ || op == Py_NE) && left_len != right_len) {
        return PyBool_FromLong(op == Py_NE);
    }

    char *left_data = PyUTF8Str_GET_DATA(left);
    char *right_data = PyUTF8Str_GET_DATA(right);

    int result = strcmp(left_data, right_data);
    Py_RETURN_RICHCOMPARE(result, 0, op);
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

    left_len = PyUTF8Str_GET_LENGTH(left);
    right_len = PyUTF8Str_GET_LENGTH(right);
    if (left_len > PY_SSIZE_T_MAX - right_len) {
        PyErr_SetString(PyExc_OverflowError,
                        "strings are too large to concat");
        return NULL;
    }
    new_len = left_len + right_len;

    Py_ssize_t struct_size = sizeof(PyUTF8StrObject);
    PyUTF8StrObject *result = PyObject_Malloc(struct_size + new_len + 1);
    _PyObject_Init((PyObject *)result, &PyUTF8Str_Type);
    if (result == NULL) {
        return PyErr_NoMemory();
    }

    result->length = new_len;
    result->data = (char *)(result + 1);
    
    char *left_data = PyUTF8Str_GET_DATA(left);
    char *right_data = PyUTF8Str_GET_DATA(right);
    memcpy(result->data, left_data, left_len);
    memcpy(result->data + left_len, right_data, right_len);
    result->data[new_len] = 0;

    return (PyObject *)result;
}

static PySequenceMethods utf8str_as_sequence = {
    .sq_concat = PyUTF8Str_Concat,
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
    .tp_richcompare = PyUTF8Str_RichCompare,
    .tp_as_sequence = &utf8str_as_sequence,
};
