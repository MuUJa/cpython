#ifndef Py_STROBJECT_H
#define Py_STROBJECT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "object.h"

#define WORD_SIZE (sizeof(uintptr_t) * 8)

// This works because the UTF-8 encoding of a code point is at most 4 bytes,
// so the largest value one can need to store in additional_offsets is at most 63 * 4,
// which fits in a uint8_t. Effectively it's a lightweight compression scheme
// on having just an array of all the offsets.
#define INDEX_BLOCK_SIZE 64

typedef struct {
    uintptr_t base_offset;
    uint8_t additional_offset[INDEX_BLOCK_SIZE];
} index_entry;

typedef struct {
    index_entry *entries;
} PyUTF8Index;

typedef struct {
    PyObject_HEAD
    uintptr_t interned: 2;
    uintptr_t ascii: 1;
    uintptr_t valid_utf8: 1;
    uintptr_t length: (WORD_SIZE-4);    /* Number of code points in the string */
    uintptr_t byte_count;      /* Number of bytes in the string */
    Py_hash_t hash;             /* Hash value; -1 if not set */
    PyUTF8Index *index;    /* NULL unless needed */
    char *data;
} PyUTF8StrObject;

extern PyTypeObject PyUTF8Str_Type;

#define PyUTF8Str_Check(op) PyObject_TypeCheck(op, &PyUTF8Str_Type)
#define PyUTF8Str_CheckExact(op) Py_IS_TYPE((op), &PyUTF8Str_Type)

#define _PyUTF8StrObject_CAST(op) \
    (assert(PyUTF8Str_Check(op)), \
      _Py_CAST(PyUTF8StrObject*, (op)))

static inline Py_ssize_t PyUTF8Str_LENGTH(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->length;
}
#define PyUTF8Str_LENGTH(op) PyUTF8Str_LENGTH(_PyObject_CAST(op))

static inline void PyUTF8Str_SET_LENGTH(PyObject *op, Py_ssize_t x) {
    _PyUTF8StrObject_CAST(op)->length = x;
}
#define PyUTF8Str_SET_LENGTH(op, x) PyUTF8Str_SET_LENGTH(_PyObject_CAST(op), x)

static inline Py_ssize_t PyUTF8Str_BYTE_COUNT(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->byte_count;
}
#define PyUTF8Str_BYTE_COUNT(op) PyUTF8Str_BYTE_COUNT(_PyObject_CAST(op))

static inline Py_hash_t PyUTF8Str_HASH(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->hash;
}
#define PyUTF8Str_HASH(op) PyUTF8Str_HASH(_PyObject_CAST(op))

static inline void PyUTF8Str_SET_HASH(PyObject *op, Py_hash_t x) {
    _PyUTF8StrObject_CAST(op)->hash = x;
}
#define PyUTF8Str_SET_HASH(op, x) PyUTF8Str_SET_HASH(_PyObject_CAST(op), x)

static inline char* PyUTF8Str_DATA(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->data;
}
#define PyUTF8Str_DATA(op) PyUTF8Str_DATA(_PyObject_CAST(op))

static inline int PyUTF8Str_IS_ASCII(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->ascii;
}
#define PyUTF8Str_IS_ASCII(op) PyUTF8Str_IS_ASCII(_PyObject_CAST(op))

static inline int PyUTF8Str_VALID(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->valid_utf8;
}
#define PyUTF8Str_VALID(op) PyUTF8Str_VALID(_PyObject_CAST(op))

static inline PyUTF8Index *PyUTF8Str_INDEX(PyObject *op) {
    return _PyUTF8StrObject_CAST(op)->index;
}
#define PyUTF8Str_INDEX(op) PyUTF8Str_INDEX(_PyObject_CAST(op))

static inline void PyUTF8Str_SET_INDEX(PyObject *op, PyUTF8Index *x) {
    _PyUTF8StrObject_CAST(op)->index = x;
}
#define PyUTF8Str_SET_INDEX(op, x) PyUTF8Str_SET_INDEX(_PyObject_CAST(op), x)

#ifdef __cplusplus
}
#endif
#endif /* !Py_STROBJECT_H */
