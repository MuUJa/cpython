#include "Python.h"
#include "strobject.h"

static PyObject *
utf8str_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    const char *s;
    if (!PyArg_ParseTuple(args, "s", &s))
        return NULL;

    PyUTF8StrObject *self;
    self = (PyUTF8StrObject *)type->tp_alloc(type, 0);
    if (!self)
        return NULL;

    self->length = strlen(s);
    self->data = PyMem_Malloc(self->length + 1);
    if (!self->data) {
        Py_DECREF(self);
        return PyErr_NoMemory();
    }
    strcpy(self->data, s);
    self->hash = -1;
    return (PyObject *)self;
}

static void
utf8str_dealloc(PyUTF8StrObject *self)
{
    PyMem_Free(self->data);
    Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *
utf8str_str(PyObject *self)
{
    return PyUnicode_FromString(((PyUTF8StrObject *)self)->data);
}


PyTypeObject PyUTF8Str_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    .tp_name = "_str",
    .tp_basicsize = sizeof(PyUTF8StrObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)utf8str_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = utf8str_new,
    .tp_str = utf8str_str,
};
