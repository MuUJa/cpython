""" Test script for the Unicode implementation.

Written by Marc-Andre Lemburg (mal@lemburg.com).

(c) Copyright CNRI, All Rights Reserved. NO WARRANTY.

"""

import _string
import codecs
import datetime
import itertools
import operator
import pickle
import struct
import sys
import textwrap
import unicodedata
import unittest
import warnings
from test.support import warnings_helper
from test import support
from test import string_tests_my as string_tests
from test.support.script_helper import assert_python_failure
try:
    import _testcapi
except ImportError:
    _testcapi = None

from stringzilla import Str
str_type = Str
# str_type = _str


def search_function(encoding):

    def decode1(input, errors=str_type('strict')):
        return 42

    def encode1(input, errors=str_type('strict')):
        return 42

    def encode2(input, errors=str_type('strict')):
        return 42, 42

    def decode2(input, errors=str_type('strict')):
        return 42, 42
    if encoding == str_type('test.unicode1'):
        return encode1, decode1, None, None
    elif encoding == str_type('test.unicode2'):
        return encode2, decode2, None, None
    else:
        return None


def duplicate_string(text):
    str_type(
        """
    Try to get a fresh clone of the specified text:
    new object with a reference count of 1.

    This is a best-effort: latin1 single letters and the empty
    string ('') are singletons and cannot be cloned.
    """
        )
    return text.encode().decode()


# class StrSubclass(str_type):
#     pass


# class OtherStrSubclass(str_type):
#     pass


class WithStr:

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class WithRepr:

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value


