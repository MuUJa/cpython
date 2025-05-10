#ifndef Py_STROBJECT_H
#define Py_STROBJECT_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"


#define WORD_SIZE (sizeof(uintptr_t) * 8)


typedef struct {
  PyObject_HEAD
  uintptr_t interned: 2;
  uintptr_t ascii: 1;
  uintptr_t valid_utf8: 1;
  uintptr_t length: (WORD_SIZE-4);    /* Number of code points in the string */
  uintptr_t byte_count;      /* Number of bytes in the string */
  Py_hash_t hash;             /* Hash value; -1 if not set */
//   PyUnicodeIndex *index;    /* NULL unless needed */
  char *data;
} PyUTF8StrObject;

extern PyTypeObject PyUTF8Str_Type;

#define PyUTF8Str_Check(op) PyObject_TypeCheck(op, &PyUTF8Str_Type)

#ifdef __cplusplus
}
#endif
#endif /* !Py_STROBJECT_H */
