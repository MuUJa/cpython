#ifndef Py_STROBJECT_H
#define Py_STROBJECT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "object.h"

#define WORD_SIZE (sizeof(uintptr_t) * 8)


typedef struct {
    PyObject_HEAD
    uintptr_t interned: 2;
    uintptr_t ascii: 1;
    uintptr_t valid_utf8: 1;
    uintptr_t length: (WORD_SIZE-4);    /* Number of code points in the string */
    uintptr_t byte_count;      /* Number of bytes in the string */
    Py_hash_t hash;             /* Hash value; -1 if not set */
    // PyUnicodeIndex *index;    /* NULL unless needed */
    char *data;
} PyUTF8StrObject;

extern PyTypeObject PyUTF8Str_Type;

#define PyUTF8Str_Check(op) PyObject_TypeCheck(op, &PyUTF8Str_Type)

#define _PyUTF8StrObject_CAST(op) \
    (assert(PyUTF8Str_Check(op)), \
      _Py_CAST(PyUTF8StrObject*, (op)))

static inline Py_ssize_t PyUTF8Str_GET_LENGTH(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->length;
}
#define PyUTF8Str_GET_LENGTH(op) PyUTF8Str_GET_LENGTH(_PyObject_CAST(op))

static inline Py_ssize_t PyUTF8Str_GET_BYTE_COUNT(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->byte_count;
}
#define PyUTF8Str_GET_BYTE_COUNT(op) PyUTF8Str_GET_BYTE_COUNT(_PyObject_CAST(op))

static inline char* PyUTF8Str_DATA(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->data;
}
#define PyUTF8Str_DATA(op) PyUTF8Str_DATA(_PyObject_CAST(op))

static inline int PyUTF8Str_IS_ASCII(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->ascii;
}
#define PyUTF8Str_IS_ASCII(op) PyUTF8Str_IS_ASCII(_PyObject_CAST(op))

#ifdef __cplusplus
}
#endif
#endif /* !Py_STROBJECT_H */