class StrTest(string_tests.StringLikeTest, string_tests.MixinStrUnicodeTest,
    unittest.TestCase):
    type2test = str_type

    def setUp(self):
        codecs.register(search_function)
        self.addCleanup(codecs.unregister, search_function)

    def checkequalnofix(self, result, object, methodname, *args):
        methodname = str(methodname)
        # ^^^ dirty fix _str
        method = getattr(object, methodname)
        realresult = method(*args)
        self.assertEqual(realresult, result)
        self.assertTrue(type(realresult) is type(result))
        if realresult is object:


            class usub(str_type):

                def __repr__(self):
                    return str_type('usub(%r)') % str_type.__repr__(self)
            object = usub(object)
            method = getattr(object, methodname)
            realresult = method(*args)
            self.assertEqual(realresult, result)
            self.assertTrue(object is not realresult)

    def assertTypedEqual(self, actual, expected):
        self.assertIs(type(actual), type(expected))
        self.assertEqual(actual, expected)

    def test_literals(self):
        self.assertEqual(str_type('ÿ'), str_type('ÿ'))
        self.assertEqual(str_type('\uffff'), str_type('\uffff'))
        self.assertRaises(SyntaxError, eval, str_type("'\\Ufffffffe'"))
        self.assertRaises(SyntaxError, eval, str_type("'\\Uffffffff'"))
        self.assertRaises(SyntaxError, eval, str_type("'\\U%08x'") % 1114112)
        self.assertNotEqual(str_type('\\u0020'), str_type(' '))

    def test_ascii(self):
        self.assertEqual(ascii(str_type('abc')), str_type("'abc'"))
        self.assertEqual(ascii(str_type('ab\\c')), str_type("'ab\\\\c'"))
        self.assertEqual(ascii(str_type('ab\\')), str_type("'ab\\\\'"))
        self.assertEqual(ascii(str_type('\\c')), str_type("'\\\\c'"))
        self.assertEqual(ascii(str_type('\\')), str_type("'\\\\'"))
        self.assertEqual(ascii(str_type('\n')), str_type("'\\n'"))
        self.assertEqual(ascii(str_type('\r')), str_type("'\\r'"))
        self.assertEqual(ascii(str_type('\t')), str_type("'\\t'"))
        self.assertEqual(ascii(str_type('\x08')), str_type("'\\x08'"))
        self.assertEqual(ascii(str_type('\'"')), str_type('\'\\\'"\''))
        self.assertEqual(ascii(str_type('\'"')), str_type('\'\\\'"\''))
        self.assertEqual(ascii(str_type("'")), str_type('"\'"'))
        self.assertEqual(ascii(str_type('"')), str_type('\'"\''))
        latin1repr = str_type(
            '\'\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\x7f\\x80\\x81\\x82\\x83\\x84\\x85\\x86\\x87\\x88\\x89\\x8a\\x8b\\x8c\\x8d\\x8e\\x8f\\x90\\x91\\x92\\x93\\x94\\x95\\x96\\x97\\x98\\x99\\x9a\\x9b\\x9c\\x9d\\x9e\\x9f\\xa0\\xa1\\xa2\\xa3\\xa4\\xa5\\xa6\\xa7\\xa8\\xa9\\xaa\\xab\\xac\\xad\\xae\\xaf\\xb0\\xb1\\xb2\\xb3\\xb4\\xb5\\xb6\\xb7\\xb8\\xb9\\xba\\xbb\\xbc\\xbd\\xbe\\xbf\\xc0\\xc1\\xc2\\xc3\\xc4\\xc5\\xc6\\xc7\\xc8\\xc9\\xca\\xcb\\xcc\\xcd\\xce\\xcf\\xd0\\xd1\\xd2\\xd3\\xd4\\xd5\\xd6\\xd7\\xd8\\xd9\\xda\\xdb\\xdc\\xdd\\xde\\xdf\\xe0\\xe1\\xe2\\xe3\\xe4\\xe5\\xe6\\xe7\\xe8\\xe9\\xea\\xeb\\xec\\xed\\xee\\xef\\xf0\\xf1\\xf2\\xf3\\xf4\\xf5\\xf6\\xf7\\xf8\\xf9\\xfa\\xfb\\xfc\\xfd\\xfe\\xff\''
            )
        testrepr = ascii(str_type('').join(map(chr, range(256))))
        self.assertEqual(testrepr, latin1repr)
        self.assertEqual(ascii(str_type('𐀀') * 39 + str_type('\uffff') *
            4096), ascii(str_type('𐀀') * 39 + str_type('\uffff') * 4096))
        self.assertTypedEqual(ascii(str_type('🐍')), str_type("'\\U0001f40d'"))
        # self.assertTypedEqual(ascii(StrSubclass(str_type('abc'))), str_type
        #     ("'abc'"))
        self.assertTypedEqual(ascii(WithRepr(str_type('<abc>'))), str_type(
            '<abc>'))
        # self.assertTypedEqual(ascii(WithRepr(StrSubclass(str_type('<abc>'))
        #     )), StrSubclass(str_type('<abc>')))
        self.assertTypedEqual(ascii(WithRepr(str_type('<🐍>'))), str_type(
            '<\\U0001f40d>'))
        # self.assertTypedEqual(ascii(WithRepr(StrSubclass(str_type('<🐍>')))),
        #     str_type('<\\U0001f40d>'))
        self.assertRaises(TypeError, ascii, WithRepr(b'byte-repr'))

    def test_repr(self):
        self.assertEqual(repr(str_type('abc')), str_type("'abc'"))
        self.assertEqual(repr(str_type('ab\\c')), str_type("'ab\\\\c'"))
        self.assertEqual(repr(str_type('ab\\')), str_type("'ab\\\\'"))
        self.assertEqual(repr(str_type('\\c')), str_type("'\\\\c'"))
        self.assertEqual(repr(str_type('\\')), str_type("'\\\\'"))
        self.assertEqual(repr(str_type('\n')), str_type("'\\n'"))
        self.assertEqual(repr(str_type('\r')), str_type("'\\r'"))
        self.assertEqual(repr(str_type('\t')), str_type("'\\t'"))
        self.assertEqual(repr(str_type('\x08')), str_type("'\\x08'"))
        self.assertEqual(repr(str_type('\'"')), str_type('\'\\\'"\''))
        self.assertEqual(repr(str_type('\'"')), str_type('\'\\\'"\''))
        self.assertEqual(repr(str_type("'")), str_type('"\'"'))
        self.assertEqual(repr(str_type('"')), str_type('\'"\''))
        latin1repr = str_type(
            '\'\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\x7f\\x80\\x81\\x82\\x83\\x84\\x85\\x86\\x87\\x88\\x89\\x8a\\x8b\\x8c\\x8d\\x8e\\x8f\\x90\\x91\\x92\\x93\\x94\\x95\\x96\\x97\\x98\\x99\\x9a\\x9b\\x9c\\x9d\\x9e\\x9f\\xa0¡¢£¤¥¦§¨©ª«¬\\xad®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ\''
            )
        testrepr = repr(str_type('').join(map(chr, range(256))))
        self.assertEqual(testrepr, latin1repr)
        self.assertEqual(repr(str_type('𐀀') * 39 + str_type('\uffff') *
            4096), repr(str_type('𐀀') * 39 + str_type('\uffff') * 4096))
        self.assertTypedEqual(repr(str_type('🐍')), str_type("'🐍'"))
        # self.assertTypedEqual(repr(StrSubclass(str_type('abc'))), str_type(
        #     "'abc'"))
        self.assertTypedEqual(repr(WithRepr(str_type('<abc>'))), str_type(
            '<abc>'))
        # self.assertTypedEqual(repr(WithRepr(StrSubclass(str_type('<abc>')))
        #     ), StrSubclass(str_type('<abc>')))
        self.assertTypedEqual(repr(WithRepr(str_type('<🐍>'))), str_type('<🐍>'))
        # self.assertTypedEqual(repr(WithRepr(StrSubclass(str_type('<🐍>')))),
        #     StrSubclass(str_type('<🐍>')))
        self.assertRaises(TypeError, repr, WithRepr(b'byte-repr'))

    def test_iterators(self):
        it = str_type('ᄑ∢㌳').__iter__()
        self.assertEqual(next(it), str_type('ᄑ'))
        self.assertEqual(next(it), str_type('∢'))
        self.assertEqual(next(it), str_type('㌳'))
        self.assertRaises(StopIteration, next, it)

    def test_iterators_invocation(self):
        cases = [type(iter(str_type('abc'))), type(iter(str_type('🚀')))]
        for cls in cases:
            with self.subTest(cls=cls):
                self.assertRaises(TypeError, cls)

    def test_iteration(self):
        cases = [str_type('abc'), str_type('🚀🚀🚀'), str_type('ᄑ∢㌳')]
        for case in cases:
            with self.subTest(string=case):
                self.assertEqual(case, str_type('').join(iter(case)))

    def test_exhausted_iterator(self):
        cases = [str_type('abc'), str_type('🚀🚀🚀'), str_type('ᄑ∢㌳')]
        for case in cases:
            with self.subTest(case=case):
                iterator = iter(case)
                tuple(iterator)
                self.assertRaises(StopIteration, next, iterator)

    def test_pickle_iterator(self):
        cases = [str_type('abc'), str_type('🚀🚀🚀'), str_type('ᄑ∢㌳')]
        for case in cases:
            with self.subTest(case=case):
                for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                    it = iter(case)
                    with self.subTest(proto=proto):
                        pickled = str_type('').join(pickle.loads(pickle.
                            dumps(it, proto)))
                        self.assertEqual(case, pickled)

    def test_count(self):
        string_tests.StringLikeTest.test_count(self)
        self.checkequalnofix(3, str_type('aaa'), str_type('count'),
            str_type('a'))
        self.checkequalnofix(0, str_type('aaa'), str_type('count'),
            str_type('b'))
        self.checkequalnofix(3, str_type('aaa'), str_type('count'),
            str_type('a'))
        self.checkequalnofix(0, str_type('aaa'), str_type('count'),
            str_type('b'))
        self.checkequalnofix(0, str_type('aaa'), str_type('count'),
            str_type('b'))
        self.checkequalnofix(1, str_type('aaa'), str_type('count'),
            str_type('a'), -1)
        self.checkequalnofix(3, str_type('aaa'), str_type('count'),
            str_type('a'), -10)
        self.checkequalnofix(2, str_type('aaa'), str_type('count'),
            str_type('a'), 0, -1)
        self.checkequalnofix(0, str_type('aaa'), str_type('count'),
            str_type('a'), 0, -10)
        self.checkequal(10, str_type('Ă') + str_type('a') * 10, str_type(
            'count'), str_type('a'))
        self.checkequal(10, str_type('\U00100304') + str_type('a') * 10,
            str_type('count'), str_type('a'))
        self.checkequal(10, str_type('\U00100304') + str_type('Ă') * 10,
            str_type('count'), str_type('Ă'))
        self.checkequal(0, str_type('a') * 10, str_type('count'), str_type('Ă')
            )
        self.checkequal(0, str_type('a') * 10, str_type('count'), str_type(
            '\U00100304'))
        self.checkequal(0, str_type('Ă') * 10, str_type('count'), str_type(
            '\U00100304'))
        self.checkequal(10, str_type('Ă') + str_type('a_') * 10, str_type(
            'count'), str_type('a_'))
        self.checkequal(10, str_type('\U00100304') + str_type('a_') * 10,
            str_type('count'), str_type('a_'))
        self.checkequal(10, str_type('\U00100304') + str_type('Ă_') * 10,
            str_type('count'), str_type('Ă_'))
        self.checkequal(0, str_type('a') * 10, str_type('count'), str_type(
            'aĂ'))
        self.checkequal(0, str_type('a') * 10, str_type('count'), str_type(
            'a\U00100304'))
        self.checkequal(0, str_type('Ă') * 10, str_type('count'), str_type(
            'Ă\U00100304'))


        class MyStr(str_type):
            pass
        self.checkequal(3, MyStr(str_type('aaa')), str_type('count'),
            str_type('a'))

    def test_find(self):
        string_tests.StringLikeTest.test_find(self)
        self.checkequal(100, str_type('a') * 100 + str_type('Ă'), str_type(
            'find'), str_type('Ă'))
        self.checkequal(-1, str_type('a') * 100 + str_type('Ă'), str_type(
            'find'), str_type('ȁ'))
        self.checkequal(-1, str_type('a') * 100 + str_type('Ă'), str_type(
            'find'), str_type('Ġ'))
        self.checkequal(-1, str_type('a') * 100 + str_type('Ă'), str_type(
            'find'), str_type('Ƞ'))
        self.checkequal(100, str_type('a') * 100 + str_type('\U00100304'),
            str_type('find'), str_type('\U00100304'))
        self.checkequal(-1, str_type('a') * 100 + str_type('\U00100304'),
            str_type('find'), str_type('\U00100204'))
        self.checkequal(-1, str_type('a') * 100 + str_type('\U00100304'),
            str_type('find'), str_type('\U00102004'))
        self.checkequalnofix(0, str_type('abcdefghiabc'), str_type('find'),
            str_type('abc'))
        self.checkequalnofix(9, str_type('abcdefghiabc'), str_type('find'),
            str_type('abc'), 1)
        self.checkequalnofix(-1, str_type('abcdefghiabc'), str_type('find'),
            str_type('def'), 4)
        self.checkequal(0, str_type('тест'), str_type('find'), str_type('т'))
        self.checkequal(3, str_type('тест'), str_type('find'), str_type('т'), 1
            )
        self.checkequal(-1, str_type('тест'), str_type('find'), str_type(
            'т'), 1, 3)
        self.checkequal(-1, str_type('тест'), str_type('find'), str_type('e'))
        self.checkequal(1, str_type('тест тест'), str_type('find'),
            str_type('ес'))
        self.checkequal(1, str_type('тест тест'), str_type('find'),
            str_type('ес'), 1)
        self.checkequal(1, str_type('тест тест'), str_type('find'),
            str_type('ес'), 1, 3)
        self.checkequal(6, str_type('тест тест'), str_type('find'),
            str_type('ес'), 2)
        self.checkequal(-1, str_type('тест тест'), str_type('find'),
            str_type('ес'), 6, 7)
        self.checkequal(-1, str_type('тест тест'), str_type('find'),
            str_type('ес'), 7)
        self.checkequal(-1, str_type('тест тест'), str_type('find'),
            str_type('ec'))
        self.assertRaises(TypeError, str_type('hello').find)
        self.assertRaises(TypeError, str_type('hello').find, 42)
        self.checkequal(100, str_type('Ă') * 100 + str_type('a'), str_type(
            'find'), str_type('a'))
        self.checkequal(100, str_type('\U00100304') * 100 + str_type('a'),
            str_type('find'), str_type('a'))
        self.checkequal(100, str_type('\U00100304') * 100 + str_type('Ă'),
            str_type('find'), str_type('Ă'))
        self.checkequal(-1, str_type('a') * 100, str_type('find'), str_type
            ('Ă'))
        self.checkequal(-1, str_type('a') * 100, str_type('find'), str_type
            ('\U00100304'))
        self.checkequal(-1, str_type('Ă') * 100, str_type('find'), str_type
            ('\U00100304'))
        self.checkequal(100, str_type('Ă') * 100 + str_type('a_'), str_type
            ('find'), str_type('a_'))
        self.checkequal(100, str_type('\U00100304') * 100 + str_type('a_'),
            str_type('find'), str_type('a_'))
        self.checkequal(100, str_type('\U00100304') * 100 + str_type('Ă_'),
            str_type('find'), str_type('Ă_'))
        self.checkequal(-1, str_type('a') * 100, str_type('find'), str_type
            ('aĂ'))
        self.checkequal(-1, str_type('a') * 100, str_type('find'), str_type
            ('a\U00100304'))
        self.checkequal(-1, str_type('Ă') * 100, str_type('find'), str_type
            ('Ă\U00100304'))

    def test_rfind(self):
        string_tests.StringLikeTest.test_rfind(self)
        self.checkequal(0, str_type('Ă') + str_type('a') * 100, str_type(
            'rfind'), str_type('Ă'))
        self.checkequal(-1, str_type('Ă') + str_type('a') * 100, str_type(
            'rfind'), str_type('ȁ'))
        self.checkequal(-1, str_type('Ă') + str_type('a') * 100, str_type(
            'rfind'), str_type('Ġ'))
        self.checkequal(-1, str_type('Ă') + str_type('a') * 100, str_type(
            'rfind'), str_type('Ƞ'))
        self.checkequal(0, str_type('\U00100304') + str_type('a') * 100,
            str_type('rfind'), str_type('\U00100304'))
        self.checkequal(-1, str_type('\U00100304') + str_type('a') * 100,
            str_type('rfind'), str_type('\U00100204'))
        self.checkequal(-1, str_type('\U00100304') + str_type('a') * 100,
            str_type('rfind'), str_type('\U00102004'))
        self.checkequalnofix(9, str_type('abcdefghiabc'), str_type('rfind'),
            str_type('abc'))
        self.checkequalnofix(12, str_type('abcdefghiabc'), str_type('rfind'
            ), str_type(''))
        self.checkequalnofix(12, str_type('abcdefghiabc'), str_type('rfind'
            ), str_type(''))
        self.checkequal(1, str_type('тест'), str_type('rfind'), str_type('е'))
        self.checkequal(1, str_type('тест'), str_type('rfind'), str_type(
            'е'), 1)
        self.checkequal(-1, str_type('тест'), str_type('rfind'), str_type(
            'е'), 2)
        self.checkequal(-1, str_type('тест'), str_type('rfind'), str_type('e'))
        self.checkequal(6, str_type('тест тест'), str_type('rfind'),
            str_type('ес'))
        self.checkequal(6, str_type('тест тест'), str_type('rfind'),
            str_type('ес'), 1)
        self.checkequal(1, str_type('тест тест'), str_type('rfind'),
            str_type('ес'), 1, 3)
        self.checkequal(6, str_type('тест тест'), str_type('rfind'),
            str_type('ес'), 2)
        self.checkequal(-1, str_type('тест тест'), str_type('rfind'),
            str_type('ес'), 6, 7)
        self.checkequal(-1, str_type('тест тест'), str_type('rfind'),
            str_type('ес'), 7)
        self.checkequal(-1, str_type('тест тест'), str_type('rfind'),
            str_type('ec'))
        self.checkequal(0, str_type('a') + str_type('Ă') * 100, str_type(
            'rfind'), str_type('a'))
        self.checkequal(0, str_type('a') + str_type('\U00100304') * 100,
            str_type('rfind'), str_type('a'))
        self.checkequal(0, str_type('Ă') + str_type('\U00100304') * 100,
            str_type('rfind'), str_type('Ă'))
        self.checkequal(-1, str_type('a') * 100, str_type('rfind'),
            str_type('Ă'))
        self.checkequal(-1, str_type('a') * 100, str_type('rfind'),
            str_type('\U00100304'))
        self.checkequal(-1, str_type('Ă') * 100, str_type('rfind'),
            str_type('\U00100304'))
        self.checkequal(0, str_type('_a') + str_type('Ă') * 100, str_type(
            'rfind'), str_type('_a'))
        self.checkequal(0, str_type('_a') + str_type('\U00100304') * 100,
            str_type('rfind'), str_type('_a'))
        self.checkequal(0, str_type('_Ă') + str_type('\U00100304') * 100,
            str_type('rfind'), str_type('_Ă'))
        self.checkequal(-1, str_type('a') * 100, str_type('rfind'),
            str_type('Ăa'))
        self.checkequal(-1, str_type('a') * 100, str_type('rfind'),
            str_type('\U00100304a'))
        self.checkequal(-1, str_type('Ă') * 100, str_type('rfind'),
            str_type('\U00100304Ă'))

    def test_index(self):
        string_tests.StringLikeTest.test_index(self)
        self.checkequalnofix(0, str_type('abcdefghiabc'), str_type('index'),
            str_type(''))
        self.checkequalnofix(3, str_type('abcdefghiabc'), str_type('index'),
            str_type('def'))
        self.checkequalnofix(0, str_type('abcdefghiabc'), str_type('index'),
            str_type('abc'))
        self.checkequalnofix(9, str_type('abcdefghiabc'), str_type('index'),
            str_type('abc'), 1)
        self.assertRaises(ValueError, str_type('abcdefghiabc').index,
            str_type('hib'))
        self.assertRaises(ValueError, str_type('abcdefghiab').index,
            str_type('abc'), 1)
        self.assertRaises(ValueError, str_type('abcdefghi').index, str_type
            ('ghi'), 8)
        self.assertRaises(ValueError, str_type('abcdefghi').index, str_type
            ('ghi'), -1)
        self.checkequal(100, str_type('Ă') * 100 + str_type('a'), str_type(
            'index'), str_type('a'))
        self.checkequal(100, str_type('\U00100304') * 100 + str_type('a'),
            str_type('index'), str_type('a'))
        self.checkequal(100, str_type('\U00100304') * 100 + str_type('Ă'),
            str_type('index'), str_type('Ă'))
        self.assertRaises(ValueError, (str_type('a') * 100).index, str_type
            ('Ă'))
        self.assertRaises(ValueError, (str_type('a') * 100).index, str_type
            ('\U00100304'))
        self.assertRaises(ValueError, (str_type('Ă') * 100).index, str_type
            ('\U00100304'))
        self.checkequal(100, str_type('Ă') * 100 + str_type('a_'), str_type
            ('index'), str_type('a_'))
        self.checkequal(100, str_type('\U00100304') * 100 + str_type('a_'),
            str_type('index'), str_type('a_'))
        self.checkequal(100, str_type('\U00100304') * 100 + str_type('Ă_'),
            str_type('index'), str_type('Ă_'))
        self.assertRaises(ValueError, (str_type('a') * 100).index, str_type
            ('aĂ'))
        self.assertRaises(ValueError, (str_type('a') * 100).index, str_type
            ('a\U00100304'))
        self.assertRaises(ValueError, (str_type('Ă') * 100).index, str_type
            ('Ă\U00100304'))

    def test_rindex(self):
        string_tests.StringLikeTest.test_rindex(self)
        self.checkequalnofix(12, str_type('abcdefghiabc'), str_type(
            'rindex'), str_type(''))
        self.checkequalnofix(3, str_type('abcdefghiabc'), str_type('rindex'
            ), str_type('def'))
        self.checkequalnofix(9, str_type('abcdefghiabc'), str_type('rindex'
            ), str_type('abc'))
        self.checkequalnofix(0, str_type('abcdefghiabc'), str_type('rindex'
            ), str_type('abc'), 0, -1)
        self.assertRaises(ValueError, str_type('abcdefghiabc').rindex,
            str_type('hib'))
        self.assertRaises(ValueError, str_type('defghiabc').rindex,
            str_type('def'), 1)
        self.assertRaises(ValueError, str_type('defghiabc').rindex,
            str_type('abc'), 0, -1)
        self.assertRaises(ValueError, str_type('abcdefghi').rindex,
            str_type('ghi'), 0, 8)
        self.assertRaises(ValueError, str_type('abcdefghi').rindex,
            str_type('ghi'), 0, -1)
        self.checkequal(0, str_type('a') + str_type('Ă') * 100, str_type(
            'rindex'), str_type('a'))
        self.checkequal(0, str_type('a') + str_type('\U00100304') * 100,
            str_type('rindex'), str_type('a'))
        self.checkequal(0, str_type('Ă') + str_type('\U00100304') * 100,
            str_type('rindex'), str_type('Ă'))
        self.assertRaises(ValueError, (str_type('a') * 100).rindex,
            str_type('Ă'))
        self.assertRaises(ValueError, (str_type('a') * 100).rindex,
            str_type('\U00100304'))
        self.assertRaises(ValueError, (str_type('Ă') * 100).rindex,
            str_type('\U00100304'))
        self.checkequal(0, str_type('_a') + str_type('Ă') * 100, str_type(
            'rindex'), str_type('_a'))
        self.checkequal(0, str_type('_a') + str_type('\U00100304') * 100,
            str_type('rindex'), str_type('_a'))
        self.checkequal(0, str_type('_Ă') + str_type('\U00100304') * 100,
            str_type('rindex'), str_type('_Ă'))
        self.assertRaises(ValueError, (str_type('a') * 100).rindex,
            str_type('Ăa'))
        self.assertRaises(ValueError, (str_type('a') * 100).rindex,
            str_type('\U00100304a'))
        self.assertRaises(ValueError, (str_type('Ă') * 100).rindex,
            str_type('\U00100304Ă'))

    def test_maketrans_translate(self):
        self.checkequalnofix(str_type('bbbc'), str_type('abababc'),
            str_type('translate'), {ord(str_type('a')): None})
        self.checkequalnofix(str_type('iiic'), str_type('abababc'),
            str_type('translate'), {ord(str_type('a')): None, ord(str_type(
            'b')): ord(str_type('i'))})
        self.checkequalnofix(str_type('iiix'), str_type('abababc'),
            str_type('translate'), {ord(str_type('a')): None, ord(str_type(
            'b')): ord(str_type('i')), ord(str_type('c')): str_type('x')})
        self.checkequalnofix(str_type('c'), str_type('abababc'), str_type(
            'translate'), {ord(str_type('a')): None, ord(str_type('b')):
            str_type('')})
        self.checkequalnofix(str_type('xyyx'), str_type('xzx'), str_type(
            'translate'), {ord(str_type('z')): str_type('yy')})
        self.checkequalnofix(str_type('abababc'), str_type('abababc'),
            str_type('translate'), {str_type('b'): str_type('<i>')})
        tbl = self.type2test.maketrans({str_type('a'): None, str_type('b'):
            str_type('<i>')})
        self.checkequalnofix(str_type('<i><i><i>c'), str_type('abababc'),
            str_type('translate'), tbl)
        tbl = self.type2test.maketrans(str_type('abc'), str_type('xyz'),
            str_type('d'))
        self.checkequalnofix(str_type('xyzzy'), str_type('abdcdcbdddd'),
            str_type('translate'), tbl)
        self.assertEqual(str_type('[a]').translate(str_type.maketrans(str_type(
            'a'), str_type('X'))), str_type('[X]'))
        self.assertEqual(str_type('[a]').translate(str_type.maketrans({str_type(
            'a'): str_type('X')})), str_type('[X]'))
        self.assertEqual(str_type('[a]').translate(str_type.maketrans({str_type(
            'a'): None})), str_type('[]'))
        self.assertEqual(str_type('[a]').translate(str_type.maketrans({str_type(
            'a'): str_type('XXX')})), str_type('[XXX]'))
        self.assertEqual(str_type('[a]').translate(str_type.maketrans({str_type(
            'a'): str_type('é')})), str_type('[é]'))
        self.assertEqual(str_type('axb').translate(str_type.maketrans({str_type(
            'a'): None, str_type('b'): str_type('123')})), str_type('x123'))
        self.assertEqual(str_type('axb').translate(str_type.maketrans({str_type(
            'a'): None, str_type('b'): str_type('é')})), str_type('xé'))
        self.assertEqual(str_type('[a]').translate(str_type.maketrans({str_type(
            'a'): str_type('<é>')})), str_type('[<é>]'))
        self.assertEqual(str_type('[é]').translate(str_type.maketrans({str_type(
            'é'): str_type('a')})), str_type('[a]'))
        self.assertEqual(str_type('[é]').translate(str_type.maketrans({str_type(
            'é'): None})), str_type('[]'))
        self.assertEqual(str_type('[é]').translate(str_type.maketrans({str_type(
            'é'): str_type('123')})), str_type('[123]'))
        self.assertEqual(str_type('[aé]').translate(str_type.maketrans({str_type
            ('a'): str_type('<€>')})), str_type('[<€>é]'))
        invalid_char = 1114111 + 1
        for before in str_type('aé€\U0010ffff'):
            mapping = str_type.maketrans({before: invalid_char})
            text = str_type('[%s]') % before
            self.assertRaises(ValueError, text.translate, mapping)
        self.assertRaises(TypeError, self.type2test.maketrans)
        self.assertRaises(ValueError, self.type2test.maketrans, str_type(
            'abc'), str_type('defg'))
        self.assertRaises(TypeError, self.type2test.maketrans, 2, str_type(
            'def'))
        self.assertRaises(TypeError, self.type2test.maketrans, str_type(
            'abc'), 2)
        self.assertRaises(TypeError, self.type2test.maketrans, str_type(
            'abc'), str_type('def'), 2)
        self.assertRaises(ValueError, self.type2test.maketrans, {str_type(
            'xy'): 2})
        self.assertRaises(TypeError, self.type2test.maketrans, {(1,): 2})
        self.assertRaises(TypeError, str_type('hello').translate)
        self.assertRaises(TypeError, str_type('abababc').translate,
            str_type('abc'), str_type('xyz'))

    def test_split(self):
        string_tests.StringLikeTest.test_split(self)
        for left, right in (str_type('ba'), str_type('āĀ'), str_type('𐌁𐌀')):
            left *= 9
            right *= 9
            for delim in (str_type('c'), str_type('Ă'), str_type('𐌂')):
                self.checkequal([left + right], left + right, str_type(
                    'split'), delim)
                self.checkequal([left, right], left + delim + right,
                    str_type('split'), delim)
                self.checkequal([left + right], left + right, str_type(
                    'split'), delim * 2)
                self.checkequal([left, right], left + delim * 2 + right,
                    str_type('split'), delim * 2)

    def test_rsplit(self):
        string_tests.StringLikeTest.test_rsplit(self)
        for left, right in (str_type('ba'), str_type('юё'), str_type('āĀ'),
            str_type('𐌁𐌀')):
            left *= 9
            right *= 9
            for delim in (str_type('c'), str_type('ы'), str_type('Ă'),
                str_type('𐌂')):
                self.checkequal([left + right], left + right, str_type(
                    'rsplit'), delim)
                self.checkequal([left, right], left + delim + right,
                    str_type('rsplit'), delim)
                self.checkequal([left + right], left + right, str_type(
                    'rsplit'), delim * 2)
                self.checkequal([left, right], left + delim * 2 + right,
                    str_type('rsplit'), delim * 2)
            self.checkequal([left + right], left + right, str_type('rsplit'
                ), None)

    def test_partition(self):
        string_tests.StringLikeTest.test_partition(self)
        self.checkequal((str_type('ABCDEFGH'), str_type(''), str_type('')),
            str_type('ABCDEFGH'), str_type('partition'), str_type('䈀'))
        for left, right in (str_type('ba'), str_type('āĀ'), str_type('𐌁𐌀')):
            left *= 9
            right *= 9
            for delim in (str_type('c'), str_type('Ă'), str_type('𐌂')):
                self.checkequal((left + right, str_type(''), str_type('')),
                    left + right, str_type('partition'), delim)
                self.checkequal((left, delim, right), left + delim + right,
                    str_type('partition'), delim)
                self.checkequal((left + right, str_type(''), str_type('')),
                    left + right, str_type('partition'), delim * 2)
                self.checkequal((left, delim * 2, right), left + delim * 2 +
                    right, str_type('partition'), delim * 2)

    def test_rpartition(self):
        string_tests.StringLikeTest.test_rpartition(self)
        self.checkequal((str_type(''), str_type(''), str_type('ABCDEFGH')),
            str_type('ABCDEFGH'), str_type('rpartition'), str_type('䈀'))
        for left, right in (str_type('ba'), str_type('āĀ'), str_type('𐌁𐌀')):
            left *= 9
            right *= 9
            for delim in (str_type('c'), str_type('Ă'), str_type('𐌂')):
                self.checkequal((str_type(''), str_type(''), left + right),
                    left + right, str_type('rpartition'), delim)
                self.checkequal((left, delim, right), left + delim + right,
                    str_type('rpartition'), delim)
                self.checkequal((str_type(''), str_type(''), left + right),
                    left + right, str_type('rpartition'), delim * 2)
                self.checkequal((left, delim * 2, right), left + delim * 2 +
                    right, str_type('rpartition'), delim * 2)

    def test_join(self):
        string_tests.StringLikeTest.test_join(self)


        class MyWrapper:

            def __init__(self, sval):
                self.sval = sval

            def __str__(self):
                return self.sval
        self.checkequalnofix(str_type('a b c d'), str_type(' '), str_type(
            'join'), [str_type('a'), str_type('b'), str_type('c'), str_type
            ('d')])
        self.checkequalnofix(str_type('abcd'), str_type(''), str_type(
            'join'), (str_type('a'), str_type('b'), str_type('c'), str_type
            ('d')))
        self.checkequalnofix(str_type('w x y z'), str_type(' '), str_type(
            'join'), string_tests.Sequence(str_type('wxyz')))
        self.checkequalnofix(str_type('a b c d'), str_type(' '), str_type(
            'join'), [str_type('a'), str_type('b'), str_type('c'), str_type
            ('d')])
        self.checkequalnofix(str_type('a b c d'), str_type(' '), str_type(
            'join'), [str_type('a'), str_type('b'), str_type('c'), str_type
            ('d')])
        self.checkequalnofix(str_type('abcd'), str_type(''), str_type(
            'join'), (str_type('a'), str_type('b'), str_type('c'), str_type
            ('d')))
        self.checkequalnofix(str_type('w x y z'), str_type(' '), str_type(
            'join'), string_tests.Sequence(str_type('wxyz')))
        self.checkraises(TypeError, str_type(' '), str_type('join'), [
            str_type('1'), str_type('2'), MyWrapper(str_type('foo'))])
        self.checkraises(TypeError, str_type(' '), str_type('join'), [
            str_type('1'), str_type('2'), str_type('3'), bytes()])
        self.checkraises(TypeError, str_type(' '), str_type('join'), [1, 2, 3])
        self.checkraises(TypeError, str_type(' '), str_type('join'), [
            str_type('1'), str_type('2'), 3])

    @unittest.skipIf(sys.maxsize > 2 ** 32, str_type(
        'needs too much memory on a 64-bit platform'))
    def test_join_overflow(self):
        size = int(sys.maxsize ** 0.5) + 1
        seq = (str_type('A') * size,) * size
        self.assertRaises(OverflowError, str_type('').join, seq)

    def test_replace(self):
        string_tests.StringLikeTest.test_replace(self)
        self.checkequalnofix(str_type('one@two!three!'), str_type(
            'one!two!three!'), str_type('replace'), str_type('!'), str_type
            ('@'), 1)
        self.assertRaises(TypeError, str_type('replace').replace, str_type(
            'r'), 42)
        for left, right in (str_type('ba'), str_type('āĀ'), str_type('𐌁𐌀')):
            left *= 9
            right *= 9
            for delim in (str_type('c'), str_type('Ă'), str_type('𐌂')):
                for repl in (str_type('d'), str_type('ă'), str_type('𐌃')):
                    self.checkequal(left + right, left + right, str_type(
                        'replace'), delim, repl)
                    self.checkequal(left + repl + right, left + delim +
                        right, str_type('replace'), delim, repl)
                    self.checkequal(left + right, left + right, str_type(
                        'replace'), delim * 2, repl)
                    self.checkequal(left + repl + right, left + delim * 2 +
                        right, str_type('replace'), delim * 2, repl)

    @support.cpython_only
    def test_replace_id(self):
        pattern = str_type('abc')
        text = str_type('abc def')
        self.assertIs(text.replace(pattern, pattern), text)

    def test_repeat_id_preserving(self):
        a = str_type('123abc1@')
        b = str_type('456zyx-+')
        self.assertEqual(id(a), id(a))
        self.assertNotEqual(id(a), id(b))
        self.assertNotEqual(id(a), id(a * -4))
        self.assertNotEqual(id(a), id(a * 0))
        self.assertEqual(id(a), id(a * 1))
        self.assertEqual(id(a), id(1 * a))
        self.assertNotEqual(id(a), id(a * 2))


        class SubStr(str_type):
            pass
        s = SubStr(str_type('qwerty()'))
        self.assertEqual(id(s), id(s))
        self.assertNotEqual(id(s), id(s * -4))
        self.assertNotEqual(id(s), id(s * 0))
        self.assertNotEqual(id(s), id(s * 1))
        self.assertNotEqual(id(s), id(1 * s))
        self.assertNotEqual(id(s), id(s * 2))

    def test_bytes_comparison(self):
        with warnings_helper.check_warnings():
            warnings.simplefilter(str_type('ignore'), BytesWarning)
            self.assertEqual(str_type('abc') == b'abc', False)
            self.assertEqual(str_type('abc') != b'abc', True)
            self.assertEqual(str_type('abc') == bytearray(b'abc'), False)
            self.assertEqual(str_type('abc') != bytearray(b'abc'), True)

    def test_comparison(self):
        self.assertEqual(str_type('abc'), str_type('abc'))
        self.assertTrue(str_type('abcd') > str_type('abc'))
        self.assertTrue(str_type('abc') < str_type('abcd'))
        if 0:
            self.assertTrue(str_type('a') < str_type('€'))
            self.assertTrue(str_type('a') < str_type('\ud800\udc02'))

            def test_lecmp(s, s2):
                self.assertTrue(s < s2)

            def test_fixup(s):
                s2 = str_type('\ud800\udc01')
                test_lecmp(s, s2)
                s2 = str_type('\ud900\udc01')
                test_lecmp(s, s2)
                s2 = str_type('\uda00\udc01')
                test_lecmp(s, s2)
                s2 = str_type('\udb00\udc01')
                test_lecmp(s, s2)
                s2 = str_type('\ud800\udd01')
                test_lecmp(s, s2)
                s2 = str_type('\ud900\udd01')
                test_lecmp(s, s2)
                s2 = str_type('\uda00\udd01')
                test_lecmp(s, s2)
                s2 = str_type('\udb00\udd01')
                test_lecmp(s, s2)
                s2 = str_type('\ud800\ude01')
                test_lecmp(s, s2)
                s2 = str_type('\ud900\ude01')
                test_lecmp(s, s2)
                s2 = str_type('\uda00\ude01')
                test_lecmp(s, s2)
                s2 = str_type('\udb00\ude01')
                test_lecmp(s, s2)
                s2 = str_type('\ud800\udfff')
                test_lecmp(s, s2)
                s2 = str_type('\ud900\udfff')
                test_lecmp(s, s2)
                s2 = str_type('\uda00\udfff')
                test_lecmp(s, s2)
                s2 = str_type('\udb00\udfff')
                test_lecmp(s, s2)
                test_fixup(str_type('\ue000'))
                test_fixup(str_type('｡'))
        # TODO: fix surrogates?
        self.assertTrue(str_type('\ud800\udc02'.encode('utf-16', errors='surrogatepass').decode('utf-16')) < str_type('\ud84d\udc56'.encode('utf-16', errors='surrogatepass').decode('utf-16')))

    def test_islower(self):
        super().test_islower()
        self.checkequalnofix(False, str_type('ῼ'), str_type('islower'))
        self.assertFalse(str_type('Ⅷ').islower())
        self.assertTrue(str_type('ⅷ').islower())
        self.assertFalse(str_type('𐐁').islower())
        self.assertFalse(str_type('𐐧').islower())
        self.assertTrue(str_type('𐐩').islower())
        self.assertTrue(str_type('𐑎').islower())
        self.assertFalse(str_type('🐍').islower())
        self.assertFalse(str_type('👯').islower())

    def test_isupper(self):
        super().test_isupper()
        self.checkequalnofix(False, str_type('ῼ'), str_type('isupper'))
        self.assertTrue(str_type('Ⅷ').isupper())
        self.assertFalse(str_type('ⅷ').isupper())
        self.assertTrue(str_type('𐐁').isupper())
        self.assertTrue(str_type('𐐧').isupper())
        self.assertFalse(str_type('𐐩').isupper())
        self.assertFalse(str_type('𐑎').isupper())
        self.assertFalse(str_type('🐍').isupper())
        self.assertFalse(str_type('👯').isupper())

    def test_istitle(self):
        super().test_istitle()
        self.checkequalnofix(True, str_type('ῼ'), str_type('istitle'))
        self.checkequalnofix(True, str_type('Greek ῼitlecases ...'),
            str_type('istitle'))
        self.assertTrue(str_type('𐐁𐐩').istitle())
        self.assertTrue(str_type('𐐧𐑎').istitle())
        for ch in [str_type('𐐩'), str_type('𐑎'), str_type('🐍'), str_type('👯')]:
            self.assertFalse(ch.istitle(), str_type('{!a} is not title').
                format(ch))

    def test_isspace(self):
        super().test_isspace()
        self.checkequalnofix(True, str_type('\u2000'), str_type('isspace'))
        self.checkequalnofix(True, str_type('\u200a'), str_type('isspace'))
        self.checkequalnofix(False, str_type('—'), str_type('isspace'))
        for ch in [str_type('𐐁'), str_type('𐐧'), str_type('𐐩'), str_type(
            '𐑎'), str_type('🐍'), str_type('👯')]:
            self.assertFalse(ch.isspace(), str_type('{!a} is not space.').
                format(ch))

    # @support.requires_resource(str_type('cpu'))
    def test_isspace_invariant(self):
        for codepoint in range(sys.maxunicode + 1):
            char = chr(codepoint)
            bidirectional = unicodedata.bidirectional(char)
            category = unicodedata.category(char)
            self.assertEqual(char.isspace(), bidirectional in (str_type(
                'WS'), str_type('B'), str_type('S')) or category ==
                str_type('Zs'))

    def test_isalnum(self):
        super().test_isalnum()
        for ch in [str_type('𐐁'), str_type('𐐧'), str_type('𐐩'), str_type(
            '𐑎'), str_type('𝟶'), str_type('𑁦'), str_type('𐒠'), str_type('🄇')]:
            self.assertTrue(ch.isalnum(), str_type('{!a} is alnum.').format(ch)
                )

    def test_isalpha(self):
        super().test_isalpha()
        self.checkequalnofix(True, str_type('ῼ'), str_type('isalpha'))
        self.assertTrue(str_type('𐐁').isalpha())
        self.assertTrue(str_type('𐐧').isalpha())
        self.assertTrue(str_type('𐐩').isalpha())
        self.assertTrue(str_type('𐑎').isalpha())
        self.assertFalse(str_type('🐍').isalpha())
        self.assertFalse(str_type('👯').isalpha())

    def test_isascii(self):
        super().test_isascii()
        self.assertFalse(str_type('€').isascii())
        self.assertFalse(str_type('\U0010ffff').isascii())

    def test_isdecimal(self):
        self.checkequalnofix(False, str_type(''), str_type('isdecimal'))
        self.checkequalnofix(False, str_type('a'), str_type('isdecimal'))
        self.checkequalnofix(True, str_type('0'), str_type('isdecimal'))
        self.checkequalnofix(False, str_type('①'), str_type('isdecimal'))
        self.checkequalnofix(False, str_type('¼'), str_type('isdecimal'))
        self.checkequalnofix(True, str_type('٠'), str_type('isdecimal'))
        self.checkequalnofix(True, str_type('0123456789'), str_type(
            'isdecimal'))
        self.checkequalnofix(False, str_type('0123456789a'), str_type(
            'isdecimal'))
        self.checkraises(TypeError, str_type('abc'), str_type('isdecimal'), 42)
        for ch in [str_type('𐐁'), str_type('𐐧'), str_type('𐐩'), str_type(
            '𐑎'), str_type('🐍'), str_type('👯'), str_type('𑁥'), str_type('🄇')]:
            self.assertFalse(ch.isdecimal(), str_type(
                '{!a} is not decimal.').format(ch))
        for ch in [str_type('𝟶'), str_type('𑁦'), str_type('𐒠')]:
            self.assertTrue(ch.isdecimal(), str_type('{!a} is decimal.').
                format(ch))

    def test_isdigit(self):
        super().test_isdigit()
        self.checkequalnofix(True, str_type('①'), str_type('isdigit'))
        self.checkequalnofix(False, str_type('¼'), str_type('isdigit'))
        self.checkequalnofix(True, str_type('٠'), str_type('isdigit'))
        for ch in [str_type('𐐁'), str_type('𐐧'), str_type('𐐩'), str_type(
            '𐑎'), str_type('🐍'), str_type('👯'), str_type('𑁥')]:
            self.assertFalse(ch.isdigit(), str_type('{!a} is not a digit.')
                .format(ch))
        for ch in [str_type('𝟶'), str_type('𑁦'), str_type('𐒠'), str_type('🄇')]:
            self.assertTrue(ch.isdigit(), str_type('{!a} is a digit.').
                format(ch))

    def test_isnumeric(self):
        self.checkequalnofix(False, str_type(''), str_type('isnumeric'))
        self.checkequalnofix(False, str_type('a'), str_type('isnumeric'))
        self.checkequalnofix(True, str_type('0'), str_type('isnumeric'))
        self.checkequalnofix(True, str_type('①'), str_type('isnumeric'))
        self.checkequalnofix(True, str_type('¼'), str_type('isnumeric'))
        self.checkequalnofix(True, str_type('٠'), str_type('isnumeric'))
        self.checkequalnofix(True, str_type('0123456789'), str_type(
            'isnumeric'))
        self.checkequalnofix(False, str_type('0123456789a'), str_type(
            'isnumeric'))
        self.assertRaises(TypeError, str_type('abc').isnumeric, 42)
        for ch in [str_type('𐐁'), str_type('𐐧'), str_type('𐐩'), str_type(
            '𐑎'), str_type('🐍'), str_type('👯')]:
            self.assertFalse(ch.isnumeric(), str_type(
                '{!a} is not numeric.').format(ch))
        for ch in [str_type('𑁥'), str_type('𝟶'), str_type('𑁦'), str_type(
            '𐒠'), str_type('🄇')]:
            self.assertTrue(ch.isnumeric(), str_type('{!a} is numeric.').
                format(ch))

    def test_isidentifier(self):
        self.assertTrue(str_type('a').isidentifier())
        self.assertTrue(str_type('Z').isidentifier())
        self.assertTrue(str_type('_').isidentifier())
        self.assertTrue(str_type('b0').isidentifier())
        self.assertTrue(str_type('bc').isidentifier())
        self.assertTrue(str_type('b_').isidentifier())
        self.assertTrue(str_type('µ').isidentifier())
        self.assertTrue(str_type('𝔘𝔫𝔦𝔠𝔬𝔡𝔢').isidentifier())
        self.assertFalse(str_type(' ').isidentifier())
        self.assertFalse(str_type('[').isidentifier())
        self.assertFalse(str_type('©').isidentifier())
        self.assertFalse(str_type('0').isidentifier())

    def test_isprintable(self):
        self.assertTrue(str_type('').isprintable())
        self.assertTrue(str_type(' ').isprintable())
        self.assertTrue(str_type('abcdefg').isprintable())
        self.assertFalse(str_type('abcdefg\n').isprintable())
        self.assertTrue(str_type('ʹ').isprintable())
        self.assertFalse(str_type('\u0378').isprintable())
        self.assertFalse(str_type('\ud800').isprintable())
        self.assertTrue(str_type('👯').isprintable())
        self.assertFalse(str_type('\U000e0020').isprintable())

    # def test_surrogates(self):
    #     for s in (str_type('a\ud800b\udfff'), str_type('a\udfffb\ud800'),
    #         str_type('a\ud800b\udfffa'), str_type('a\udfffb\ud800a')):
    #         self.assertTrue(s.islower())
    #         self.assertFalse(s.isupper())
    #         self.assertFalse(s.istitle())
    #     for s in (str_type('A\ud800B\udfff'), str_type('A\udfffB\ud800'),
    #         str_type('A\ud800B\udfffA'), str_type('A\udfffB\ud800A')):
    #         self.assertFalse(s.islower())
    #         self.assertTrue(s.isupper())
    #         self.assertTrue(s.istitle())
    #     for meth_name in (str_type('islower'), str_type('isupper'),
    #         str_type('istitle')):
    #         meth = getattr(str_type, meth_name)
    #         for s in (str_type('\ud800'), str_type('\udfff'), str_type(
    #             '\ud800\ud800'), str_type('\udfff\udfff')):
    #             self.assertFalse(meth(s), str_type('%a.%s() is False') % (s,
    #                 meth_name))
    #     for meth_name in (str_type('isalpha'), str_type('isalnum'),
    #         str_type('isdigit'), str_type('isspace'), str_type('isdecimal'),
    #         str_type('isnumeric'), str_type('isidentifier'), str_type(
    #         'isprintable')):
    #         meth = getattr(str_type, meth_name)
    #         for s in (str_type('\ud800'), str_type('\udfff'), str_type(
    #             '\ud800\ud800'), str_type('\udfff\udfff'), str_type(
    #             'a\ud800b\udfff'), str_type('a\udfffb\ud800'), str_type(
    #             'a\ud800b\udfffa'), str_type('a\udfffb\ud800a')):
    #             self.assertFalse(meth(s), str_type('%a.%s() is False') % (s,
    #                 meth_name))

    def test_lower(self):
        string_tests.StringLikeTest.test_lower(self)
        self.assertEqual(str_type('𐐧').lower(), str_type('𐑏'))
        self.assertEqual(str_type('𐐧𐐧').lower(), str_type('𐑏𐑏'))
        self.assertEqual(str_type('𐐧𐑏').lower(), str_type('𐑏𐑏'))
        self.assertEqual(str_type('X𐐧x𐑏').lower(), str_type('x𐑏x𐑏'))
        self.assertEqual(str_type('ﬁ').lower(), str_type('ﬁ'))
        self.assertEqual(str_type('İ').lower(), str_type('i̇'))
        self.assertEqual(str_type('Σ').lower(), str_type('σ'))
        self.assertEqual(str_type('ͅΣ').lower(), str_type('ͅσ'))
        self.assertEqual(str_type('AͅΣ').lower(), str_type('aͅς'))
        self.assertEqual(str_type('AͅΣa').lower(), str_type('aͅσa'))
        self.assertEqual(str_type('AͅΣ').lower(), str_type('aͅς'))
        self.assertEqual(str_type('AΣͅ').lower(), str_type('aςͅ'))
        self.assertEqual(str_type('Σͅ ').lower(), str_type('σͅ '))
        self.assertEqual(str_type('\U0008fffe').lower(), str_type('\U0008fffe')
            )
        self.assertEqual(str_type('ⅷ').lower(), str_type('ⅷ'))

    def test_casefold(self):
        self.assertEqual(str_type('hello').casefold(), str_type('hello'))
        self.assertEqual(str_type('hELlo').casefold(), str_type('hello'))
        self.assertEqual(str_type('ß').casefold(), str_type('ss'))
        self.assertEqual(str_type('ﬁ').casefold(), str_type('fi'))
        self.assertEqual(str_type('Σ').casefold(), str_type('σ'))
        self.assertEqual(str_type('AͅΣ').casefold(), str_type('aισ'))
        self.assertEqual(str_type('µ').casefold(), str_type('μ'))

    def test_upper(self):
        string_tests.StringLikeTest.test_upper(self)
        self.assertEqual(str_type('𐑏').upper(), str_type('𐐧'))
        self.assertEqual(str_type('𐑏𐑏').upper(), str_type('𐐧𐐧'))
        self.assertEqual(str_type('𐐧𐑏').upper(), str_type('𐐧𐐧'))
        self.assertEqual(str_type('X𐐧x𐑏').upper(), str_type('X𐐧X𐐧'))
        self.assertEqual(str_type('ﬁ').upper(), str_type('FI'))
        self.assertEqual(str_type('İ').upper(), str_type('İ'))
        self.assertEqual(str_type('Σ').upper(), str_type('Σ'))
        self.assertEqual(str_type('ß').upper(), str_type('SS'))
        self.assertEqual(str_type('ῒ').upper(), str_type('Ϊ̀'))
        self.assertEqual(str_type('\U0008fffe').upper(), str_type('\U0008fffe')
            )
        self.assertEqual(str_type('ⅷ').upper(), str_type('Ⅷ'))

    def test_capitalize(self):
        string_tests.StringLikeTest.test_capitalize(self)
        self.assertEqual(str_type('𐑏').capitalize(), str_type('𐐧'))
        self.assertEqual(str_type('𐑏𐑏').capitalize(), str_type('𐐧𐑏'))
        self.assertEqual(str_type('𐐧𐑏').capitalize(), str_type('𐐧𐑏'))
        self.assertEqual(str_type('𐑏𐐧').capitalize(), str_type('𐐧𐑏'))
        self.assertEqual(str_type('X𐐧x𐑏').capitalize(), str_type('X𐑏x𐑏'))
        self.assertEqual(str_type('hİ').capitalize(), str_type('Hi̇'))
        exp = str_type('Ϊ̀i̇')
        self.assertEqual(str_type('ῒİ').capitalize(), exp)
        self.assertEqual(str_type('ﬁnnish').capitalize(), str_type('Finnish'))
        self.assertEqual(str_type('AͅΣ').capitalize(), str_type('Aͅς'))

    def test_title(self):
        super().test_title()
        self.assertEqual(str_type('𐑏').title(), str_type('𐐧'))
        self.assertEqual(str_type('𐑏𐑏').title(), str_type('𐐧𐑏'))
        self.assertEqual(str_type('𐑏𐑏 𐑏𐑏').title(), str_type('𐐧𐑏 𐐧𐑏'))
        self.assertEqual(str_type('𐐧𐑏 𐐧𐑏').title(), str_type('𐐧𐑏 𐐧𐑏'))
        self.assertEqual(str_type('𐑏𐐧 𐑏𐐧').title(), str_type('𐐧𐑏 𐐧𐑏'))
        self.assertEqual(str_type('X𐐧x𐑏 X𐐧x𐑏').title(), str_type('X𐑏x𐑏 X𐑏x𐑏'))
        self.assertEqual(str_type('ﬁNNISH').title(), str_type('Finnish'))
        self.assertEqual(str_type('AΣ ᾡxy').title(), str_type('Aς ᾩxy'))
        self.assertEqual(str_type('AΣA').title(), str_type('Aσa'))

    def test_swapcase(self):
        string_tests.StringLikeTest.test_swapcase(self)
        self.assertEqual(str_type('𐑏').swapcase(), str_type('𐐧'))
        self.assertEqual(str_type('𐐧').swapcase(), str_type('𐑏'))
        self.assertEqual(str_type('𐑏𐑏').swapcase(), str_type('𐐧𐐧'))
        self.assertEqual(str_type('𐐧𐑏').swapcase(), str_type('𐑏𐐧'))
        self.assertEqual(str_type('𐑏𐐧').swapcase(), str_type('𐐧𐑏'))
        self.assertEqual(str_type('X𐐧x𐑏').swapcase(), str_type('x𐑏X𐐧'))
        self.assertEqual(str_type('ﬁ').swapcase(), str_type('FI'))
        self.assertEqual(str_type('İ').swapcase(), str_type('i̇'))
        self.assertEqual(str_type('Σ').swapcase(), str_type('σ'))
        self.assertEqual(str_type('ͅΣ').swapcase(), str_type('Ισ'))
        self.assertEqual(str_type('AͅΣ').swapcase(), str_type('aΙς'))
        self.assertEqual(str_type('AͅΣa').swapcase(), str_type('aΙσA'))
        self.assertEqual(str_type('AͅΣ').swapcase(), str_type('aΙς'))
        self.assertEqual(str_type('AΣͅ').swapcase(), str_type('aςΙ'))
        self.assertEqual(str_type('Σͅ ').swapcase(), str_type('σΙ '))
        self.assertEqual(str_type('Σ').swapcase(), str_type('σ'))
        self.assertEqual(str_type('ß').swapcase(), str_type('SS'))
        self.assertEqual(str_type('ῒ').swapcase(), str_type('Ϊ̀'))

    def test_center(self):
        string_tests.StringLikeTest.test_center(self)
        self.assertEqual(str_type('x').center(2, str_type('\U0010ffff')),
            str_type('x\U0010ffff'))
        self.assertEqual(str_type('x').center(3, str_type('\U0010ffff')),
            str_type('\U0010ffffx\U0010ffff'))
        self.assertEqual(str_type('x').center(4, str_type('\U0010ffff')),
            str_type('\U0010ffffx\U0010ffff\U0010ffff'))

    @unittest.skipUnless(sys.maxsize == 2 ** 31 - 1, str_type(
        'requires 32-bit system'))
    @support.cpython_only
    def test_case_operation_overflow(self):
        size = 2 ** 32 // 12 + 1
        try:
            s = str_type('ü') * size
        except MemoryError:
            self.skipTest(str_type('no enough memory (%.0f MiB required)') %
                (size / 2 ** 20))
        try:
            self.assertRaises(OverflowError, s.upper)
        finally:
            del s

    # def test_contains(self):
    #     self.assertIn(str_type('a'), str_type('abdb'))
    #     self.assertIn(str_type('a'), str_type('bdab'))
    #     self.assertIn(str_type('a'), str_type('bdaba'))
    #     self.assertIn(str_type('a'), str_type('bdba'))
    #     self.assertNotIn(str_type('a'), str_type('bdb'))
    #     self.assertIn(str_type('a'), str_type('bdba'))
    #     self.assertIn(str_type('a'), (str_type('a'), 1, None))
    #     self.assertIn(str_type('a'), (1, None, str_type('a')))
    #     self.assertIn(str_type('a'), (str_type('a'), 1, None))
    #     self.assertIn(str_type('a'), (1, None, str_type('a')))
    #     self.assertNotIn(str_type('a'), (str_type('x'), 1, str_type('y')))
    #     self.assertNotIn(str_type('a'), (str_type('x'), 1, None))
    #     self.assertNotIn(str_type('abcd'), str_type('abcxxxx'))
    #     self.assertIn(str_type('ab'), str_type('abcd'))
    #     self.assertIn(str_type('ab'), str_type('abc'))
    #     self.assertIn(str_type('ab'), (1, None, str_type('ab')))
    #     self.assertIn(str_type(''), str_type('abc'))
    #     self.assertIn(str_type(''), str_type(''))
    #     self.assertIn(str_type(''), str_type('abc'))
    #     self.assertNotIn(str_type('\x00'), str_type('abc'))
    #     self.assertIn(str_type('\x00'), str_type('\x00abc'))
    #     self.assertIn(str_type('\x00'), str_type('abc\x00'))
    #     self.assertIn(str_type('a'), str_type('\x00abc'))
    #     self.assertIn(str_type('asdf'), str_type('asdf'))
    #     self.assertNotIn(str_type('asdf'), str_type('asd'))
    #     self.assertNotIn(str_type('asdf'), str_type(''))
    #     self.assertRaises(TypeError, str_type('abc').__contains__)
    #     for fill in (str_type('a'), str_type('Ā'), str_type('𐌀')):
    #         fill *= 9
    #         for delim in (str_type('c'), str_type('Ă'), str_type('𐌂')):
    #             self.assertNotIn(delim, fill)
    #             self.assertIn(delim, fill + delim)
    #             self.assertNotIn(delim * 2, fill)
    #             self.assertIn(delim * 2, fill + delim * 2)

    def test_issue18183(self):
        str_type('𐀀\U00100000').lower()
        str_type('𐀀\U00100000').casefold()
        str_type('𐀀\U00100000').upper()
        str_type('𐀀\U00100000').capitalize()
        str_type('𐀀\U00100000').title()
        str_type('𐀀\U00100000').swapcase()
        str_type('\U00100000').center(3, str_type('𐀀'))
        str_type('\U00100000').ljust(3, str_type('𐀀'))
        str_type('\U00100000').rjust(3, str_type('𐀀'))

    def test_format(self):
        self.assertEqual(str_type('').format(), str_type(''))
        self.assertEqual(str_type('a').format(), str_type('a'))
        self.assertEqual(str_type('ab').format(), str_type('ab'))
        self.assertEqual(str_type('a{{').format(), str_type('a{'))
        self.assertEqual(str_type('a}}').format(), str_type('a}'))
        self.assertEqual(str_type('{{b').format(), str_type('{b'))
        self.assertEqual(str_type('}}b').format(), str_type('}b'))
        self.assertEqual(str_type('a{{b').format(), str_type('a{b'))
        import datetime
        self.assertEqual(str_type('My name is {0}').format(str_type('Fred')
            ), str_type('My name is Fred'))
        self.assertEqual(str_type('My name is {0[name]}').format(dict(name=
            str_type('Fred'))), str_type('My name is Fred'))
        self.assertEqual(str_type('My name is {0} :-{{}}').format(str_type(
            'Fred')), str_type('My name is Fred :-{}'))
        d = datetime.date(2007, 8, 18)
        self.assertEqual(str_type('The year is {0.year}').format(d),
            str_type('The year is 2007'))


        class C:

            def __init__(self, x=100):
                self._x = x

            def __format__(self, spec):
                return spec


        class D:

            def __init__(self, x):
                self.x = x

            def __format__(self, spec):
                return str_type(self.x)


        class E:

            def __init__(self, x):
                self.x = x

            def __str__(self):
                return str_type('E(') + self.x + str_type(')')


        class F:

            def __init__(self, x):
                self.x = x

            def __repr__(self):
                return str_type('F(') + self.x + str_type(')')


        class G:

            def __init__(self, x):
                self.x = x

            def __str__(self):
                return str_type('string is ') + self.x

            def __format__(self, format_spec):
                if format_spec == str_type('d'):
                    return str_type('G(') + self.x + str_type(')')
                return object.__format__(self, format_spec)


        class I(datetime.date):

            def __format__(self, format_spec):
                return self.strftime(format_spec)


        class J(int):

            def __format__(self, format_spec):
                return int.__format__(self * 2, format_spec)


        class M:

            def __init__(self, x):
                self.x = x

            def __repr__(self):
                return str_type('M(') + self.x + str_type(')')
            __str__ = None


        class N:

            def __init__(self, x):
                self.x = x

            def __repr__(self):
                return str_type('N(') + self.x + str_type(')')
            __format__ = None
        self.assertEqual(str_type('').format(), str_type(''))
        self.assertEqual(str_type('abc').format(), str_type('abc'))
        self.assertEqual(str_type('{0}').format(str_type('abc')), str_type(
            'abc'))
        self.assertEqual(str_type('{0:}').format(str_type('abc')), str_type
            ('abc'))
        self.assertEqual(str_type('X{0}').format(str_type('abc')), str_type
            ('Xabc'))
        self.assertEqual(str_type('{0}X').format(str_type('abc')), str_type
            ('abcX'))
        self.assertEqual(str_type('X{0}Y').format(str_type('abc')),
            str_type('XabcY'))
        self.assertEqual(str_type('{1}').format(1, str_type('abc')),
            str_type('abc'))
        self.assertEqual(str_type('X{1}').format(1, str_type('abc')),
            str_type('Xabc'))
        self.assertEqual(str_type('{1}X').format(1, str_type('abc')),
            str_type('abcX'))
        self.assertEqual(str_type('X{1}Y').format(1, str_type('abc')),
            str_type('XabcY'))
        self.assertEqual(str_type('{0}').format(-15), str_type('-15'))
        self.assertEqual(str_type('{0}{1}').format(-15, str_type('abc')),
            str_type('-15abc'))
        self.assertEqual(str_type('{0}X{1}').format(-15, str_type('abc')),
            str_type('-15Xabc'))
        self.assertEqual(str_type('{{').format(), str_type('{'))
        self.assertEqual(str_type('}}').format(), str_type('}'))
        self.assertEqual(str_type('{{}}').format(), str_type('{}'))
        self.assertEqual(str_type('{{x}}').format(), str_type('{x}'))
        self.assertEqual(str_type('{{{0}}}').format(123), str_type('{123}'))
        self.assertEqual(str_type('{{{{0}}}}').format(), str_type('{{0}}'))
        self.assertEqual(str_type('}}{{').format(), str_type('}{'))
        self.assertEqual(str_type('}}x{{').format(), str_type('}x{'))
        self.assertEqual(str_type('{0[foo-bar]}').format({str_type(
            'foo-bar'): str_type('baz')}), str_type('baz'))
        self.assertEqual(str_type('{0[foo bar]}').format({str_type(
            'foo bar'): str_type('baz')}), str_type('baz'))
        self.assertEqual(str_type('{0[ ]}').format({str_type(' '): 3}),
            str_type('3'))
        self.assertEqual(str_type('{foo._x}').format(foo=C(20)), str_type('20')
            )
        self.assertEqual(str_type('{1}{0}').format(D(10), D(20)), str_type(
            '2010'))
        self.assertEqual(str_type('{0._x.x}').format(C(D(str_type('abc')))),
            str_type('abc'))
        self.assertEqual(str_type('{0[0]}').format([str_type('abc'),
            str_type('def')]), str_type('abc'))
        self.assertEqual(str_type('{0[1]}').format([str_type('abc'),
            str_type('def')]), str_type('def'))
        self.assertEqual(str_type('{0[1][0]}').format([str_type('abc'), [
            str_type('def')]]), str_type('def'))
        self.assertEqual(str_type('{0[1][0].x}').format([str_type('abc'), [
            D(str_type('def'))]]), str_type('def'))
        self.assertEqual(str_type('{0:.3s}').format(str_type('abc')),
            str_type('abc'))
        self.assertEqual(str_type('{0:.3s}').format(str_type('ab')),
            str_type('ab'))
        self.assertEqual(str_type('{0:.3s}').format(str_type('abcdef')),
            str_type('abc'))
        self.assertEqual(str_type('{0:.0s}').format(str_type('abcdef')),
            str_type(''))
        self.assertEqual(str_type('{0:3.3s}').format(str_type('abc')),
            str_type('abc'))
        self.assertEqual(str_type('{0:2.3s}').format(str_type('abc')),
            str_type('abc'))
        self.assertEqual(str_type('{0:2.2s}').format(str_type('abc')),
            str_type('ab'))
        self.assertEqual(str_type('{0:3.2s}').format(str_type('abc')),
            str_type('ab '))
        self.assertEqual(str_type('{0:x<0s}').format(str_type('result')),
            str_type('result'))
        self.assertEqual(str_type('{0:x<5s}').format(str_type('result')),
            str_type('result'))
        self.assertEqual(str_type('{0:x<6s}').format(str_type('result')),
            str_type('result'))
        self.assertEqual(str_type('{0:x<7s}').format(str_type('result')),
            str_type('resultx'))
        self.assertEqual(str_type('{0:x<8s}').format(str_type('result')),
            str_type('resultxx'))
        self.assertEqual(str_type('{0: <7s}').format(str_type('result')),
            str_type('result '))
        self.assertEqual(str_type('{0:<7s}').format(str_type('result')),
            str_type('result '))
        self.assertEqual(str_type('{0:>7s}').format(str_type('result')),
            str_type(' result'))
        self.assertEqual(str_type('{0:>8s}').format(str_type('result')),
            str_type('  result'))
        self.assertEqual(str_type('{0:^8s}').format(str_type('result')),
            str_type(' result '))
        self.assertEqual(str_type('{0:^9s}').format(str_type('result')),
            str_type(' result  '))
        self.assertEqual(str_type('{0:^10s}').format(str_type('result')),
            str_type('  result  '))
        self.assertEqual(str_type('{0:8s}').format(str_type('result')),
            str_type('result  '))
        self.assertEqual(str_type('{0:0s}').format(str_type('result')),
            str_type('result'))
        self.assertEqual(str_type('{0:08s}').format(str_type('result')),
            str_type('result00'))
        self.assertEqual(str_type('{0:<08s}').format(str_type('result')),
            str_type('result00'))
        self.assertEqual(str_type('{0:>08s}').format(str_type('result')),
            str_type('00result'))
        self.assertEqual(str_type('{0:^08s}').format(str_type('result')),
            str_type('0result0'))
        self.assertEqual(str_type('{0:10000}').format(str_type('a')),
            str_type('a') + str_type(' ') * 9999)
        self.assertEqual(str_type('{0:10000}').format(str_type('')),
            str_type(' ') * 10000)
        self.assertEqual(str_type('{0:10000000}').format(str_type('')),
            str_type(' ') * 10000000)
        self.assertEqual(str_type('{0:\x00<6s}').format(str_type('foo')),
            str_type('foo\x00\x00\x00'))
        self.assertEqual(str_type('{0:\x01<6s}').format(str_type('foo')),
            str_type('foo\x01\x01\x01'))
        self.assertEqual(str_type('{0:\x00^6s}').format(str_type('foo')),
            str_type('\x00foo\x00\x00'))
        self.assertEqual(str_type('{0:^6s}').format(str_type('foo')),
            str_type(' foo  '))
        self.assertEqual(str_type('{0:\x00<6}').format(3), str_type(
            '3\x00\x00\x00\x00\x00'))
        self.assertEqual(str_type('{0:\x01<6}').format(3), str_type(
            '3\x01\x01\x01\x01\x01'))
        self.assertEqual(str_type('{0:\x00^6}').format(3), str_type(
            '\x00\x003\x00\x00\x00'))
        self.assertEqual(str_type('{0:<6}').format(3), str_type('3     '))
        self.assertEqual(str_type('{0:\x00<6}').format(3.14), str_type(
            '3.14\x00\x00'))
        self.assertEqual(str_type('{0:\x01<6}').format(3.14), str_type(
            '3.14\x01\x01'))
        self.assertEqual(str_type('{0:\x00^6}').format(3.14), str_type(
            '\x003.14\x00'))
        self.assertEqual(str_type('{0:^6}').format(3.14), str_type(' 3.14 '))
        self.assertEqual(str_type('{0:\x00<12}').format(3 + 2.0j), str_type
            ('(3+2j)\x00\x00\x00\x00\x00\x00'))
        self.assertEqual(str_type('{0:\x01<12}').format(3 + 2.0j), str_type
            ('(3+2j)\x01\x01\x01\x01\x01\x01'))
        self.assertEqual(str_type('{0:\x00^12}').format(3 + 2.0j), str_type
            ('\x00\x00\x00(3+2j)\x00\x00\x00'))
        self.assertEqual(str_type('{0:^12}').format(3 + 2.0j), str_type(
            '   (3+2j)   '))
        self.assertEqual(str_type('{0:abc}').format(C()), str_type('abc'))
        self.assertEqual(str_type('{0!s}').format(str_type('Hello')),
            str_type('Hello'))
        self.assertEqual(str_type('{0!s:}').format(str_type('Hello')),
            str_type('Hello'))
        self.assertEqual(str_type('{0!s:15}').format(str_type('Hello')),
            str_type('Hello          '))
        self.assertEqual(str_type('{0!s:15s}').format(str_type('Hello')),
            str_type('Hello          '))
        self.assertEqual(str_type('{0!r}').format(str_type('Hello')),
            str_type("'Hello'"))
        self.assertEqual(str_type('{0!r:}').format(str_type('Hello')),
            str_type("'Hello'"))
        self.assertEqual(str_type('{0!r}').format(F(str_type('Hello'))),
            str_type('F(Hello)'))
        self.assertEqual(str_type('{0!r}').format(str_type('\u0378')),
            str_type("'\\u0378'"))
        self.assertEqual(str_type('{0!r}').format(str_type('ʹ')), str_type(
            "'ʹ'"))
        self.assertEqual(str_type('{0!r}').format(F(str_type('ʹ'))),
            str_type('F(ʹ)'))
        self.assertEqual(str_type('{0!a}').format(str_type('Hello')),
            str_type("'Hello'"))
        self.assertEqual(str_type('{0!a}').format(str_type('\u0378')),
            str_type("'\\u0378'"))
        self.assertEqual(str_type('{0!a}').format(str_type('ʹ')), str_type(
            "'\\u0374'"))
        self.assertEqual(str_type('{0!a:}').format(str_type('Hello')),
            str_type("'Hello'"))
        self.assertEqual(str_type('{0!a}').format(F(str_type('Hello'))),
            str_type('F(Hello)'))
        self.assertEqual(str_type('{0!a}').format(F(str_type('ʹ'))),
            str_type('F(\\u0374)'))
        self.assertEqual(str_type('{0}').format({}), str_type('{}'))
        self.assertEqual(str_type('{0}').format([]), str_type('[]'))
        self.assertEqual(str_type('{0}').format([1]), str_type('[1]'))
        self.assertEqual(str_type('{0:d}').format(G(str_type('data'))),
            str_type('G(data)'))
        self.assertEqual(str_type('{0!s}').format(G(str_type('data'))),
            str_type('string is data'))
        self.assertRaises(TypeError, str_type('{0:^10}').format, E(str_type
            ('data')))
        self.assertRaises(TypeError, str_type('{0:^10s}').format, E(
            str_type('data')))
        self.assertRaises(TypeError, str_type('{0:>15s}').format, G(
            str_type('data')))
        self.assertEqual(str_type('{0:date: %Y-%m-%d}').format(I(year=2007,
            month=8, day=27)), str_type('date: 2007-08-27'))
        self.assertEqual(str_type('{0}').format(J(10)), str_type('20'))
        self.assertEqual(str_type('{0:}').format(str_type('a')), str_type('a'))
        self.assertEqual(str_type('{0:.{1}}').format(str_type('hello world'
            ), 5), str_type('hello'))
        self.assertEqual(str_type('{0:.{1}s}').format(str_type(
            'hello world'), 5), str_type('hello'))
        self.assertEqual(str_type('{0:.{precision}s}').format(str_type(
            'hello world'), precision=5), str_type('hello'))
        self.assertEqual(str_type('{0:{width}.{precision}s}').format(
            str_type('hello world'), width=10, precision=5), str_type(
            'hello     '))
        self.assertEqual(str_type('{0:{width}.{precision}s}').format(
            str_type('hello world'), width=str_type('10'), precision=
            str_type('5')), str_type('hello     '))
        self.assertRaises(ValueError, str_type('{').format)
        self.assertRaises(ValueError, str_type('}').format)
        self.assertRaises(ValueError, str_type('a{').format)
        self.assertRaises(ValueError, str_type('a}').format)
        self.assertRaises(ValueError, str_type('{a').format)
        self.assertRaises(ValueError, str_type('}a').format)
        self.assertRaises(IndexError, str_type('{0}').format)
        self.assertRaises(IndexError, str_type('{1}').format, str_type('abc'))
        self.assertRaises(KeyError, str_type('{x}').format)
        self.assertRaises(ValueError, str_type('}{').format)
        self.assertRaises(ValueError, str_type('abc{0:{}').format)
        self.assertRaises(ValueError, str_type('{0').format)
        self.assertRaises(IndexError, str_type('{0.}').format)
        self.assertRaises(ValueError, str_type('{0.}').format, 0)
        self.assertRaises(ValueError, str_type('{0[}').format)
        self.assertRaises(ValueError, str_type('{0[}').format, [])
        self.assertRaises(KeyError, str_type('{0]}').format)
        self.assertRaises(ValueError, str_type('{0.[]}').format, 0)
        self.assertRaises(ValueError, str_type('{0..foo}').format, 0)
        self.assertRaises(ValueError, str_type('{0[0}').format, 0)
        self.assertRaises(ValueError, str_type('{0[0:foo}').format, 0)
        self.assertRaises(KeyError, str_type('{c]}').format)
        self.assertRaises(ValueError, str_type('{{ {{{0}}').format, 0)
        self.assertRaises(ValueError, str_type('{0}}').format, 0)
        self.assertRaises(KeyError, str_type('{foo}').format, bar=3)
        self.assertRaises(ValueError, str_type('{0!x}').format, 3)
        self.assertRaises(ValueError, str_type('{0!}').format, 0)
        self.assertRaises(ValueError, str_type('{0!rs}').format, 0)
        self.assertRaises(ValueError, str_type('{!}').format)
        self.assertRaises(IndexError, str_type('{:}').format)
        self.assertRaises(IndexError, str_type('{:s}').format)
        self.assertRaises(IndexError, str_type('{}').format)
        big = str_type('23098475029384702983476098230754973209482573')
        self.assertRaises(ValueError, (str_type('{') + big + str_type('}'))
            .format)
        self.assertRaises(ValueError, (str_type('{[') + big + str_type(']}'
            )).format, [0])
        self.assertRaises(ValueError, str_type('{0:x}').format, 1.0j)
        self.assertRaises(ValueError, str_type('{0:x}').format, 1.0)
        self.assertRaises(ValueError, str_type('{0:X}').format, 1.0j)
        self.assertRaises(ValueError, str_type('{0:X}').format, 1.0)
        self.assertRaises(ValueError, str_type('{0:o}').format, 1.0j)
        self.assertRaises(ValueError, str_type('{0:o}').format, 1.0)
        self.assertRaises(ValueError, str_type('{0:u}').format, 1.0j)
        self.assertRaises(ValueError, str_type('{0:u}').format, 1.0)
        self.assertRaises(ValueError, str_type('{0:i}').format, 1.0j)
        self.assertRaises(ValueError, str_type('{0:i}').format, 1.0)
        self.assertRaises(ValueError, str_type('{0:d}').format, 1.0j)
        self.assertRaises(ValueError, str_type('{0:d}').format, 1.0)
        self.assertRaises(ValueError, str_type('{0[0]x}').format, [None])
        self.assertRaises(ValueError, str_type('{0[0](10)}').format, [None])
        self.assertRaises(TypeError, str_type('{0[{1}]}').format, str_type(
            'abcdefg'), 4)
        self.assertRaises(ValueError, str_type('{0:{1:{2}}}').format,
            str_type('abc'), str_type('s'), str_type(''))
        self.assertRaises(ValueError, str_type(
            '{0:{1:{2:{3:{4:{5:{6}}}}}}}').format, 0, 1, 2, 3, 4, 5, 6, 7)
        sign_msg = str_type('Sign not allowed in string format specifier')
        self.assertRaisesRegex(ValueError, sign_msg, str_type('{0:-s}').
            format, str_type(''))
        self.assertRaisesRegex(ValueError, sign_msg, format, str_type(''),
            str_type('-'))
        space_msg = str_type('Space not allowed in string format specifier')
        self.assertRaisesRegex(ValueError, space_msg, str_type('{: }').
            format, str_type(''))
        self.assertRaises(ValueError, str_type('{0:=s}').format, str_type(''))
        self.assertRaises(ValueError, format, str_type(''), str_type('#'))
        self.assertRaises(ValueError, format, str_type(''), str_type('#20'))
        self.assertEqual(str_type('{0:s}{1:s}').format(str_type('ABC'),
            str_type('АБВ')), str_type('ABCАБВ'))
        self.assertEqual(str_type('{0:.3s}').format(str_type('ABCАБВ')),
            str_type('ABC'))
        self.assertEqual(str_type('{0:.0s}').format(str_type('ABCАБВ')),
            str_type(''))
        self.assertEqual(str_type('{[{}]}').format({str_type('{}'): 5}),
            str_type('5'))
        self.assertEqual(str_type('{[{}]}').format({str_type('{}'):
            str_type('a')}), str_type('a'))
        self.assertEqual(str_type('{[{]}').format({str_type('{'): str_type(
            'a')}), str_type('a'))
        self.assertEqual(str_type('{[}]}').format({str_type('}'): str_type(
            'a')}), str_type('a'))
        self.assertEqual(str_type('{[[]}').format({str_type('['): str_type(
            'a')}), str_type('a'))
        self.assertEqual(str_type('{[!]}').format({str_type('!'): str_type(
            'a')}), str_type('a'))
        self.assertRaises(ValueError, str_type('{a{}b}').format, 42)
        self.assertRaises(ValueError, str_type('{a{b}').format, 42)
        self.assertRaises(ValueError, str_type('{[}').format, 42)
        self.assertEqual(str_type('0x{:0{:d}X}').format(0, 16), str_type(
            '0x0000000000000000'))
        m = M(str_type('data'))
        self.assertEqual(str_type('{!r}').format(m), str_type('M(data)'))
        self.assertRaises(TypeError, str_type('{!s}').format, m)
        self.assertRaises(TypeError, str_type('{}').format, m)
        n = N(str_type('data'))
        self.assertEqual(str_type('{!r}').format(n), str_type('N(data)'))
        self.assertEqual(str_type('{!s}').format(n), str_type('N(data)'))
        self.assertRaises(TypeError, str_type('{}').format, n)

    def test_format_map(self):
        self.assertEqual(str_type('').format_map({}), str_type(''))
        self.assertEqual(str_type('a').format_map({}), str_type('a'))
        self.assertEqual(str_type('ab').format_map({}), str_type('ab'))
        self.assertEqual(str_type('a{{').format_map({}), str_type('a{'))
        self.assertEqual(str_type('a}}').format_map({}), str_type('a}'))
        self.assertEqual(str_type('{{b').format_map({}), str_type('{b'))
        self.assertEqual(str_type('}}b').format_map({}), str_type('}b'))
        self.assertEqual(str_type('a{{b').format_map({}), str_type('a{b'))


        class Mapping(dict):

            def __missing__(self, key):
                return key
        self.assertEqual(str_type('{hello}').format_map(Mapping()),
            str_type('hello'))
        self.assertEqual(str_type('{a} {world}').format_map(Mapping(a=
            str_type('hello'))), str_type('hello world'))


        class InternalMapping:

            def __init__(self):
                self.mapping = {str_type('a'): str_type('hello')}

            def __getitem__(self, key):
                return self.mapping[key]
        self.assertEqual(str_type('{a}').format_map(InternalMapping()),
            str_type('hello'))


        class C:

            def __init__(self, x=100):
                self._x = x

            def __format__(self, spec):
                return spec
        self.assertEqual(str_type('{foo._x}').format_map({str_type('foo'):
            C(20)}), str_type('20'))
        self.assertRaises(TypeError, str_type('').format_map)
        self.assertRaises(TypeError, str_type('a').format_map)
        self.assertRaises(ValueError, str_type('{').format_map, {})
        self.assertRaises(ValueError, str_type('}').format_map, {})
        self.assertRaises(ValueError, str_type('a{').format_map, {})
        self.assertRaises(ValueError, str_type('a}').format_map, {})
        self.assertRaises(ValueError, str_type('{a').format_map, {})
        self.assertRaises(ValueError, str_type('}a').format_map, {})
        self.assertRaises(ValueError, str_type('{}').format_map, {str_type(
            'a'): 2})
        self.assertRaises(ValueError, str_type('{}').format_map, str_type('a'))
        self.assertRaises(ValueError, str_type('{a} {}').format_map, {
            str_type('a'): 2, str_type('b'): 1})


        class BadMapping:

            def __getitem__(self, key):
                return 1 / 0
        self.assertRaises(KeyError, str_type('{a}').format_map, {})
        self.assertRaises(TypeError, str_type('{a}').format_map, [])
        self.assertRaises(ZeroDivisionError, str_type('{a}').format_map,
            BadMapping())

    def test_format_huge_precision(self):
        format_string = str_type('.{}f').format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format(2.34, format_string)

    def test_format_huge_width(self):
        format_string = str_type('{}f').format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format(2.34, format_string)

    def test_format_huge_item_number(self):
        format_string = str_type('{{{}:.6f}}').format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format_string.format(2.34)

    def test_format_auto_numbering(self):


        class C:

            def __init__(self, x=100):
                self._x = x

            def __format__(self, spec):
                return spec
        self.assertEqual(str_type('{}').format(10), str_type('10'))
        self.assertEqual(str_type('{:5}').format(str_type('s')), str_type(
            's    '))
        self.assertEqual(str_type('{!r}').format(str_type('s')), str_type(
            "'s'"))
        self.assertEqual(str_type('{._x}').format(C(10)), str_type('10'))
        self.assertEqual(str_type('{[1]}').format([1, 2]), str_type('2'))
        self.assertEqual(str_type('{[a]}').format({str_type('a'): 4,
            str_type('b'): 2}), str_type('4'))
        self.assertEqual(str_type('a{}b{}c').format(0, 1), str_type('a0b1c'))
        self.assertEqual(str_type('a{:{}}b').format(str_type('x'), str_type
            ('^10')), str_type('a    x     b'))
        self.assertEqual(str_type('a{:{}x}b').format(20, str_type('#')),
            str_type('a0x14b'))
        self.assertRaises(ValueError, str_type('{}{1}').format, 1, 2)
        self.assertRaises(ValueError, str_type('{1}{}').format, 1, 2)
        self.assertRaises(ValueError, str_type('{:{1}}').format, 1, 2)
        self.assertRaises(ValueError, str_type('{0:{}}').format, 1, 2)
        self.assertEqual(str_type('{f}{}').format(4, f=str_type('test')),
            str_type('test4'))
        self.assertEqual(str_type('{}{f}').format(4, f=str_type('test')),
            str_type('4test'))
        self.assertEqual(str_type('{:{f}}{g}{}').format(1, 3, g=str_type(
            'g'), f=2), str_type(' 1g3'))
        self.assertEqual(str_type('{f:{}}{}{g}').format(2, 4, f=1, g=
            str_type('g')), str_type(' 14g'))

    def test_formatting(self):
        string_tests.StringLikeTest.test_formatting(self)
        self.assertEqual(str_type('%s, %s') % (str_type('abc'), str_type(
            'abc')), str_type('abc, abc'))
        self.assertEqual(str_type('%s, %s, %i, %f, %5.2f') % (str_type(
            'abc'), str_type('abc'), 1, 2, 3), str_type(
            'abc, abc, 1, 2.000000,  3.00'))
        self.assertEqual(str_type('%s, %s, %i, %f, %5.2f') % (str_type(
            'abc'), str_type('abc'), 1, -2, 3), str_type(
            'abc, abc, 1, -2.000000,  3.00'))
        self.assertEqual(str_type('%s, %s, %i, %f, %5.2f') % (str_type(
            'abc'), str_type('abc'), -1, -2, 3.5), str_type(
            'abc, abc, -1, -2.000000,  3.50'))
        self.assertEqual(str_type('%s, %s, %i, %f, %5.2f') % (str_type(
            'abc'), str_type('abc'), -1, -2, 3.57), str_type(
            'abc, abc, -1, -2.000000,  3.57'))
        self.assertEqual(str_type('%s, %s, %i, %f, %5.2f') % (str_type(
            'abc'), str_type('abc'), -1, -2, 1003.57), str_type(
            'abc, abc, -1, -2.000000, 1003.57'))
        self.assertEqual(str_type('%r, %r') % (b'abc', str_type('abc')),
            str_type("b'abc', 'abc'"))
        self.assertEqual(str_type('%r') % (str_type('ሴ'),), str_type("'ሴ'"))
        self.assertEqual(str_type('%a') % (str_type('ሴ'),), str_type(
            "'\\u1234'"))
        self.assertEqual(str_type('%(x)s, %(y)s') % {str_type('x'):
            str_type('abc'), str_type('y'): str_type('def')}, str_type(
            'abc, def'))
        self.assertEqual(str_type('%(x)s, %(ü)s') % {str_type('x'):
            str_type('abc'), str_type('ü'): str_type('def')}, str_type(
            'abc, def'))
        self.assertEqual(str_type('%c') % 4660, str_type('ሴ'))
        self.assertEqual(str_type('%c') % 136323, str_type('𡒃'))
        self.assertRaises(OverflowError, str_type('%c').__mod__, (1114112,))
        self.assertEqual(str_type('%c') % str_type('𡒃'), str_type('𡒃'))
        self.assertRaises(TypeError, str_type('%c').__mod__, str_type('aa'))
        self.assertRaises(ValueError, str_type('%.1ဲf').__mod__, 1.0 / 3)
        self.assertRaises(TypeError, str_type('%i').__mod__, str_type('aa'))
        self.assertEqual(str_type('...%(foo)s...') % {str_type('foo'):
            str_type('abc')}, str_type('...abc...'))
        self.assertEqual(str_type('...%(foo)s...') % {str_type('foo'):
            str_type('abc')}, str_type('...abc...'))
        self.assertEqual(str_type('...%(foo)s...') % {str_type('foo'):
            str_type('abc')}, str_type('...abc...'))
        self.assertEqual(str_type('...%(foo)s...') % {str_type('foo'):
            str_type('abc')}, str_type('...abc...'))
        self.assertEqual(str_type('...%(foo)s...') % {str_type('foo'):
            str_type('abc'), str_type('def'): 123}, str_type('...abc...'))
        self.assertEqual(str_type('...%(foo)s...') % {str_type('foo'):
            str_type('abc'), str_type('def'): 123}, str_type('...abc...'))
        self.assertEqual(str_type('...%s...%s...%s...%s...') % (1, 2, 3,
            str_type('abc')), str_type('...1...2...3...abc...'))
        self.assertEqual(str_type('...%%...%%s...%s...%s...%s...%s...') % (
            1, 2, 3, str_type('abc')), str_type(
            '...%...%s...1...2...3...abc...'))
        self.assertEqual(str_type('...%s...') % str_type('abc'), str_type(
            '...abc...'))
        self.assertEqual(str_type('%*s') % (5, str_type('abc')), str_type(
            '  abc'))
        self.assertEqual(str_type('%*s') % (-5, str_type('abc')), str_type(
            'abc  '))
        self.assertEqual(str_type('%*.*s') % (5, 2, str_type('abc')),
            str_type('   ab'))
        self.assertEqual(str_type('%*.*s') % (5, 3, str_type('abc')),
            str_type('  abc'))
        self.assertEqual(str_type('%i %*.*s') % (10, 5, 3, str_type('abc')),
            str_type('10   abc'))
        self.assertEqual(str_type('%i%s %*.*s') % (10, 3, 5, 3, str_type(
            'abc')), str_type('103   abc'))
        self.assertEqual(str_type('%c') % str_type('a'), str_type('a'))


        class Wrapper:

            def __str__(self):
                return str_type('ሴ')
        self.assertEqual(str_type('%s') % Wrapper(), str_type('ሴ'))
        NAN = float(str_type('nan'))
        INF = float(str_type('inf'))
        self.assertEqual(str_type('%f') % NAN, str_type('nan'))
        self.assertEqual(str_type('%F') % NAN, str_type('NAN'))
        self.assertEqual(str_type('%f') % INF, str_type('inf'))
        self.assertEqual(str_type('%F') % INF, str_type('INF'))
        self.assertEqual(str_type('%.1s') % str_type('aé€'), str_type('a'))
        self.assertEqual(str_type('%.2s') % str_type('aé€'), str_type('aé'))


        class PseudoInt:

            def __init__(self, value):
                self.value = int(value)

            def __int__(self):
                return self.value

            def __index__(self):
                return self.value


        class PseudoFloat:

            def __init__(self, value):
                self.value = float(value)

            def __int__(self):
                return int(self.value)
        pi = PseudoFloat(3.1415)
        letter_m = PseudoInt(109)
        self.assertEqual(str_type('%x') % 42, str_type('2a'))
        self.assertEqual(str_type('%X') % 15, str_type('F'))
        self.assertEqual(str_type('%o') % 9, str_type('11'))
        self.assertEqual(str_type('%c') % 109, str_type('m'))
        self.assertEqual(str_type('%x') % letter_m, str_type('6d'))
        self.assertEqual(str_type('%X') % letter_m, str_type('6D'))
        self.assertEqual(str_type('%o') % letter_m, str_type('155'))
        self.assertEqual(str_type('%c') % letter_m, str_type('m'))
        self.assertRaisesRegex(TypeError, str_type(
            '%x format: an integer is required, not float'), operator.mod,
            str_type('%x'), 3.14)
        self.assertRaisesRegex(TypeError, str_type(
            '%X format: an integer is required, not float'), operator.mod,
            str_type('%X'), 2.11)
        self.assertRaisesRegex(TypeError, str_type(
            '%o format: an integer is required, not float'), operator.mod,
            str_type('%o'), 1.79)
        self.assertRaisesRegex(TypeError, str_type(
            '%x format: an integer is required, not PseudoFloat'), operator
            .mod, str_type('%x'), pi)
        self.assertRaisesRegex(TypeError, str_type(
            '%x format: an integer is required, not complex'), operator.mod,
            str_type('%x'), 3.0j)
        self.assertRaisesRegex(TypeError, str_type(
            '%X format: an integer is required, not complex'), operator.mod,
            str_type('%X'), 2.0j)
        self.assertRaisesRegex(TypeError, str_type(
            '%o format: an integer is required, not complex'), operator.mod,
            str_type('%o'), 1.0j)
        self.assertRaisesRegex(TypeError, str_type(
            '%u format: a real number is required, not complex'), operator.
            mod, str_type('%u'), 3.0j)
        self.assertRaisesRegex(TypeError, str_type(
            '%i format: a real number is required, not complex'), operator.
            mod, str_type('%i'), 2.0j)
        self.assertRaisesRegex(TypeError, str_type(
            '%d format: a real number is required, not complex'), operator.
            mod, str_type('%d'), 1.0j)
        self.assertRaisesRegex(TypeError, str_type(
            '%c requires an int or a unicode character, not .*\\.PseudoFloat'
            ), operator.mod, str_type('%c'), pi)


        class RaisingNumber:

            def __int__(self):
                raise RuntimeError(str_type('int'))

            def __index__(self):
                raise RuntimeError(str_type('index'))
        rn = RaisingNumber()
        self.assertRaisesRegex(RuntimeError, str_type('int'), operator.mod,
            str_type('%d'), rn)
        self.assertRaisesRegex(RuntimeError, str_type('int'), operator.mod,
            str_type('%i'), rn)
        self.assertRaisesRegex(RuntimeError, str_type('int'), operator.mod,
            str_type('%u'), rn)
        self.assertRaisesRegex(RuntimeError, str_type('index'), operator.
            mod, str_type('%x'), rn)
        self.assertRaisesRegex(RuntimeError, str_type('index'), operator.
            mod, str_type('%X'), rn)
        self.assertRaisesRegex(RuntimeError, str_type('index'), operator.
            mod, str_type('%o'), rn)

    def test_formatting_with_enum(self):
        import enum


        class Float(float, enum.Enum):
            PI = 3.1415926


        class Int(enum.IntEnum):
            IDES = 15


        class Str(enum.StrEnum):
            ABC = str_type('abc')
        self.assertEqual(str_type('%s, %s') % (Str.ABC, Str.ABC), str_type(
            'abc, abc'))
        self.assertEqual(str_type('%s, %s, %d, %i, %u, %f, %5.2f') % (Str.
            ABC, Str.ABC, Int.IDES, Int.IDES, Int.IDES, Float.PI, Float.PI),
            str_type('abc, abc, 15, 15, 15, 3.141593,  3.14'))
        self.assertEqual(str_type('...%(foo)s...') % {str_type('foo'): Str.
            ABC}, str_type('...abc...'))
        self.assertEqual(str_type('...%(foo)r...') % {str_type('foo'): Int.
            IDES}, str_type('...<Int.IDES: 15>...'))
        self.assertEqual(str_type('...%(foo)s...') % {str_type('foo'): Int.
            IDES}, str_type('...15...'))
        self.assertEqual(str_type('...%(foo)i...') % {str_type('foo'): Int.
            IDES}, str_type('...15...'))
        self.assertEqual(str_type('...%(foo)d...') % {str_type('foo'): Int.
            IDES}, str_type('...15...'))
        self.assertEqual(str_type('...%(foo)u...') % {str_type('foo'): Int.
            IDES, str_type('def'): Float.PI}, str_type('...15...'))
        self.assertEqual(str_type('...%(foo)f...') % {str_type('foo'):
            Float.PI, str_type('def'): 123}, str_type('...3.141593...'))

    def test_formatting_huge_precision(self):
        format_string = str_type('%.{}f').format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format_string % 2.34

    def test_issue28598_strsubclass_rhs(self):


        class SubclassedStr(str_type):

            def __rmod__(self, other):
                return str_type('Success, self.__rmod__({!r}) was called'
                    ).format(other)
        self.assertEqual(str_type('lhs %% %r') % SubclassedStr(str_type(
            'rhs')), str_type("Success, self.__rmod__('lhs %% %r') was called")
            )

    @support.cpython_only
    @unittest.skipIf(_testcapi is None, str_type('need _testcapi module'))
    def test_formatting_huge_precision_c_limits(self):
        format_string = str_type('%.{}f').format(_testcapi.INT_MAX + 1)
        with self.assertRaises(ValueError):
            result = format_string % 2.34

    def test_formatting_huge_width(self):
        format_string = str_type('%{}f').format(sys.maxsize + 1)
        with self.assertRaises(ValueError):
            result = format_string % 2.34

    def test_startswith_endswith_errors(self):
        for meth in (str_type('foo').startswith, str_type('foo').endswith):
            with self.assertRaises(TypeError) as cm:
                meth([str_type('f')])
            exc = str_type(cm.exception)
            self.assertIn(str_type('str'), exc)
            self.assertIn(str_type('tuple'), exc)

    @support.run_with_locale(str_type('LC_ALL'), str_type('de_DE'),
        str_type('fr_FR'), str_type(''))
    def test_format_float(self):
        self.assertEqual(str_type('1.0'), str_type('%.1f') % 1.0)

    # def test_constructor(self):
    #     self.assertEqual(str_type(str_type('unicode remains unicode')), str_type
    #         ('unicode remains unicode'))
    #     for text in (str_type('ascii'), str_type('é'), str_type('€'),
    #         str_type('\U0010ffff')):
    #         subclass = StrSubclass(text)
    #         self.assertEqual(str_type(subclass), text)
    #         self.assertEqual(len(subclass), len(text))
    #         if text == str_type('ascii'):
    #             self.assertEqual(subclass.encode(str_type('ascii')), b'ascii')
    #             self.assertEqual(subclass.encode(str_type('utf-8')), b'ascii')
    #     self.assertEqual(str_type(str_type('strings are converted to unicode')),
    #         str_type('strings are converted to unicode'))


    #     class StringCompat:

    #         def __init__(self, x):
    #             self.x = x

    #         def __str__(self):
    #             return self.x
    #     self.assertEqual(str_type(StringCompat(str_type(
    #         '__str__ compatible objects are recognized'))), str_type(
    #         '__str__ compatible objects are recognized'))
    #     o = StringCompat(str_type('unicode(obj) is compatible to str_type()'))
    #     self.assertEqual(str_type(o), str_type(
    #         'unicode(obj) is compatible to str_type()'))
    #     self.assertEqual(str_type(o), str_type(
    #         'unicode(obj) is compatible to str_type()'))
    #     for obj in (123, 123.45, 123):
    #         self.assertEqual(str_type(obj), str_type(str_type(obj)))
    #     self.assertRaises(TypeError, str_type, str_type(
    #         'decoding unicode is not supported'), str_type('utf-8'),
    #         str_type('strict'))
    #     self.assertEqual(str_type(b'strings are decoded to unicode', str_type(
    #         'utf-8'), str_type('strict')), str_type(
    #         'strings are decoded to unicode'))
    #     self.assertEqual(str_type(memoryview(
    #         b'character buffers are decoded to unicode'), str_type('utf-8'),
    #         str_type('strict')), str_type(
    #         'character buffers are decoded to unicode'))

    # def test_constructor_keyword_args(self):
    #     str_type(
    #         'Pass various keyword argument combinations to the constructor.')
    #     self.assertEqual(str_type(object=str_type('foo')), str_type('foo'))
    #     self.assertEqual(str_type(object=b'foo', encoding=str_type('utf-8')),
    #         str_type('foo'))
    #     self.assertEqual(str_type(b'foo', errors=str_type('strict')), str_type(
    #         'foo'))
    #     self.assertEqual(str_type(object=b'foo', errors=str_type('strict')),
    #         str_type('foo'))

    # def test_constructor_defaults(self):
    #     str_type('Check the constructor argument defaults.')
    #     self.assertEqual(str_type(), str_type(''))
    #     self.assertEqual(str_type(errors=str_type('strict')), str_type(''))
    #     utf8_cent = str_type('¢').encode(str_type('utf-8'))
    #     self.assertEqual(str_type(utf8_cent, errors=str_type('strict')),
    #         str_type('¢'))
    #     self.assertRaises(UnicodeDecodeError, str_type, utf8_cent, encoding=
    #         str_type('ascii'))

    def test_codecs_utf7(self):
        utfTests = [(str_type('A≢Α.'), b'A+ImIDkQ.'), (str_type(
            'Hi Mom -☺-!'), b'Hi Mom -+Jjo--!'), (str_type('日本語'),
            b'+ZeVnLIqe-'), (str_type('Item 3 is £1.'),
            b'Item 3 is +AKM-1.'), (str_type('+'), b'+-'), (str_type('+-'),
            b'+--'), (str_type('+?'), b'+-?'), (str_type('\\?'), b'+AFw?'),
            (str_type('+?'), b'+-?'), (str_type('\\\\?'), b'+AFwAXA?'), (
            str_type('\\\\\\?'), b'+AFwAXABc?'), (str_type('++--'),
            b'+-+---'), (str_type('\U000abcde'), b'+2m/c3g-'), (str_type(
            '/'), b'/')]
        for x, y in utfTests:
            self.assertEqual(x.encode(str_type('utf-7')), y)
        self.assertEqual(str_type('\ud801').encode(str_type('utf-7')), b'+2AE-'
            )
        self.assertEqual(str_type('\ud801x').encode(str_type('utf-7')),
            b'+2AE-x')
        self.assertEqual(str_type('\udc01').encode(str_type('utf-7')), b'+3AE-'
            )
        self.assertEqual(str_type('\udc01x').encode(str_type('utf-7')),
            b'+3AE-x')
        self.assertEqual(b'+2AE-'.decode(str_type('utf-7')), str_type('\ud801')
            )
        self.assertEqual(b'+2AE-x'.decode(str_type('utf-7')), str_type(
            '\ud801x'))
        self.assertEqual(b'+3AE-'.decode(str_type('utf-7')), str_type('\udc01')
            )
        self.assertEqual(b'+3AE-x'.decode(str_type('utf-7')), str_type(
            '\udc01x'))
        self.assertEqual(str_type('\ud801\U000abcde').encode(str_type(
            'utf-7')), b'+2AHab9ze-')
        self.assertEqual(b'+2AHab9ze-'.decode(str_type('utf-7')), str_type(
            '\ud801\U000abcde'))
        self.assertEqual(b'+\xc1'.decode(str_type('utf-7'), str_type(
            'ignore')), str_type(''))
        set_d = str_type(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'(),-./:?"
            )
        set_o = str_type('!"#$%&*;<=>@[]^_`{|}')
        for c in set_d:
            self.assertEqual(c.encode(str_type('utf7')), c.encode(str_type(
                'ascii')))
            self.assertEqual(c.encode(str_type('ascii')).decode(str_type(
                'utf7')), c)
        for c in set_o:
            self.assertEqual(c.encode(str_type('ascii')).decode(str_type(
                'utf7')), c)
        with self.assertRaisesRegex(UnicodeDecodeError, str_type(
            'ill-formed sequence')):
            b'+@'.decode(str_type('utf-7'))

    def test_codecs_utf8(self):
        self.assertEqual(str_type('').encode(str_type('utf-8')), b'')
        self.assertEqual(str_type('€').encode(str_type('utf-8')),
            b'\xe2\x82\xac')
        self.assertEqual(str_type('𐀂').encode(str_type('utf-8')),
            b'\xf0\x90\x80\x82')
        self.assertEqual(str_type('𣑖').encode(str_type('utf-8')),
            b'\xf0\xa3\x91\x96')
        self.assertEqual(str_type('\ud800').encode(str_type('utf-8'),
            str_type('surrogatepass')), b'\xed\xa0\x80')
        self.assertEqual(str_type('\udc00').encode(str_type('utf-8'),
            str_type('surrogatepass')), b'\xed\xb0\x80')
        self.assertEqual((str_type('𐀂') * 10).encode(str_type('utf-8')),
            b'\xf0\x90\x80\x82' * 10)
        self.assertEqual(str_type(
            '正確に言うと翻訳はされていません。一部はドイツ語ですが、あとはでたらめです。実際には「Wenn ist das Nunstuck git und'
            ).encode(str_type('utf-8')),
            b'\xe6\xad\xa3\xe7\xa2\xba\xe3\x81\xab\xe8\xa8\x80\xe3\x81\x86\xe3\x81\xa8\xe7\xbf\xbb\xe8\xa8\xb3\xe3\x81\xaf\xe3\x81\x95\xe3\x82\x8c\xe3\x81\xa6\xe3\x81\x84\xe3\x81\xbe\xe3\x81\x9b\xe3\x82\x93\xe3\x80\x82\xe4\xb8\x80\xe9\x83\xa8\xe3\x81\xaf\xe3\x83\x89\xe3\x82\xa4\xe3\x83\x84\xe8\xaa\x9e\xe3\x81\xa7\xe3\x81\x99\xe3\x81\x8c\xe3\x80\x81\xe3\x81\x82\xe3\x81\xa8\xe3\x81\xaf\xe3\x81\xa7\xe3\x81\x9f\xe3\x82\x89\xe3\x82\x81\xe3\x81\xa7\xe3\x81\x99\xe3\x80\x82\xe5\xae\x9f\xe9\x9a\x9b\xe3\x81\xab\xe3\x81\xaf\xe3\x80\x8cWenn ist das Nunstuck git und'
            )
        self.assertEqual(str_type(b'\xf0\xa3\x91\x96', str_type('utf-8')),
            str_type('𣑖'))
        self.assertEqual(str_type(b'\xf0\x90\x80\x82', str_type('utf-8')),
            str_type('𐀂'))
        self.assertEqual(str_type(b'\xe2\x82\xac', str_type('utf-8')), str_type('€')
            )

    def test_utf8_decode_valid_sequences(self):
        sequences = [(b'\x00', str_type('\x00')), (b'a', str_type('a')), (
            b'\x7f', str_type('\x7f')), (b'\xc2\x80', str_type('\x80')), (
            b'\xdf\xbf', str_type('߿')), (b'\xe0\xa0\x80', str_type('ࠀ')),
            (b'\xed\x9f\xbf', str_type('\ud7ff')), (b'\xee\x80\x80',
            str_type('\ue000')), (b'\xef\xbf\xbf', str_type('\uffff')), (
            b'\xf0\x90\x80\x80', str_type('𐀀')), (b'\xf4\x8f\xbf\xbf',
            str_type('\U0010ffff'))]
        for seq, res in sequences:
            self.assertEqual(seq.decode(str_type('utf-8')), res)

    def test_utf8_decode_invalid_sequences(self):
        continuation_bytes = [bytes([x]) for x in range(128, 192)]
        invalid_2B_seq_start_bytes = [bytes([x]) for x in range(192, 194)]
        invalid_4B_seq_start_bytes = [bytes([x]) for x in range(245, 248)]
        invalid_start_bytes = (continuation_bytes +
            invalid_2B_seq_start_bytes + invalid_4B_seq_start_bytes + [
            bytes([x]) for x in range(247, 256)])
        for byte in invalid_start_bytes:
            self.assertRaises(UnicodeDecodeError, byte.decode, str_type(
                'utf-8'))
        for sb in invalid_2B_seq_start_bytes:
            for cb in continuation_bytes:
                self.assertRaises(UnicodeDecodeError, (sb + cb).decode,
                    str_type('utf-8'))
        for sb in invalid_4B_seq_start_bytes:
            for cb1 in continuation_bytes[:3]:
                for cb3 in continuation_bytes[:3]:
                    self.assertRaises(UnicodeDecodeError, (sb + cb1 +
                        b'\x80' + cb3).decode, str_type('utf-8'))
        for cb in [bytes([x]) for x in range(128, 160)]:
            self.assertRaises(UnicodeDecodeError, (b'\xe0' + cb + b'\x80').
                decode, str_type('utf-8'))
            self.assertRaises(UnicodeDecodeError, (b'\xe0' + cb + b'\xbf').
                decode, str_type('utf-8'))
        for cb in [bytes([x]) for x in range(160, 192)]:
            self.assertRaises(UnicodeDecodeError, (b'\xed' + cb + b'\x80').
                decode, str_type('utf-8'))
            self.assertRaises(UnicodeDecodeError, (b'\xed' + cb + b'\xbf').
                decode, str_type('utf-8'))
        for cb in [bytes([x]) for x in range(128, 144)]:
            self.assertRaises(UnicodeDecodeError, (b'\xf0' + cb +
                b'\x80\x80').decode, str_type('utf-8'))
            self.assertRaises(UnicodeDecodeError, (b'\xf0' + cb +
                b'\xbf\xbf').decode, str_type('utf-8'))
        for cb in [bytes([x]) for x in range(144, 192)]:
            self.assertRaises(UnicodeDecodeError, (b'\xf4' + cb +
                b'\x80\x80').decode, str_type('utf-8'))
            self.assertRaises(UnicodeDecodeError, (b'\xf4' + cb +
                b'\xbf\xbf').decode, str_type('utf-8'))

    def test_issue127903(self):
        d = datetime.datetime(2013, 11, 10, 14, 20, 59)
        self.assertEqual(d.strftime(str_type('%z')), str_type(''))

    def test_issue8271(self):
        FFFD = str_type('�')
        sequences = [(b'\x80', FFFD), (b'\x80\x80', FFFD * 2), (b'\xc0',
            FFFD), (b'\xc0\xc0', FFFD * 2), (b'\xc1', FFFD), (b'\xc1\xc0',
            FFFD * 2), (b'\xc0\xc1', FFFD * 2), (b'\xc2', FFFD), (
            b'\xc2\xc2', FFFD * 2), (b'\xc2\xc2\xc2', FFFD * 3), (b'\xc2A',
            FFFD + str_type('A')), (b'\xe1', FFFD), (b'\xe1\xe1', FFFD * 2),
            (b'\xe1\xe1\xe1', FFFD * 3), (b'\xe1\xe1\xe1\xe1', FFFD * 4), (
            b'\xe1\x80', FFFD), (b'\xe1A', FFFD + str_type('A')), (
            b'\xe1A\x80', FFFD + str_type('A') + FFFD), (b'\xe1AA', FFFD +
            str_type('AA')), (b'\xe1\x80A', FFFD + str_type('A')), (
            b'\xe1\x80\xe1A', FFFD * 2 + str_type('A')), (b'\xe1A\xe1\x80',
            FFFD + str_type('A') + FFFD), (b'\xf1', FFFD), (b'\xf1\xf1',
            FFFD * 2), (b'\xf1\xf1\xf1', FFFD * 3), (b'\xf1\xf1\xf1\xf1',
            FFFD * 4), (b'\xf1\xf1\xf1\xf1\xf1', FFFD * 5), (b'\xf1\x80',
            FFFD), (b'\xf1\x80\x80', FFFD), (b'\xf1\x80A', FFFD + str_type(
            'A')), (b'\xf1\x80AA', FFFD + str_type('AA')), (
            b'\xf1\x80\x80A', FFFD + str_type('A')), (b'\xf1A\x80', FFFD +
            str_type('A') + FFFD), (b'\xf1A\x80\x80', FFFD + str_type('A') +
            FFFD * 2), (b'\xf1A\x80A', FFFD + str_type('A') + FFFD +
            str_type('A')), (b'\xf1AA\x80', FFFD + str_type('AA') + FFFD),
            (b'\xf1A\xf1\x80', FFFD + str_type('A') + FFFD), (
            b'\xf1A\x80\xf1', FFFD + str_type('A') + FFFD * 2), (
            b'\xf1\xf1\x80A', FFFD * 2 + str_type('A')), (b'\xf1A\xf1\xf1',
            FFFD + str_type('A') + FFFD * 2), (b'\xf5', FFFD), (b'\xf5\xf5',
            FFFD * 2), (b'\xf5\x80', FFFD * 2), (b'\xf5\x80\x80', FFFD * 3),
            (b'\xf5\x80\x80\x80', FFFD * 4), (b'\xf5\x80A', FFFD * 2 +
            str_type('A')), (b'\xf5\x80A\xf5', FFFD * 2 + str_type('A') +
            FFFD), (b'\xf5A\x80\x80A', FFFD + str_type('A') + FFFD * 2 +
            str_type('A')), (b'\xf8', FFFD), (b'\xf8\xf8', FFFD * 2), (
            b'\xf8\x80', FFFD * 2), (b'\xf8\x80A', FFFD * 2 + str_type('A')
            ), (b'\xf8\x80\x80\x80\x80', FFFD * 5), (b'\xfc', FFFD), (
            b'\xfc\xfc', FFFD * 2), (b'\xfc\x80\x80', FFFD * 3), (
            b'\xfc\x80\x80\x80\x80\x80', FFFD * 6), (b'\xfe', FFFD), (
            b'\xfe\x80\x80', FFFD * 3), (b'\xf1\x80ABC', str_type('�ABC')),
            (b'\xf1\x80\xffBC', str_type('��BC')), (b'\xf1\x80\xc2\x81C',
            str_type('�\x81C')), (
            b'a\xf1\x80\x80\xe1\x80\xc2b\x80c\x80\xbfd', str_type(
            'a���b�c��d'))]
        for n, (seq, res) in enumerate(sequences):
            self.assertRaises(UnicodeDecodeError, seq.decode, str_type(
                'utf-8'), str_type('strict'))
            self.assertEqual(seq.decode(str_type('utf-8'), str_type(
                'replace')), res)
            self.assertEqual((seq + b'b').decode(str_type('utf-8'),
                str_type('replace')), res + str_type('b'))
            self.assertEqual(seq.decode(str_type('utf-8'), str_type(
                'ignore')), res.replace(str_type('�'), str_type('')))

    def assertCorrectUTF8Decoding(self, seq, res, err):
        str_type(
            """
        Check that an invalid UTF-8 sequence raises a UnicodeDecodeError when
        'strict' is used, returns res when 'replace' is used, and that doesn't
        return anything when 'ignore' is used.
        """
            )
        with self.assertRaises(UnicodeDecodeError) as cm:
            seq.decode(str_type('utf-8'))
        exc = cm.exception
        self.assertIn(err, str_type(exc))
        self.assertEqual(seq.decode(str_type('utf-8'), str_type('replace')),
            res)
        self.assertEqual((b'aaaa' + seq + b'bbbb').decode(str_type('utf-8'),
            str_type('replace')), str_type('aaaa') + res + str_type('bbbb'))
        res = res.replace(str_type('�'), str_type(''))
        self.assertEqual(seq.decode(str_type('utf-8'), str_type('ignore')), res
            )
        self.assertEqual((b'aaaa' + seq + b'bbbb').decode(str_type('utf-8'),
            str_type('ignore')), str_type('aaaa') + res + str_type('bbbb'))

    def test_invalid_start_byte(self):
        str_type(
            """
        Test that an 'invalid start byte' error is raised when the first byte
        is not in the ASCII range or is not a valid start byte of a 2-, 3-, or
        4-bytes sequence. The invalid start byte is replaced with a single
        U+FFFD when errors='replace'.
        E.g. <80> is a continuation byte and can appear only after a start byte.
        """
            )
        FFFD = str_type('�')
        for byte in b'\x80\xa0\x9f\xbf\xc0\xc1\xf5\xff':
            self.assertCorrectUTF8Decoding(bytes([byte]), str_type('�'),
                str_type('invalid start byte'))

    def test_unexpected_end_of_data(self):
        str_type(
            """
        Test that an 'unexpected end of data' error is raised when the string
        ends after a start byte of a 2-, 3-, or 4-bytes sequence without having
        enough continuation bytes.  The incomplete sequence is replaced with a
        single U+FFFD when errors='replace'.
        E.g. in the sequence <F3 80 80>, F3 is the start byte of a 4-bytes
        sequence, but it's followed by only 2 valid continuation bytes and the
        last continuation bytes is missing.
        Note: the continuation bytes must be all valid, if one of them is
        invalid another error will be raised.
        """
            )
        sequences = [str_type('C2'), str_type('DF'), str_type('E0 A0'),
            str_type('E0 BF'), str_type('E1 80'), str_type('E1 BF'),
            str_type('EC 80'), str_type('EC BF'), str_type('ED 80'),
            str_type('ED 9F'), str_type('EE 80'), str_type('EE BF'),
            str_type('EF 80'), str_type('EF BF'), str_type('F0 90'),
            str_type('F0 BF'), str_type('F0 90 80'), str_type('F0 90 BF'),
            str_type('F0 BF 80'), str_type('F0 BF BF'), str_type('F1 80'),
            str_type('F1 BF'), str_type('F1 80 80'), str_type('F1 80 BF'),
            str_type('F1 BF 80'), str_type('F1 BF BF'), str_type('F3 80'),
            str_type('F3 BF'), str_type('F3 80 80'), str_type('F3 80 BF'),
            str_type('F3 BF 80'), str_type('F3 BF BF'), str_type('F4 80'),
            str_type('F4 8F'), str_type('F4 80 80'), str_type('F4 80 BF'),
            str_type('F4 8F 80'), str_type('F4 8F BF')]
        FFFD = str_type('�')
        for seq in sequences:
            self.assertCorrectUTF8Decoding(bytes.fromhex(seq), str_type('�'
                ), str_type('unexpected end of data'))

    def test_invalid_cb_for_2bytes_seq(self):
        str_type(
            """
        Test that an 'invalid continuation byte' error is raised when the
        continuation byte of a 2-bytes sequence is invalid.  The start byte
        is replaced by a single U+FFFD and the second byte is handled
        separately when errors='replace'.
        E.g. in the sequence <C2 41>, C2 is the start byte of a 2-bytes
        sequence, but 41 is not a valid continuation byte because it's the
        ASCII letter 'A'.
        """
            )
        FFFD = str_type('�')
        FFFDx2 = FFFD * 2
        sequences = [(str_type('C2 00'), FFFD + str_type('\x00')), (
            str_type('C2 7F'), FFFD + str_type('\x7f')), (str_type('C2 C0'),
            FFFDx2), (str_type('C2 FF'), FFFDx2), (str_type('DF 00'), FFFD +
            str_type('\x00')), (str_type('DF 7F'), FFFD + str_type('\x7f')),
            (str_type('DF C0'), FFFDx2), (str_type('DF FF'), FFFDx2)]
        for seq, res in sequences:
            self.assertCorrectUTF8Decoding(bytes.fromhex(seq), res,
                str_type('invalid continuation byte'))

    def test_invalid_cb_for_3bytes_seq(self):
        str_type(
            """
        Test that an 'invalid continuation byte' error is raised when the
        continuation byte(s) of a 3-bytes sequence are invalid.  When
        errors='replace', if the first continuation byte is valid, the first
        two bytes (start byte + 1st cb) are replaced by a single U+FFFD and the
        third byte is handled separately, otherwise only the start byte is
        replaced with a U+FFFD and the other continuation bytes are handled
        separately.
        E.g. in the sequence <E1 80 41>, E1 is the start byte of a 3-bytes
        sequence, 80 is a valid continuation byte, but 41 is not a valid cb
        because it's the ASCII letter 'A'.
        Note: when the start byte is E0 or ED, the valid ranges for the first
        continuation byte are limited to A0..BF and 80..9F respectively.
        Python 2 used to consider all the bytes in range 80..BF valid when the
        start byte was ED.  This is fixed in Python 3.
        """
            )
        FFFD = str_type('�')
        FFFDx2 = FFFD * 2
        sequences = [(str_type('E0 00'), FFFD + str_type('\x00')), (
            str_type('E0 7F'), FFFD + str_type('\x7f')), (str_type('E0 80'),
            FFFDx2), (str_type('E0 9F'), FFFDx2), (str_type('E0 C0'),
            FFFDx2), (str_type('E0 FF'), FFFDx2), (str_type('E0 A0 00'),
            FFFD + str_type('\x00')), (str_type('E0 A0 7F'), FFFD +
            str_type('\x7f')), (str_type('E0 A0 C0'), FFFDx2), (str_type(
            'E0 A0 FF'), FFFDx2), (str_type('E0 BF 00'), FFFD + str_type(
            '\x00')), (str_type('E0 BF 7F'), FFFD + str_type('\x7f')), (
            str_type('E0 BF C0'), FFFDx2), (str_type('E0 BF FF'), FFFDx2),
            (str_type('E1 00'), FFFD + str_type('\x00')), (str_type('E1 7F'
            ), FFFD + str_type('\x7f')), (str_type('E1 C0'), FFFDx2), (
            str_type('E1 FF'), FFFDx2), (str_type('E1 80 00'), FFFD +
            str_type('\x00')), (str_type('E1 80 7F'), FFFD + str_type(
            '\x7f')), (str_type('E1 80 C0'), FFFDx2), (str_type('E1 80 FF'),
            FFFDx2), (str_type('E1 BF 00'), FFFD + str_type('\x00')), (
            str_type('E1 BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'E1 BF C0'), FFFDx2), (str_type('E1 BF FF'), FFFDx2), (str_type
            ('EC 00'), FFFD + str_type('\x00')), (str_type('EC 7F'), FFFD +
            str_type('\x7f')), (str_type('EC C0'), FFFDx2), (str_type(
            'EC FF'), FFFDx2), (str_type('EC 80 00'), FFFD + str_type(
            '\x00')), (str_type('EC 80 7F'), FFFD + str_type('\x7f')), (
            str_type('EC 80 C0'), FFFDx2), (str_type('EC 80 FF'), FFFDx2),
            (str_type('EC BF 00'), FFFD + str_type('\x00')), (str_type(
            'EC BF 7F'), FFFD + str_type('\x7f')), (str_type('EC BF C0'),
            FFFDx2), (str_type('EC BF FF'), FFFDx2), (str_type('ED 00'),
            FFFD + str_type('\x00')), (str_type('ED 7F'), FFFD + str_type(
            '\x7f')), (str_type('ED A0'), FFFDx2), (str_type('ED BF'),
            FFFDx2), (str_type('ED C0'), FFFDx2), (str_type('ED FF'),
            FFFDx2), (str_type('ED 80 00'), FFFD + str_type('\x00')), (
            str_type('ED 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'ED 80 C0'), FFFDx2), (str_type('ED 80 FF'), FFFDx2), (str_type
            ('ED 9F 00'), FFFD + str_type('\x00')), (str_type('ED 9F 7F'),
            FFFD + str_type('\x7f')), (str_type('ED 9F C0'), FFFDx2), (
            str_type('ED 9F FF'), FFFDx2), (str_type('EE 00'), FFFD +
            str_type('\x00')), (str_type('EE 7F'), FFFD + str_type('\x7f')),
            (str_type('EE C0'), FFFDx2), (str_type('EE FF'), FFFDx2), (
            str_type('EE 80 00'), FFFD + str_type('\x00')), (str_type(
            'EE 80 7F'), FFFD + str_type('\x7f')), (str_type('EE 80 C0'),
            FFFDx2), (str_type('EE 80 FF'), FFFDx2), (str_type('EE BF 00'),
            FFFD + str_type('\x00')), (str_type('EE BF 7F'), FFFD +
            str_type('\x7f')), (str_type('EE BF C0'), FFFDx2), (str_type(
            'EE BF FF'), FFFDx2), (str_type('EF 00'), FFFD + str_type(
            '\x00')), (str_type('EF 7F'), FFFD + str_type('\x7f')), (
            str_type('EF C0'), FFFDx2), (str_type('EF FF'), FFFDx2), (
            str_type('EF 80 00'), FFFD + str_type('\x00')), (str_type(
            'EF 80 7F'), FFFD + str_type('\x7f')), (str_type('EF 80 C0'),
            FFFDx2), (str_type('EF 80 FF'), FFFDx2), (str_type('EF BF 00'),
            FFFD + str_type('\x00')), (str_type('EF BF 7F'), FFFD +
            str_type('\x7f')), (str_type('EF BF C0'), FFFDx2), (str_type(
            'EF BF FF'), FFFDx2)]
        for seq, res in sequences:
            self.assertCorrectUTF8Decoding(bytes.fromhex(seq), res,
                str_type('invalid continuation byte'))

    def test_invalid_cb_for_4bytes_seq(self):
        str_type(
            """
        Test that an 'invalid continuation byte' error is raised when the
        continuation byte(s) of a 4-bytes sequence are invalid.  When
        errors='replace',the start byte and all the following valid
        continuation bytes are replaced with a single U+FFFD, and all the bytes
        starting from the first invalid continuation bytes (included) are
        handled separately.
        E.g. in the sequence <E1 80 41>, E1 is the start byte of a 3-bytes
        sequence, 80 is a valid continuation byte, but 41 is not a valid cb
        because it's the ASCII letter 'A'.
        Note: when the start byte is E0 or ED, the valid ranges for the first
        continuation byte are limited to A0..BF and 80..9F respectively.
        However, when the start byte is ED, Python 2 considers all the bytes
        in range 80..BF valid.  This is fixed in Python 3.
        """
            )
        FFFD = str_type('�')
        FFFDx2 = FFFD * 2
        sequences = [(str_type('F0 00'), FFFD + str_type('\x00')), (
            str_type('F0 7F'), FFFD + str_type('\x7f')), (str_type('F0 80'),
            FFFDx2), (str_type('F0 8F'), FFFDx2), (str_type('F0 C0'),
            FFFDx2), (str_type('F0 FF'), FFFDx2), (str_type('F0 90 00'),
            FFFD + str_type('\x00')), (str_type('F0 90 7F'), FFFD +
            str_type('\x7f')), (str_type('F0 90 C0'), FFFDx2), (str_type(
            'F0 90 FF'), FFFDx2), (str_type('F0 BF 00'), FFFD + str_type(
            '\x00')), (str_type('F0 BF 7F'), FFFD + str_type('\x7f')), (
            str_type('F0 BF C0'), FFFDx2), (str_type('F0 BF FF'), FFFDx2),
            (str_type('F0 90 80 00'), FFFD + str_type('\x00')), (str_type(
            'F0 90 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'F0 90 80 C0'), FFFDx2), (str_type('F0 90 80 FF'), FFFDx2), (
            str_type('F0 90 BF 00'), FFFD + str_type('\x00')), (str_type(
            'F0 90 BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F0 90 BF C0'), FFFDx2), (str_type('F0 90 BF FF'), FFFDx2), (
            str_type('F0 BF 80 00'), FFFD + str_type('\x00')), (str_type(
            'F0 BF 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'F0 BF 80 C0'), FFFDx2), (str_type('F0 BF 80 FF'), FFFDx2), (
            str_type('F0 BF BF 00'), FFFD + str_type('\x00')), (str_type(
            'F0 BF BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F0 BF BF C0'), FFFDx2), (str_type('F0 BF BF FF'), FFFDx2), (
            str_type('F1 00'), FFFD + str_type('\x00')), (str_type('F1 7F'),
            FFFD + str_type('\x7f')), (str_type('F1 C0'), FFFDx2), (
            str_type('F1 FF'), FFFDx2), (str_type('F1 80 00'), FFFD +
            str_type('\x00')), (str_type('F1 80 7F'), FFFD + str_type(
            '\x7f')), (str_type('F1 80 C0'), FFFDx2), (str_type('F1 80 FF'),
            FFFDx2), (str_type('F1 BF 00'), FFFD + str_type('\x00')), (
            str_type('F1 BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F1 BF C0'), FFFDx2), (str_type('F1 BF FF'), FFFDx2), (str_type
            ('F1 80 80 00'), FFFD + str_type('\x00')), (str_type(
            'F1 80 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'F1 80 80 C0'), FFFDx2), (str_type('F1 80 80 FF'), FFFDx2), (
            str_type('F1 80 BF 00'), FFFD + str_type('\x00')), (str_type(
            'F1 80 BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F1 80 BF C0'), FFFDx2), (str_type('F1 80 BF FF'), FFFDx2), (
            str_type('F1 BF 80 00'), FFFD + str_type('\x00')), (str_type(
            'F1 BF 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'F1 BF 80 C0'), FFFDx2), (str_type('F1 BF 80 FF'), FFFDx2), (
            str_type('F1 BF BF 00'), FFFD + str_type('\x00')), (str_type(
            'F1 BF BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F1 BF BF C0'), FFFDx2), (str_type('F1 BF BF FF'), FFFDx2), (
            str_type('F3 00'), FFFD + str_type('\x00')), (str_type('F3 7F'),
            FFFD + str_type('\x7f')), (str_type('F3 C0'), FFFDx2), (
            str_type('F3 FF'), FFFDx2), (str_type('F3 80 00'), FFFD +
            str_type('\x00')), (str_type('F3 80 7F'), FFFD + str_type(
            '\x7f')), (str_type('F3 80 C0'), FFFDx2), (str_type('F3 80 FF'),
            FFFDx2), (str_type('F3 BF 00'), FFFD + str_type('\x00')), (
            str_type('F3 BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F3 BF C0'), FFFDx2), (str_type('F3 BF FF'), FFFDx2), (str_type
            ('F3 80 80 00'), FFFD + str_type('\x00')), (str_type(
            'F3 80 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'F3 80 80 C0'), FFFDx2), (str_type('F3 80 80 FF'), FFFDx2), (
            str_type('F3 80 BF 00'), FFFD + str_type('\x00')), (str_type(
            'F3 80 BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F3 80 BF C0'), FFFDx2), (str_type('F3 80 BF FF'), FFFDx2), (
            str_type('F3 BF 80 00'), FFFD + str_type('\x00')), (str_type(
            'F3 BF 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'F3 BF 80 C0'), FFFDx2), (str_type('F3 BF 80 FF'), FFFDx2), (
            str_type('F3 BF BF 00'), FFFD + str_type('\x00')), (str_type(
            'F3 BF BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F3 BF BF C0'), FFFDx2), (str_type('F3 BF BF FF'), FFFDx2), (
            str_type('F4 00'), FFFD + str_type('\x00')), (str_type('F4 7F'),
            FFFD + str_type('\x7f')), (str_type('F4 90'), FFFDx2), (
            str_type('F4 BF'), FFFDx2), (str_type('F4 C0'), FFFDx2), (
            str_type('F4 FF'), FFFDx2), (str_type('F4 80 00'), FFFD +
            str_type('\x00')), (str_type('F4 80 7F'), FFFD + str_type(
            '\x7f')), (str_type('F4 80 C0'), FFFDx2), (str_type('F4 80 FF'),
            FFFDx2), (str_type('F4 8F 00'), FFFD + str_type('\x00')), (
            str_type('F4 8F 7F'), FFFD + str_type('\x7f')), (str_type(
            'F4 8F C0'), FFFDx2), (str_type('F4 8F FF'), FFFDx2), (str_type
            ('F4 80 80 00'), FFFD + str_type('\x00')), (str_type(
            'F4 80 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'F4 80 80 C0'), FFFDx2), (str_type('F4 80 80 FF'), FFFDx2), (
            str_type('F4 80 BF 00'), FFFD + str_type('\x00')), (str_type(
            'F4 80 BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F4 80 BF C0'), FFFDx2), (str_type('F4 80 BF FF'), FFFDx2), (
            str_type('F4 8F 80 00'), FFFD + str_type('\x00')), (str_type(
            'F4 8F 80 7F'), FFFD + str_type('\x7f')), (str_type(
            'F4 8F 80 C0'), FFFDx2), (str_type('F4 8F 80 FF'), FFFDx2), (
            str_type('F4 8F BF 00'), FFFD + str_type('\x00')), (str_type(
            'F4 8F BF 7F'), FFFD + str_type('\x7f')), (str_type(
            'F4 8F BF C0'), FFFDx2), (str_type('F4 8F BF FF'), FFFDx2)]
        for seq, res in sequences:
            self.assertCorrectUTF8Decoding(bytes.fromhex(seq), res,
                str_type('invalid continuation byte'))

    def test_codecs_idna(self):
        self.assertEqual(str_type('www.python.org.').encode(str_type('idna'
            )), b'www.python.org.')

    def test_codecs_errors(self):
        self.assertRaises(UnicodeError, str_type('Andr\x82 x').encode,
            str_type('ascii'))
        self.assertRaises(UnicodeError, str_type('Andr\x82 x').encode,
            str_type('ascii'), str_type('strict'))
        self.assertEqual(str_type('Andr\x82 x').encode(str_type('ascii'),
            str_type('ignore')), b'Andr x')
        self.assertEqual(str_type('Andr\x82 x').encode(str_type('ascii'),
            str_type('replace')), b'Andr? x')
        self.assertEqual(str_type('Andr\x82 x').encode(str_type('ascii'),
            str_type('replace')), str_type('Andr\x82 x').encode(str_type(
            'ascii'), errors=str_type('replace')))
        self.assertEqual(str_type('Andr\x82 x').encode(str_type('ascii'),
            str_type('ignore')), str_type('Andr\x82 x').encode(encoding=
            str_type('ascii'), errors=str_type('ignore')))
        self.assertRaises(UnicodeError, str_type, b'Andr\x82 x', str_type('ascii'))
        self.assertRaises(UnicodeError, str_type, b'Andr\x82 x', str_type(
            'ascii'), str_type('strict'))
        self.assertEqual(str_type(b'Andr\x82 x', str_type('ascii'), str_type(
            'ignore')), str_type('Andr x'))
        self.assertEqual(str_type(b'Andr\x82 x', str_type('ascii'), str_type(
            'replace')), str_type('Andr� x'))
        self.assertEqual(str_type(b'\x82 x', str_type('ascii'), str_type(
            'replace')), str_type('� x'))
        self.assertEqual(b'\\N{foo}xx'.decode(str_type('unicode-escape'),
            str_type('ignore')), str_type('xx'))
        self.assertRaises(UnicodeError, b'\\'.decode, str_type(
            'unicode-escape'))
        self.assertRaises(TypeError, b'hello'.decode, str_type('test.unicode1')
            )
        self.assertRaises(TypeError, str_type, b'hello', str_type('test.unicode2'))
        self.assertRaises(TypeError, str_type('hello').encode, str_type(
            'test.unicode1'))
        self.assertRaises(TypeError, str_type('hello').encode, str_type(
            'test.unicode2'))
        self.assertRaises(TypeError, str_type('hello').encode, 42, 42, 42)
        self.assertRaises(ValueError, int, str_type('\ud800'))
        self.assertRaises(ValueError, int, str_type('\udf00'))
        self.assertRaises(ValueError, float, str_type('\ud800'))
        self.assertRaises(ValueError, float, str_type('\udf00'))
        self.assertRaises(ValueError, complex, str_type('\ud800'))
        self.assertRaises(ValueError, complex, str_type('\udf00'))

    def test_codecs(self):
        self.assertEqual(str_type('hello').encode(str_type('ascii')), b'hello')
        self.assertEqual(str_type('hello').encode(str_type('utf-7')), b'hello')
        self.assertEqual(str_type('hello').encode(str_type('utf-8')), b'hello')
        self.assertEqual(str_type('hello').encode(str_type('utf-8')), b'hello')
        self.assertEqual(str_type('hello').encode(str_type('utf-16-le')),
            b'h\x00e\x00l\x00l\x00o\x00')
        self.assertEqual(str_type('hello').encode(str_type('utf-16-be')),
            b'\x00h\x00e\x00l\x00l\x00o')
        self.assertEqual(str_type('hello').encode(str_type('latin-1')),
            b'hello')
        self.assertEqual(str_type('☃').encode(), b'\xe2\x98\x83')
        for c in range(1024):
            u = chr(c)
            for encoding in (str_type('utf-7'), str_type('utf-8'), str_type
                ('utf-16'), str_type('utf-16-le'), str_type('utf-16-be'),
                str_type('raw_unicode_escape'), str_type('unicode_escape')):
                self.assertEqual(str_type(u.encode(encoding), encoding), u)
        for c in range(256):
            u = chr(c)
            for encoding in (str_type('latin-1'),):
                self.assertEqual(str_type(u.encode(encoding), encoding), u)
        for c in range(128):
            u = chr(c)
            for encoding in (str_type('ascii'),):
                self.assertEqual(str_type(u.encode(encoding), encoding), u)
        with warnings.catch_warnings():
            u = str_type('𐀁𠀂𰀃\U00040004\U00050005')
            for encoding in (str_type('utf-8'), str_type('utf-16'),
                str_type('utf-16-le'), str_type('utf-16-be'), str_type(
                'raw_unicode_escape'), str_type('unicode_escape')):
                self.assertEqual(str_type(u.encode(encoding), encoding), u)
        u = str_type('').join(map(chr, list(range(0, 55296)) + list(range(
            57344, 1114112))))
        for encoding in (str_type('utf-8'),):
            self.assertEqual(str_type(u.encode(encoding), encoding), u)

    def test_codecs_charmap(self):
        s = bytes(range(128))
        for encoding in (str_type('cp037'), str_type('cp1026'), str_type(
            'cp273'), str_type('cp437'), str_type('cp500'), str_type(
            'cp720'), str_type('cp737'), str_type('cp775'), str_type(
            'cp850'), str_type('cp852'), str_type('cp855'), str_type(
            'cp858'), str_type('cp860'), str_type('cp861'), str_type(
            'cp862'), str_type('cp863'), str_type('cp865'), str_type(
            'cp866'), str_type('cp1125'), str_type('iso8859_10'), str_type(
            'iso8859_13'), str_type('iso8859_14'), str_type('iso8859_15'),
            str_type('iso8859_2'), str_type('iso8859_3'), str_type(
            'iso8859_4'), str_type('iso8859_5'), str_type('iso8859_6'),
            str_type('iso8859_7'), str_type('iso8859_9'), str_type('koi8_r'
            ), str_type('koi8_t'), str_type('koi8_u'), str_type('kz1048'),
            str_type('latin_1'), str_type('mac_cyrillic'), str_type(
            'mac_latin2'), str_type('cp1250'), str_type('cp1251'), str_type
            ('cp1252'), str_type('cp1253'), str_type('cp1254'), str_type(
            'cp1255'), str_type('cp1256'), str_type('cp1257'), str_type(
            'cp1258'), str_type('cp856'), str_type('cp857'), str_type(
            'cp864'), str_type('cp869'), str_type('cp874'), str_type(
            'mac_greek'), str_type('mac_iceland'), str_type('mac_roman'),
            str_type('mac_turkish'), str_type('cp1006'), str_type('iso8859_8')
            ):
            self.assertEqual(str_type(s, encoding).encode(encoding), s)
        s = bytes(range(128, 256))
        for encoding in (str_type('cp037'), str_type('cp1026'), str_type(
            'cp273'), str_type('cp437'), str_type('cp500'), str_type(
            'cp720'), str_type('cp737'), str_type('cp775'), str_type(
            'cp850'), str_type('cp852'), str_type('cp855'), str_type(
            'cp858'), str_type('cp860'), str_type('cp861'), str_type(
            'cp862'), str_type('cp863'), str_type('cp865'), str_type(
            'cp866'), str_type('cp1125'), str_type('iso8859_10'), str_type(
            'iso8859_13'), str_type('iso8859_14'), str_type('iso8859_15'),
            str_type('iso8859_2'), str_type('iso8859_4'), str_type(
            'iso8859_5'), str_type('iso8859_9'), str_type('koi8_r'),
            str_type('koi8_u'), str_type('latin_1'), str_type(
            'mac_cyrillic'), str_type('mac_latin2')):
            self.assertEqual(str_type(s, encoding).encode(encoding), s)

    def test_concatenation(self):
        self.assertEqual((str_type("abc") + str_type("def")), str_type("abcdef"))
        self.assertEqual((str_type("abc") + str_type("def")), str_type("abcdef"))
        self.assertEqual((str_type("abc") + str_type("def")), str_type("abcdef"))
        self.assertEqual((str_type("abc") + str_type("def") + str_type("ghi")), str_type("abcdefghi"))
        self.assertEqual((str_type("abc") + str_type("def") + str_type("ghi")), str_type("abcdefghi"))

    def test_ucs4(self):
        x = str_type('\U00100000')
        y = x.encode(str_type('raw-unicode-escape')).decode(str_type(
            'raw-unicode-escape'))
        self.assertEqual(x, y)
        y = b'\\U00100000'
        x = y.decode(str_type('raw-unicode-escape')).encode(str_type(
            'raw-unicode-escape'))
        self.assertEqual(x, y)
        y = b'\\U00010000'
        x = y.decode(str_type('raw-unicode-escape')).encode(str_type(
            'raw-unicode-escape'))
        self.assertEqual(x, y)
        try:
            b'\\U11111111'.decode(str_type('raw-unicode-escape'))
        except UnicodeDecodeError as e:
            self.assertEqual(e.start, 0)
            self.assertEqual(e.end, 10)
        else:
            self.fail(str_type('Should have raised UnicodeDecodeError'))

    # def test_conversion(self):


    #     class StrWithStr(str_type):

    #         def __new__(cls, value):
    #             self = str_type.__new__(cls, str_type(''))
    #             self.value = value
    #             return self

    #         def __str__(self):
    #             return self.value
    #     self.assertTypedEqual(str_type(WithStr(str_type('abc'))), str_type('abc'))
    #     self.assertTypedEqual(str_type(WithStr(StrSubclass(str_type('abc')))),
    #         StrSubclass(str_type('abc')))
    #     self.assertTypedEqual(StrSubclass(WithStr(str_type('abc'))),
    #         StrSubclass(str_type('abc')))
    #     self.assertTypedEqual(StrSubclass(WithStr(StrSubclass(str_type(
    #         'abc')))), StrSubclass(str_type('abc')))
    #     self.assertTypedEqual(StrSubclass(WithStr(OtherStrSubclass(str_type
    #         ('abc')))), StrSubclass(str_type('abc')))
    #     self.assertTypedEqual(str_type(StrWithStr(str_type('abc'))), str_type('abc')
    #         )
    #     self.assertTypedEqual(str_type(StrWithStr(StrSubclass(str_type('abc')))),
    #         StrSubclass(str_type('abc')))
    #     self.assertTypedEqual(StrSubclass(StrWithStr(str_type('abc'))),
    #         StrSubclass(str_type('abc')))
    #     self.assertTypedEqual(StrSubclass(StrWithStr(StrSubclass(str_type(
    #         'abc')))), StrSubclass(str_type('abc')))
    #     self.assertTypedEqual(StrSubclass(StrWithStr(OtherStrSubclass(
    #         str_type('abc')))), StrSubclass(str_type('abc')))
    #     self.assertTypedEqual(str_type(WithRepr(str_type('<abc>'))), str_type(
    #         '<abc>'))
    #     self.assertTypedEqual(str_type(WithRepr(StrSubclass(str_type('<abc>')))),
    #         StrSubclass(str_type('<abc>')))
    #     self.assertTypedEqual(StrSubclass(WithRepr(str_type('<abc>'))),
    #         StrSubclass(str_type('<abc>')))
    #     self.assertTypedEqual(StrSubclass(WithRepr(StrSubclass(str_type(
    #         '<abc>')))), StrSubclass(str_type('<abc>')))
    #     self.assertTypedEqual(StrSubclass(WithRepr(OtherStrSubclass(
    #         str_type('<abc>')))), StrSubclass(str_type('<abc>')))

    def test_unicode_repr(self):


        class s1:

            def __repr__(self):
                return str_type('\\n')
        self.assertEqual(repr(s1()), str_type('\\n'))

    def test_printable_repr(self):
        self.assertEqual(repr(str_type('𐀀')), str_type("'%c'") % (65536,))
        self.assertEqual(repr(str_type('\U00100001')), str_type(
            "'\\U00100001'"))

    @unittest.skipIf(sys.maxsize > 1 << 32 or struct.calcsize(str_type('P')
        ) != 4, str_type('only applies to 32-bit platforms'))
    def test_expandtabs_overflows_gracefully(self):
        self.assertRaises(OverflowError, str_type('t\tt\t').expandtabs, sys
            .maxsize)

    @support.cpython_only
    def test_expandtabs_optimization(self):
        s = str_type('abc')
        self.assertIs(s.expandtabs(), s)

    def test_raiseMemError(self):
        asciifields = str_type('nnb')
        compactfields = asciifields + str_type('nP')
        ascii_struct_size = support.calcobjsize(asciifields)
        compact_struct_size = support.calcobjsize(compactfields)
        for char in (str_type('a'), str_type('é'), str_type('€'), str_type(
            '\U0010ffff')):
            code = ord(char)
            if code < 128:
                char_size = 1
                struct_size = ascii_struct_size
            elif code < 256:
                char_size = 1
                struct_size = compact_struct_size
            elif code < 65536:
                char_size = 2
                struct_size = compact_struct_size
            else:
                char_size = 4
                struct_size = compact_struct_size
            maxlen = (sys.maxsize - struct_size) // char_size
            alloc = lambda : char * maxlen
            with self.subTest(char=char, struct_size=struct_size, char_size
                =char_size):
                self.assertEqual(sys.getsizeof(char * 42), struct_size +
                    char_size * (42 + 1))
                self.assertRaises(MemoryError, alloc)
                self.assertRaises(MemoryError, alloc)

    def test_format_subclass(self):


        class S(str_type):

            def __str__(self):
                return str_type('__str__ overridden')
        s = S(str_type('xxx'))
        self.assertEqual(str_type('%s') % s, str_type('__str__ overridden'))
        self.assertEqual(str_type('{}').format(s), str_type(
            '__str__ overridden'))

    def test_subclass_add(self):


        class S(str_type):

            def __add__(self, o):
                return str_type('3')
        self.assertEqual(S(str_type('4')) + S(str_type('5')), str_type('3'))


        class S(str_type):

            def __iadd__(self, o):
                return str_type('3')
        s = S(str_type('1'))
        s += str_type('4')
        self.assertEqual(s, str_type('3'))

    def test_getnewargs(self):
        text = str_type('abc')
        args = text.__getnewargs__()
        self.assertIsNot(args[0], text)
        self.assertEqual(args[0], text)
        self.assertEqual(len(args), 1)

    def test_compare(self):
        N = 10
        ascii = str_type('a') * N
        ascii2 = str_type('z') * N
        latin = str_type('\x80') * N
        latin2 = str_type('ÿ') * N
        bmp = str_type('Ā') * N
        bmp2 = str_type('\uffff') * N
        astral = str_type('\U00100000') * N
        astral2 = str_type('\U0010ffff') * N
        strings = ascii, ascii2, latin, latin2, bmp, bmp2, astral, astral2
        for text1, text2 in itertools.combinations(strings, 2):
            equal = text1 is text2
            self.assertEqual(text1 == text2, equal)
            self.assertEqual(text1 != text2, not equal)
            if equal:
                self.assertTrue(text1 <= text2)
                self.assertTrue(text1 >= text2)
                copy1 = duplicate_string(text1)
                copy2 = duplicate_string(text2)
                self.assertIsNot(copy1, copy2)
                self.assertTrue(copy1 == copy2)
                self.assertFalse(copy1 != copy2)
                self.assertTrue(copy1 <= copy2)
                self.assertTrue(copy2 >= copy2)
        self.assertTrue(ascii < ascii2)
        self.assertTrue(ascii < latin)
        self.assertTrue(ascii < bmp)
        self.assertTrue(ascii < astral)
        self.assertFalse(ascii >= ascii2)
        self.assertFalse(ascii >= latin)
        self.assertFalse(ascii >= bmp)
        self.assertFalse(ascii >= astral)
        self.assertFalse(latin < ascii)
        self.assertTrue(latin < latin2)
        self.assertTrue(latin < bmp)
        self.assertTrue(latin < astral)
        self.assertTrue(latin >= ascii)
        self.assertFalse(latin >= latin2)
        self.assertFalse(latin >= bmp)
        self.assertFalse(latin >= astral)
        self.assertFalse(bmp < ascii)
        self.assertFalse(bmp < latin)
        self.assertTrue(bmp < bmp2)
        self.assertTrue(bmp < astral)
        self.assertTrue(bmp >= ascii)
        self.assertTrue(bmp >= latin)
        self.assertFalse(bmp >= bmp2)
        self.assertFalse(bmp >= astral)
        self.assertFalse(astral < ascii)
        self.assertFalse(astral < latin)
        self.assertFalse(astral < bmp2)
        self.assertTrue(astral < astral2)
        self.assertTrue(astral >= ascii)
        self.assertTrue(astral >= latin)
        self.assertTrue(astral >= bmp2)
        self.assertFalse(astral >= astral2)

    def test_free_after_iterating(self):
        support.check_free_after_iterating(self, iter, str_type)
        support.check_free_after_iterating(self, reversed, str_type)

    def test_check_encoding_errors(self):
        encodings = str_type('ascii'), str_type('utf8'), str_type('latin1')
        invalid = str_type('Boom, Shaka Laka, Boom!')
        code = textwrap.dedent(
            f"""
            import sys
            encodings = {encodings!r}
            str_type = str

            for data in (b'', b'short string'):
                try:
                    str_type(data, encoding={invalid!r})
                except LookupError:
                    pass
                else:
                    sys.exit(21)

                try:
                    str_type(data, errors={invalid!r})
                except LookupError:
                    pass
                else:
                    sys.exit(22)

                for encoding in encodings:
                    try:
                        str_type(data, encoding, errors={invalid!r})
                    except LookupError:
                        pass
                    else:
                        sys.exit(22)

            for data in ('', 'short string'):
                try:
                    data.encode(encoding={invalid!r})
                except LookupError:
                    pass
                else:
                    sys.exit(23)

                try:
                    data.encode(errors={invalid!r})
                except LookupError:
                    pass
                else:
                    sys.exit(24)

                for encoding in encodings:
                    try:
                        data.encode(encoding, errors={invalid!r})
                    except LookupError:
                        pass
                    else:
                        sys.exit(24)

            sys.exit(10)
        """
            )
        proc = assert_python_failure(str_type('-X'), str_type('dev'),
            str_type('-c'), code)
        self.assertEqual(proc.rc, 10, proc)

    def test_str_invalid_call(self):
        with self.assertRaisesRegex(TypeError, str_type(
            'str expected at most 3 arguments, got 4')):
            str_type(str_type('too'), str_type('many'), str_type('argu'),
                str_type('ments'))
        with self.assertRaisesRegex(TypeError, str_type(
            'str expected at most 3 arguments, got 4')):
            str_type(1, str_type(''), str_type(''), 1)
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) got an unexpected keyword argument 'test'")):
            str_type(test=1)
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'encoding' must be str, not int")):
            str_type(1, 1)
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'encoding' must be str, not int")):
            str_type(1, encoding=1)
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'encoding' must be str, not bytes")):
            str_type(b'x', b'ascii')
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'encoding' must be str, not bytes")):
            str_type(b'x', encoding=b'ascii')
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'encoding' must be str, not int")):
            str_type(1, 1, 1)
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'errors' must be str, not int")):
            str_type(1, errors=1)
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'errors' must be str, not int")):
            str_type(1, str_type(''), errors=1)
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'errors' must be str, not bytes")):
            str_type(b'x', str_type('ascii'), b'strict')
        with self.assertRaisesRegex(TypeError, str_type(
            "str\\(\\) argument 'errors' must be str, not bytes")):
            str_type(b'x', str_type('ascii'), errors=b'strict')
        with self.assertRaisesRegex(TypeError, str_type(
            "argument for str\\(\\) given by name \\('encoding'\\) and position \\(2\\)"
            )):
            str_type(b'x', str_type('utf-8'), encoding=str_type('ascii'))
        with self.assertRaisesRegex(TypeError, str_type(
            'str\\(\\) takes at most 3 arguments \\(4 given\\)')):
            str_type(b'x', str_type('utf-8'), str_type('ignore'), encoding=
                str_type('ascii'))
        with self.assertRaisesRegex(TypeError, str_type(
            'str\\(\\) takes at most 3 arguments \\(4 given\\)')):
            str_type(b'x', str_type('utf-8'), str_type('strict'), errors=
                str_type('ignore'))


class StringModuleTest(unittest.TestCase):

    def test_formatter_parser(self):

        def parse(format):
            return list(_string.formatter_parser(format))
        formatter = parse(str_type(
            'prefix {2!s}xxx{0:^+10.3f}{obj.attr!s} {z[0]!s:10}'))
        self.assertEqual(formatter, [(str_type('prefix '), str_type('2'),
            str_type(''), str_type('s')), (str_type('xxx'), str_type('0'),
            str_type('^+10.3f'), None), (str_type(''), str_type('obj.attr'),
            str_type(''), str_type('s')), (str_type(' '), str_type('z[0]'),
            str_type('10'), str_type('s'))])
        formatter = parse(str_type('prefix {} suffix'))
        self.assertEqual(formatter, [(str_type('prefix '), str_type(''),
            str_type(''), None), (str_type(' suffix'), None, None, None)])
        formatter = parse(str_type('str_type'))
        self.assertEqual(formatter, [(str_type('str_type'), None, None, None)])
        formatter = parse(str_type(''))
        self.assertEqual(formatter, [])
        formatter = parse(str_type('{0}'))
        self.assertEqual(formatter, [(str_type(''), str_type('0'), str_type
            (''), None)])
        self.assertRaises(TypeError, _string.formatter_parser, 1)

    def test_formatter_field_name_split(self):

        def split(name):
            items = list(_string.formatter_field_name_split(name))
            items[1] = list(items[1])
            return items
        self.assertEqual(split(str_type('obj')), [str_type('obj'), []])
        self.assertEqual(split(str_type('obj.arg')), [str_type('obj'), [(
            True, str_type('arg'))]])
        self.assertEqual(split(str_type('obj[key]')), [str_type('obj'), [(
            False, str_type('key'))]])
        self.assertEqual(split(str_type('obj.arg[key1][key2]')), [str_type(
            'obj'), [(True, str_type('arg')), (False, str_type('key1')), (
            False, str_type('key2'))]])
        self.assertRaises(TypeError, _string.formatter_field_name_split, 1)

    # def test_str_subclass_attr(self):
    #     name = StrSubclass(str_type('name'))
    #     name2 = StrSubclass(str_type('name2'))


    #     class Bag:
    #         pass
    #     o = Bag()
    #     with self.assertRaises(AttributeError):
    #         delattr(o, name)
    #     setattr(o, name, 1)
    #     self.assertEqual(o.name, 1)
    #     o.name = 2
    #     self.assertEqual(list(o.__dict__), [name])
    #     with self.assertRaises(AttributeError):
    #         delattr(o, name2)
    #     with self.assertRaises(AttributeError):
    #         del o.name2
    #     setattr(o, name2, 3)
    #     self.assertEqual(o.name2, 3)
    #     o.name2 = 4
    #     self.assertEqual(list(o.__dict__), [name, name2])


if __name__ == str_type('__main__'):
    unittest.main()
