"""
Common tests shared by test_unicode, test_userstring and test_bytes.
"""
import unittest, string, sys, struct
from test import support
from test.support import import_helper
from collections import UserList
import random


str_type = str


class Sequence:

    def __init__(self, seq=str_type('wxyz')):
        self.seq = seq

    def __len__(self):
        return len(self.seq)

    def __getitem__(self, i):
        return self.seq[i]


class BaseTest:
    type2test = None
    contains_bytes = False

    def fixtype(self, obj):
        if isinstance(obj, str_type):
            return self.__class__.type2test(obj)
        elif isinstance(obj, list):
            return [self.fixtype(x) for x in obj]
        elif isinstance(obj, tuple):
            return tuple([self.fixtype(x) for x in obj])
        elif isinstance(obj, dict):
            return dict([(self.fixtype(key), self.fixtype(value)) for key,
                value in obj.items()])
        else:
            return obj

    def test_fixtype(self):
        self.assertIs(type(self.fixtype(str_type('123'))), self.type2test)

    def checkequal(self, result, obj, methodname, *args, **kwargs):
        result = self.fixtype(result)
        obj = self.fixtype(obj)
        args = self.fixtype(args)
        kwargs = {k: self.fixtype(v) for k, v in kwargs.items()}
        realresult = getattr(obj, methodname)(*args, **kwargs)
        self.assertEqual(result, realresult)
        if obj is realresult:
            try:


                class subtype(self.__class__.type2test):
                    pass
            except TypeError:
                pass
            else:
                obj = subtype(obj)
                realresult = getattr(obj, methodname)(*args)
                self.assertIsNot(obj, realresult)

    def checkraises(self, exc, obj, methodname, *args, expected_msg=None):
        obj = self.fixtype(obj)
        args = self.fixtype(args)
        with self.assertRaises(exc) as cm:
            getattr(obj, methodname)(*args)
        self.assertNotEqual(str_type(cm.exception), str_type(''))
        if expected_msg is not None:
            self.assertEqual(str_type(cm.exception), expected_msg)

    def checkcall(self, obj, methodname, *args):
        obj = self.fixtype(obj)
        args = self.fixtype(args)
        getattr(obj, methodname)(*args)

    def test_count(self):
        self.checkequal(3, str_type('aaa'), str_type('count'), str_type('a'))
        self.checkequal(0, str_type('aaa'), str_type('count'), str_type('b'))
        self.checkequal(3, str_type('aaa'), str_type('count'), str_type('a'))
        self.checkequal(0, str_type('aaa'), str_type('count'), str_type('b'))
        self.checkequal(3, str_type('aaa'), str_type('count'), str_type('a'))
        self.checkequal(0, str_type('aaa'), str_type('count'), str_type('b'))
        self.checkequal(0, str_type('aaa'), str_type('count'), str_type('b'))
        self.checkequal(2, str_type('aaa'), str_type('count'), str_type('a'), 1
            )
        self.checkequal(0, str_type('aaa'), str_type('count'), str_type('a'
            ), 10)
        self.checkequal(1, str_type('aaa'), str_type('count'), str_type('a'
            ), -1)
        self.checkequal(3, str_type('aaa'), str_type('count'), str_type('a'
            ), -10)
        self.checkequal(1, str_type('aaa'), str_type('count'), str_type('a'
            ), 0, 1)
        self.checkequal(3, str_type('aaa'), str_type('count'), str_type('a'
            ), 0, 10)
        self.checkequal(2, str_type('aaa'), str_type('count'), str_type('a'
            ), 0, -1)
        self.checkequal(0, str_type('aaa'), str_type('count'), str_type('a'
            ), 0, -10)
        self.checkequal(3, str_type('aaa'), str_type('count'), str_type(''), 1)
        self.checkequal(1, str_type('aaa'), str_type('count'), str_type(''), 3)
        self.checkequal(0, str_type('aaa'), str_type('count'), str_type(''), 10
            )
        self.checkequal(2, str_type('aaa'), str_type('count'), str_type(''), -1
            )
        self.checkequal(4, str_type('aaa'), str_type('count'), str_type(''),
            -10)
        self.checkequal(1, str_type(''), str_type('count'), str_type(''))
        self.checkequal(0, str_type(''), str_type('count'), str_type(''), 1, 1)
        self.checkequal(0, str_type(''), str_type('count'), str_type(''),
            sys.maxsize, 0)
        self.checkequal(0, str_type(''), str_type('count'), str_type('xx'))
        self.checkequal(0, str_type(''), str_type('count'), str_type('xx'),
            1, 1)
        self.checkequal(0, str_type(''), str_type('count'), str_type('xx'),
            sys.maxsize, 0)
        self.checkraises(TypeError, str_type('hello'), str_type('count'))
        if self.contains_bytes:
            self.checkequal(0, str_type('hello'), str_type('count'), 42)
        else:
            self.checkraises(TypeError, str_type('hello'), str_type('count'
                ), 42)
        charset = [str_type(''), str_type('a'), str_type('b')]
        digits = 7
        base = len(charset)
        teststrings = set()
        for i in range(base ** digits):
            entry = []
            for j in range(digits):
                i, m = divmod(i, base)
                entry.append(charset[m])
            teststrings.add(str_type('').join(entry))
        teststrings = [self.fixtype(ts) for ts in teststrings]
        for i in teststrings:
            n = len(i)
            for j in teststrings:
                r1 = i.count(j)
                if j:
                    r2, rem = divmod(n - len(i.replace(j, self.fixtype(
                        str_type('')))), len(j))
                else:
                    r2, rem = len(i) + 1, 0
                if rem or r1 != r2:
                    self.assertEqual(rem, 0, str_type('%s != 0 for %s') % (
                        rem, i))
                    self.assertEqual(r1, r2, str_type('%s != %s for %s') %
                        (r1, r2, i))

    def test_count_keyword(self):
        self.assertEqual(str_type('aa').replace(str_type('a'), str_type('b'
            ), 0), str_type('aa').replace(str_type('a'), str_type('b'),
            count=0))
        self.assertEqual(str_type('aa').replace(str_type('a'), str_type('b'
            ), 1), str_type('aa').replace(str_type('a'), str_type('b'),
            count=1))
        self.assertEqual(str_type('aa').replace(str_type('a'), str_type('b'
            ), 2), str_type('aa').replace(str_type('a'), str_type('b'),
            count=2))
        self.assertEqual(str_type('aa').replace(str_type('a'), str_type('b'
            ), 3), str_type('aa').replace(str_type('a'), str_type('b'),
            count=3))

    def test_find(self):
        self.checkequal(0, str_type('abcdefghiabc'), str_type('find'),
            str_type('abc'))
        self.checkequal(9, str_type('abcdefghiabc'), str_type('find'),
            str_type('abc'), 1)
        self.checkequal(-1, str_type('abcdefghiabc'), str_type('find'),
            str_type('def'), 4)
        self.checkequal(0, str_type('abc'), str_type('find'), str_type(''), 0)
        self.checkequal(3, str_type('abc'), str_type('find'), str_type(''), 3)
        self.checkequal(-1, str_type('abc'), str_type('find'), str_type(''), 4)
        self.checkequal(2, str_type('rrarrrrrrrrra'), str_type('find'),
            str_type('a'))
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('find'),
            str_type('a'), 4)
        self.checkequal(-1, str_type('rrarrrrrrrrra'), str_type('find'),
            str_type('a'), 4, 6)
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('find'),
            str_type('a'), 4, None)
        self.checkequal(2, str_type('rrarrrrrrrrra'), str_type('find'),
            str_type('a'), None, 6)
        self.checkraises(TypeError, str_type('hello'), str_type('find'))
        if self.contains_bytes:
            self.checkequal(-1, str_type('hello'), str_type('find'), 42)
        else:
            self.checkraises(TypeError, str_type('hello'), str_type('find'), 42
                )
        self.checkequal(0, str_type(''), str_type('find'), str_type(''))
        self.checkequal(-1, str_type(''), str_type('find'), str_type(''), 1, 1)
        self.checkequal(-1, str_type(''), str_type('find'), str_type(''),
            sys.maxsize, 0)
        self.checkequal(-1, str_type(''), str_type('find'), str_type('xx'))
        self.checkequal(-1, str_type(''), str_type('find'), str_type('xx'),
            1, 1)
        self.checkequal(-1, str_type(''), str_type('find'), str_type('xx'),
            sys.maxsize, 0)
        self.checkequal(-1, str_type('ab'), str_type('find'), str_type(
            'xxx'), sys.maxsize + 1, 0)
        charset = [str_type(''), str_type('a'), str_type('b'), str_type('c')]
        digits = 5
        base = len(charset)
        teststrings = set()
        for i in range(base ** digits):
            entry = []
            for j in range(digits):
                i, m = divmod(i, base)
                entry.append(charset[m])
            teststrings.add(str_type('').join(entry))
        teststrings = [self.fixtype(ts) for ts in teststrings]
        for i in teststrings:
            for j in teststrings:
                loc = i.find(j)
                r1 = loc != -1
                r2 = j in i
                self.assertEqual(r1, r2)
                if loc != -1:
                    self.assertEqual(i[loc:loc + len(j)], j)

    def test_rfind(self):
        self.checkequal(9, str_type('abcdefghiabc'), str_type('rfind'),
            str_type('abc'))
        self.checkequal(12, str_type('abcdefghiabc'), str_type('rfind'),
            str_type(''))
        self.checkequal(0, str_type('abcdefghiabc'), str_type('rfind'),
            str_type('abcd'))
        self.checkequal(-1, str_type('abcdefghiabc'), str_type('rfind'),
            str_type('abcz'))
        self.checkequal(3, str_type('abc'), str_type('rfind'), str_type(''), 0)
        self.checkequal(3, str_type('abc'), str_type('rfind'), str_type(''), 3)
        self.checkequal(-1, str_type('abc'), str_type('rfind'), str_type(''), 4
            )
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('rfind'),
            str_type('a'))
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('rfind'),
            str_type('a'), 4)
        self.checkequal(-1, str_type('rrarrrrrrrrra'), str_type('rfind'),
            str_type('a'), 4, 6)
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('rfind'),
            str_type('a'), 4, None)
        self.checkequal(2, str_type('rrarrrrrrrrra'), str_type('rfind'),
            str_type('a'), None, 6)
        self.checkraises(TypeError, str_type('hello'), str_type('rfind'))
        if self.contains_bytes:
            self.checkequal(-1, str_type('hello'), str_type('rfind'), 42)
        else:
            self.checkraises(TypeError, str_type('hello'), str_type('rfind'
                ), 42)
        charset = [str_type(''), str_type('a'), str_type('b'), str_type('c')]
        digits = 5
        base = len(charset)
        teststrings = set()
        for i in range(base ** digits):
            entry = []
            for j in range(digits):
                i, m = divmod(i, base)
                entry.append(charset[m])
            teststrings.add(str_type('').join(entry))
        teststrings = [self.fixtype(ts) for ts in teststrings]
        for i in teststrings:
            for j in teststrings:
                loc = i.rfind(j)
                r1 = loc != -1
                r2 = j in i
                self.assertEqual(r1, r2)
                if loc != -1:
                    self.assertEqual(i[loc:loc + len(j)], j)
        self.checkequal(-1, str_type('ab'), str_type('rfind'), str_type(
            'xxx'), sys.maxsize + 1, 0)
        self.checkequal(0, str_type('<......м...'), str_type('rfind'),
            str_type('<'))

    def test_index(self):
        self.checkequal(0, str_type('abcdefghiabc'), str_type('index'),
            str_type(''))
        self.checkequal(3, str_type('abcdefghiabc'), str_type('index'),
            str_type('def'))
        self.checkequal(0, str_type('abcdefghiabc'), str_type('index'),
            str_type('abc'))
        self.checkequal(9, str_type('abcdefghiabc'), str_type('index'),
            str_type('abc'), 1)
        self.checkraises(ValueError, str_type('abcdefghiabc'), str_type(
            'index'), str_type('hib'))
        self.checkraises(ValueError, str_type('abcdefghiab'), str_type(
            'index'), str_type('abc'), 1)
        self.checkraises(ValueError, str_type('abcdefghi'), str_type(
            'index'), str_type('ghi'), 8)
        self.checkraises(ValueError, str_type('abcdefghi'), str_type(
            'index'), str_type('ghi'), -1)
        self.checkequal(2, str_type('rrarrrrrrrrra'), str_type('index'),
            str_type('a'))
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('index'),
            str_type('a'), 4)
        self.checkraises(ValueError, str_type('rrarrrrrrrrra'), str_type(
            'index'), str_type('a'), 4, 6)
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('index'),
            str_type('a'), 4, None)
        self.checkequal(2, str_type('rrarrrrrrrrra'), str_type('index'),
            str_type('a'), None, 6)
        self.checkraises(TypeError, str_type('hello'), str_type('index'))
        if self.contains_bytes:
            self.checkraises(ValueError, str_type('hello'), str_type(
                'index'), 42)
        else:
            self.checkraises(TypeError, str_type('hello'), str_type('index'
                ), 42)

    def test_rindex(self):
        self.checkequal(12, str_type('abcdefghiabc'), str_type('rindex'),
            str_type(''))
        self.checkequal(3, str_type('abcdefghiabc'), str_type('rindex'),
            str_type('def'))
        self.checkequal(9, str_type('abcdefghiabc'), str_type('rindex'),
            str_type('abc'))
        self.checkequal(0, str_type('abcdefghiabc'), str_type('rindex'),
            str_type('abc'), 0, -1)
        self.checkraises(ValueError, str_type('abcdefghiabc'), str_type(
            'rindex'), str_type('hib'))
        self.checkraises(ValueError, str_type('defghiabc'), str_type(
            'rindex'), str_type('def'), 1)
        self.checkraises(ValueError, str_type('defghiabc'), str_type(
            'rindex'), str_type('abc'), 0, -1)
        self.checkraises(ValueError, str_type('abcdefghi'), str_type(
            'rindex'), str_type('ghi'), 0, 8)
        self.checkraises(ValueError, str_type('abcdefghi'), str_type(
            'rindex'), str_type('ghi'), 0, -1)
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('rindex'),
            str_type('a'))
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('rindex'),
            str_type('a'), 4)
        self.checkraises(ValueError, str_type('rrarrrrrrrrra'), str_type(
            'rindex'), str_type('a'), 4, 6)
        self.checkequal(12, str_type('rrarrrrrrrrra'), str_type('rindex'),
            str_type('a'), 4, None)
        self.checkequal(2, str_type('rrarrrrrrrrra'), str_type('rindex'),
            str_type('a'), None, 6)
        self.checkraises(TypeError, str_type('hello'), str_type('rindex'))
        if self.contains_bytes:
            self.checkraises(ValueError, str_type('hello'), str_type(
                'rindex'), 42)
        else:
            self.checkraises(TypeError, str_type('hello'), str_type(
                'rindex'), 42)

    def test_find_periodic_pattern(self):
        str_type('Cover the special path for periodic patterns.')

        def reference_find(p, s):
            for i in range(len(s)):
                if s.startswith(p, i):
                    return i
            if p == str_type('') and s == str_type(''):
                return 0
            return -1

        def check_pattern(rr):
            choices = random.choices
            p0 = str_type('').join(choices(str_type('abcde'), k=rr(10))) * rr(
                10, 20)
            p = p0[:len(p0) - rr(10)]
            left = str_type('').join(choices(str_type('abcdef'), k=rr(2000)))
            right = str_type('').join(choices(str_type('abcdef'), k=rr(2000)))
            text = left + p + right
            with self.subTest(p=p, text=text):
                self.checkequal(reference_find(p, text), text, str_type(
                    'find'), p)
        rr = random.randrange
        for _ in range(1000):
            check_pattern(rr)
        check_pattern(lambda *args: 0)

    def test_find_many_lengths(self):
        haystack_repeats = [(a * 10 ** e) for e in range(6) for a in (1, 2, 5)]
        haystacks = [(n, self.fixtype(str_type('abcab') * n + str_type('da'
            ))) for n in haystack_repeats]
        needle_repeats = [(a * 10 ** e) for e in range(6) for a in (1, 3)]
        needles = [(m, self.fixtype(str_type('abcab') * m + str_type('da'))
            ) for m in needle_repeats]
        for n, haystack1 in haystacks:
            haystack2 = haystack1[:-1]
            for m, needle in needles:
                answer1 = 5 * (n - m) if m <= n else -1
                self.assertEqual(haystack1.find(needle), answer1, msg=(n, m))
                self.assertEqual(haystack2.find(needle), -1, msg=(n, m))

    def test_adaptive_find(self):
        for N in (1000, 10000, 100000, 1000000):
            A, B = str_type('a') * N, str_type('b') * N
            haystack = A + A + B + A + A
            needle = A + B + B + A
            self.checkequal(-1, haystack, str_type('find'), needle)
            self.checkequal(0, haystack, str_type('count'), needle)
            self.checkequal(len(haystack), haystack + needle, str_type(
                'find'), needle)
            self.checkequal(1, haystack + needle, str_type('count'), needle)

    def test_find_with_memory(self):
        for N in (1000, 3000, 10000, 30000):
            needle = str_type('ab') * N
            haystack = (str_type('ab') * (N - 1) + str_type('b')) * 2
            self.checkequal(-1, haystack, str_type('find'), needle)
            self.checkequal(0, haystack, str_type('count'), needle)
            self.checkequal(len(haystack), haystack + needle, str_type(
                'find'), needle)
            self.checkequal(1, haystack + needle, str_type('count'), needle)

    def test_find_shift_table_overflow(self):
        str_type('When the table of 8-bit shifts overflows.')
        N = 2 ** 8 + 100
        pattern1 = str_type('a') * N + str_type('b') + str_type('a') * N
        text1 = str_type('babbaa') * N + pattern1
        self.checkequal(len(text1) - len(pattern1), text1, str_type('find'),
            pattern1)
        pattern2 = str_type('ddd') + str_type('abc') * N + str_type('eee')
        text2 = pattern2[:-1] + str_type('ddeede'
            ) * 2 * N + pattern2 + str_type('de') * N
        self.checkequal(len(text2) - N * len(str_type('de')) - len(pattern2
            ), text2, str_type('find'), pattern2)

    def test_lower(self):
        self.checkequal(str_type('hello'), str_type('HeLLo'), str_type('lower')
            )
        self.checkequal(str_type('hello'), str_type('hello'), str_type('lower')
            )
        self.checkraises(TypeError, str_type('hello'), str_type('lower'), 42)

    def test_upper(self):
        self.checkequal(str_type('HELLO'), str_type('HeLLo'), str_type('upper')
            )
        self.checkequal(str_type('HELLO'), str_type('HELLO'), str_type('upper')
            )
        self.checkraises(TypeError, str_type('hello'), str_type('upper'), 42)

    def test_expandtabs(self):
        self.checkequal(str_type('abc\rab      def\ng       hi'), str_type(
            'abc\rab\tdef\ng\thi'), str_type('expandtabs'))
        self.checkequal(str_type('abc\rab      def\ng       hi'), str_type(
            'abc\rab\tdef\ng\thi'), str_type('expandtabs'), 8)
        self.checkequal(str_type('abc\rab  def\ng   hi'), str_type(
            'abc\rab\tdef\ng\thi'), str_type('expandtabs'), 4)
        self.checkequal(str_type('abc\r\nab      def\ng       hi'),
            str_type('abc\r\nab\tdef\ng\thi'), str_type('expandtabs'))
        self.checkequal(str_type('abc\r\nab      def\ng       hi'),
            str_type('abc\r\nab\tdef\ng\thi'), str_type('expandtabs'), 8)
        self.checkequal(str_type('abc\r\nab  def\ng   hi'), str_type(
            'abc\r\nab\tdef\ng\thi'), str_type('expandtabs'), 4)
        self.checkequal(str_type('abc\r\nab\r\ndef\ng\r\nhi'), str_type(
            'abc\r\nab\r\ndef\ng\r\nhi'), str_type('expandtabs'), 4)
        self.checkequal(str_type('abc\rab      def\ng       hi'), str_type(
            'abc\rab\tdef\ng\thi'), str_type('expandtabs'), tabsize=8)
        self.checkequal(str_type('abc\rab  def\ng   hi'), str_type(
            'abc\rab\tdef\ng\thi'), str_type('expandtabs'), tabsize=4)
        self.checkequal(str_type('  a\n b'), str_type(' \ta\n\tb'),
            str_type('expandtabs'), 1)
        self.checkraises(TypeError, str_type('hello'), str_type(
            'expandtabs'), 42, 42)
        if sys.maxsize < 1 << 32 and struct.calcsize(str_type('P')) == 4:
            self.checkraises(OverflowError, str_type('\ta\n\tb'), str_type(
                'expandtabs'), sys.maxsize)

    def test_split(self):
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('split'),
            str_type('|'))
        self.checkequal([str_type('a|b|c|d')], str_type('a|b|c|d'),
            str_type('split'), str_type('|'), 0)
        self.checkequal([str_type('a'), str_type('b|c|d')], str_type(
            'a|b|c|d'), str_type('split'), str_type('|'), 1)
        self.checkequal([str_type('a'), str_type('b'), str_type('c|d')],
            str_type('a|b|c|d'), str_type('split'), str_type('|'), 2)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('split'),
            str_type('|'), 3)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('split'),
            str_type('|'), 4)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('split'),
            str_type('|'), sys.maxsize - 2)
        self.checkequal([str_type('a|b|c|d')], str_type('a|b|c|d'),
            str_type('split'), str_type('|'), 0)
        self.checkequal([str_type('a'), str_type(''), str_type('b||c||d')],
            str_type('a||b||c||d'), str_type('split'), str_type('|'), 2)
        self.checkequal([str_type('abcd')], str_type('abcd'), str_type(
            'split'), str_type('|'))
        self.checkequal([str_type('')], str_type(''), str_type('split'),
            str_type('|'))
        self.checkequal([str_type('endcase '), str_type('')], str_type(
            'endcase |'), str_type('split'), str_type('|'))
        self.checkequal([str_type(''), str_type(' startcase')], str_type(
            '| startcase'), str_type('split'), str_type('|'))
        self.checkequal([str_type(''), str_type('bothcase'), str_type('')],
            str_type('|bothcase|'), str_type('split'), str_type('|'))
        self.checkequal([str_type('a'), str_type(''), str_type(
            'b\x00c\x00d')], str_type('a\x00\x00b\x00c\x00d'), str_type(
            'split'), str_type('\x00'), 2)
        self.checkequal([str_type('a')] * 20, (str_type('a|') * 20)[:-1],
            str_type('split'), str_type('|'))
        self.checkequal([str_type('a')] * 15 + [str_type('a|a|a|a|a')], (
            str_type('a|') * 20)[:-1], str_type('split'), str_type('|'), 15)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a//b//c//d'), str_type('split'),
            str_type('//'))
        self.checkequal([str_type('a'), str_type('b//c//d')], str_type(
            'a//b//c//d'), str_type('split'), str_type('//'), 1)
        self.checkequal([str_type('a'), str_type('b'), str_type('c//d')],
            str_type('a//b//c//d'), str_type('split'), str_type('//'), 2)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a//b//c//d'), str_type('split'),
            str_type('//'), 3)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a//b//c//d'), str_type('split'),
            str_type('//'), 4)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a//b//c//d'), str_type('split'),
            str_type('//'), sys.maxsize - 10)
        self.checkequal([str_type('a//b//c//d')], str_type('a//b//c//d'),
            str_type('split'), str_type('//'), 0)
        self.checkequal([str_type('a'), str_type(''), str_type(
            'b////c////d')], str_type('a////b////c////d'), str_type('split'
            ), str_type('//'), 2)
        self.checkequal([str_type('endcase '), str_type('')], str_type(
            'endcase test'), str_type('split'), str_type('test'))
        self.checkequal([str_type(''), str_type(' begincase')], str_type(
            'test begincase'), str_type('split'), str_type('test'))
        self.checkequal([str_type(''), str_type(' bothcase '), str_type('')
            ], str_type('test bothcase test'), str_type('split'), str_type(
            'test'))
        self.checkequal([str_type('a'), str_type('bc')], str_type('abbbc'),
            str_type('split'), str_type('bb'))
        self.checkequal([str_type(''), str_type('')], str_type('aaa'),
            str_type('split'), str_type('aaa'))
        self.checkequal([str_type('aaa')], str_type('aaa'), str_type(
            'split'), str_type('aaa'), 0)
        self.checkequal([str_type('ab'), str_type('ab')], str_type('abbaab'
            ), str_type('split'), str_type('ba'))
        self.checkequal([str_type('aaaa')], str_type('aaaa'), str_type(
            'split'), str_type('aab'))
        self.checkequal([str_type('')], str_type(''), str_type('split'),
            str_type('aaa'))
        self.checkequal([str_type('aa')], str_type('aa'), str_type('split'),
            str_type('aaa'))
        self.checkequal([str_type('A'), str_type('bobb')], str_type(
            'Abbobbbobb'), str_type('split'), str_type('bbobb'))
        self.checkequal([str_type('A'), str_type('B'), str_type('')],
            str_type('AbbobbBbbobb'), str_type('split'), str_type('bbobb'))
        self.checkequal([str_type('a')] * 20, (str_type('aBLAH') * 20)[:-4],
            str_type('split'), str_type('BLAH'))
        self.checkequal([str_type('a')] * 20, (str_type('aBLAH') * 20)[:-4],
            str_type('split'), str_type('BLAH'), 19)
        self.checkequal([str_type('a')] * 18 + [str_type('aBLAHa')], (
            str_type('aBLAH') * 20)[:-4], str_type('split'), str_type(
            'BLAH'), 18)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('split'), sep=
            str_type('|'))
        self.checkequal([str_type('a'), str_type('b|c|d')], str_type(
            'a|b|c|d'), str_type('split'), str_type('|'), maxsplit=1)
        self.checkequal([str_type('a'), str_type('b|c|d')], str_type(
            'a|b|c|d'), str_type('split'), sep=str_type('|'), maxsplit=1)
        self.checkequal([str_type('a'), str_type('b|c|d')], str_type(
            'a|b|c|d'), str_type('split'), maxsplit=1, sep=str_type('|'))
        self.checkequal([str_type('a'), str_type('b c d')], str_type(
            'a b c d'), str_type('split'), maxsplit=1)
        self.checkraises(TypeError, str_type('hello'), str_type('split'), 
            42, 42, 42)
        self.checkraises(ValueError, str_type('hello'), str_type('split'),
            str_type(''))
        self.checkraises(ValueError, str_type('hello'), str_type('split'),
            str_type(''), 0)

    def test_rsplit(self):
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d'), str_type('rsplit'))
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a  b  c d'), str_type('rsplit'))
        self.checkequal([], str_type(''), str_type('rsplit'))
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('rsplit'),
            str_type('|'))
        self.checkequal([str_type('a|b|c'), str_type('d')], str_type(
            'a|b|c|d'), str_type('rsplit'), str_type('|'), 1)
        self.checkequal([str_type('a|b'), str_type('c'), str_type('d')],
            str_type('a|b|c|d'), str_type('rsplit'), str_type('|'), 2)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('rsplit'),
            str_type('|'), 3)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('rsplit'),
            str_type('|'), 4)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('rsplit'),
            str_type('|'), sys.maxsize - 100)
        self.checkequal([str_type('a|b|c|d')], str_type('a|b|c|d'),
            str_type('rsplit'), str_type('|'), 0)
        self.checkequal([str_type('a||b||c'), str_type(''), str_type('d')],
            str_type('a||b||c||d'), str_type('rsplit'), str_type('|'), 2)
        self.checkequal([str_type('abcd')], str_type('abcd'), str_type(
            'rsplit'), str_type('|'))
        self.checkequal([str_type('')], str_type(''), str_type('rsplit'),
            str_type('|'))
        self.checkequal([str_type(''), str_type(' begincase')], str_type(
            '| begincase'), str_type('rsplit'), str_type('|'))
        self.checkequal([str_type('endcase '), str_type('')], str_type(
            'endcase |'), str_type('rsplit'), str_type('|'))
        self.checkequal([str_type(''), str_type('bothcase'), str_type('')],
            str_type('|bothcase|'), str_type('rsplit'), str_type('|'))
        self.checkequal([str_type('a\x00\x00b'), str_type('c'), str_type(
            'd')], str_type('a\x00\x00b\x00c\x00d'), str_type('rsplit'),
            str_type('\x00'), 2)
        self.checkequal([str_type('a')] * 20, (str_type('a|') * 20)[:-1],
            str_type('rsplit'), str_type('|'))
        self.checkequal([str_type('a|a|a|a|a')] + [str_type('a')] * 15, (
            str_type('a|') * 20)[:-1], str_type('rsplit'), str_type('|'), 15)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a//b//c//d'), str_type('rsplit'),
            str_type('//'))
        self.checkequal([str_type('a//b//c'), str_type('d')], str_type(
            'a//b//c//d'), str_type('rsplit'), str_type('//'), 1)
        self.checkequal([str_type('a//b'), str_type('c'), str_type('d')],
            str_type('a//b//c//d'), str_type('rsplit'), str_type('//'), 2)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a//b//c//d'), str_type('rsplit'),
            str_type('//'), 3)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a//b//c//d'), str_type('rsplit'),
            str_type('//'), 4)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a//b//c//d'), str_type('rsplit'),
            str_type('//'), sys.maxsize - 5)
        self.checkequal([str_type('a//b//c//d')], str_type('a//b//c//d'),
            str_type('rsplit'), str_type('//'), 0)
        self.checkequal([str_type('a////b////c'), str_type(''), str_type(
            'd')], str_type('a////b////c////d'), str_type('rsplit'),
            str_type('//'), 2)
        self.checkequal([str_type(''), str_type(' begincase')], str_type(
            'test begincase'), str_type('rsplit'), str_type('test'))
        self.checkequal([str_type('endcase '), str_type('')], str_type(
            'endcase test'), str_type('rsplit'), str_type('test'))
        self.checkequal([str_type(''), str_type(' bothcase '), str_type('')
            ], str_type('test bothcase test'), str_type('rsplit'), str_type
            ('test'))
        self.checkequal([str_type('ab'), str_type('c')], str_type('abbbc'),
            str_type('rsplit'), str_type('bb'))
        self.checkequal([str_type(''), str_type('')], str_type('aaa'),
            str_type('rsplit'), str_type('aaa'))
        self.checkequal([str_type('aaa')], str_type('aaa'), str_type(
            'rsplit'), str_type('aaa'), 0)
        self.checkequal([str_type('ab'), str_type('ab')], str_type('abbaab'
            ), str_type('rsplit'), str_type('ba'))
        self.checkequal([str_type('aaaa')], str_type('aaaa'), str_type(
            'rsplit'), str_type('aab'))
        self.checkequal([str_type('')], str_type(''), str_type('rsplit'),
            str_type('aaa'))
        self.checkequal([str_type('aa')], str_type('aa'), str_type('rsplit'
            ), str_type('aaa'))
        self.checkequal([str_type('bbob'), str_type('A')], str_type(
            'bbobbbobbA'), str_type('rsplit'), str_type('bbobb'))
        self.checkequal([str_type(''), str_type('B'), str_type('A')],
            str_type('bbobbBbbobbA'), str_type('rsplit'), str_type('bbobb'))
        self.checkequal([str_type('a')] * 20, (str_type('aBLAH') * 20)[:-4],
            str_type('rsplit'), str_type('BLAH'))
        self.checkequal([str_type('a')] * 20, (str_type('aBLAH') * 20)[:-4],
            str_type('rsplit'), str_type('BLAH'), 19)
        self.checkequal([str_type('aBLAHa')] + [str_type('a')] * 18, (
            str_type('aBLAH') * 20)[:-4], str_type('rsplit'), str_type(
            'BLAH'), 18)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a|b|c|d'), str_type('rsplit'), sep=
            str_type('|'))
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d'), str_type('rsplit'), sep=None)
        self.checkequal([str_type('a b c'), str_type('d')], str_type(
            'a b c d'), str_type('rsplit'), sep=None, maxsplit=1)
        self.checkequal([str_type('a|b|c'), str_type('d')], str_type(
            'a|b|c|d'), str_type('rsplit'), str_type('|'), maxsplit=1)
        self.checkequal([str_type('a|b|c'), str_type('d')], str_type(
            'a|b|c|d'), str_type('rsplit'), sep=str_type('|'), maxsplit=1)
        self.checkequal([str_type('a|b|c'), str_type('d')], str_type(
            'a|b|c|d'), str_type('rsplit'), maxsplit=1, sep=str_type('|'))
        self.checkequal([str_type('a b c'), str_type('d')], str_type(
            'a b c d'), str_type('rsplit'), maxsplit=1)
        self.checkraises(TypeError, str_type('hello'), str_type('rsplit'), 
            42, 42, 42)
        self.checkraises(ValueError, str_type('hello'), str_type('rsplit'),
            str_type(''))
        self.checkraises(ValueError, str_type('hello'), str_type('rsplit'),
            str_type(''), 0)

    def test_replace(self):
        EQ = self.checkequal
        EQ(str_type(''), str_type(''), str_type('replace'), str_type(''),
            str_type(''))
        EQ(str_type('A'), str_type(''), str_type('replace'), str_type(''),
            str_type('A'))
        EQ(str_type(''), str_type(''), str_type('replace'), str_type('A'),
            str_type(''))
        EQ(str_type(''), str_type(''), str_type('replace'), str_type('A'),
            str_type('A'))
        EQ(str_type(''), str_type(''), str_type('replace'), str_type(''),
            str_type(''), 100)
        EQ(str_type('A'), str_type(''), str_type('replace'), str_type(''),
            str_type('A'), 100)
        EQ(str_type(''), str_type(''), str_type('replace'), str_type(''),
            str_type(''), sys.maxsize)
        EQ(str_type('A'), str_type('A'), str_type('replace'), str_type(''),
            str_type(''))
        EQ(str_type('*A*'), str_type('A'), str_type('replace'), str_type(''
            ), str_type('*'))
        EQ(str_type('*1A*1'), str_type('A'), str_type('replace'), str_type(
            ''), str_type('*1'))
        EQ(str_type('*-#A*-#'), str_type('A'), str_type('replace'),
            str_type(''), str_type('*-#'))
        EQ(str_type('*-A*-A*-'), str_type('AA'), str_type('replace'),
            str_type(''), str_type('*-'))
        EQ(str_type('*-A*-A*-'), str_type('AA'), str_type('replace'),
            str_type(''), str_type('*-'), -1)
        EQ(str_type('*-A*-A*-'), str_type('AA'), str_type('replace'),
            str_type(''), str_type('*-'), sys.maxsize)
        EQ(str_type('*-A*-A*-'), str_type('AA'), str_type('replace'),
            str_type(''), str_type('*-'), 4)
        EQ(str_type('*-A*-A*-'), str_type('AA'), str_type('replace'),
            str_type(''), str_type('*-'), 3)
        EQ(str_type('*-A*-A'), str_type('AA'), str_type('replace'),
            str_type(''), str_type('*-'), 2)
        EQ(str_type('*-AA'), str_type('AA'), str_type('replace'), str_type(
            ''), str_type('*-'), 1)
        EQ(str_type('AA'), str_type('AA'), str_type('replace'), str_type(''
            ), str_type('*-'), 0)
        EQ(str_type(''), str_type('A'), str_type('replace'), str_type('A'),
            str_type(''))
        EQ(str_type(''), str_type('AAA'), str_type('replace'), str_type('A'
            ), str_type(''))
        EQ(str_type(''), str_type('AAA'), str_type('replace'), str_type('A'
            ), str_type(''), -1)
        EQ(str_type(''), str_type('AAA'), str_type('replace'), str_type('A'
            ), str_type(''), sys.maxsize)
        EQ(str_type(''), str_type('AAA'), str_type('replace'), str_type('A'
            ), str_type(''), 4)
        EQ(str_type(''), str_type('AAA'), str_type('replace'), str_type('A'
            ), str_type(''), 3)
        EQ(str_type('A'), str_type('AAA'), str_type('replace'), str_type(
            'A'), str_type(''), 2)
        EQ(str_type('AA'), str_type('AAA'), str_type('replace'), str_type(
            'A'), str_type(''), 1)
        EQ(str_type('AAA'), str_type('AAA'), str_type('replace'), str_type(
            'A'), str_type(''), 0)
        EQ(str_type(''), str_type('AAAAAAAAAA'), str_type('replace'),
            str_type('A'), str_type(''))
        EQ(str_type('BCD'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''))
        EQ(str_type('BCD'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''), -1)
        EQ(str_type('BCD'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''), sys.maxsize)
        EQ(str_type('BCD'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''), 5)
        EQ(str_type('BCD'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''), 4)
        EQ(str_type('BCDA'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''), 3)
        EQ(str_type('BCADA'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''), 2)
        EQ(str_type('BACADA'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''), 1)
        EQ(str_type('ABACADA'), str_type('ABACADA'), str_type('replace'),
            str_type('A'), str_type(''), 0)
        EQ(str_type('BCD'), str_type('ABCAD'), str_type('replace'),
            str_type('A'), str_type(''))
        EQ(str_type('BCD'), str_type('ABCADAA'), str_type('replace'),
            str_type('A'), str_type(''))
        EQ(str_type('BCD'), str_type('BCD'), str_type('replace'), str_type(
            'A'), str_type(''))
        EQ(str_type('*************'), str_type('*************'), str_type(
            'replace'), str_type('A'), str_type(''))
        EQ(str_type('^A^'), str_type('^') + str_type('A') * 1000 + str_type
            ('^'), str_type('replace'), str_type('A'), str_type(''), 999)
        EQ(str_type(''), str_type('the'), str_type('replace'), str_type(
            'the'), str_type(''))
        EQ(str_type('ater'), str_type('theater'), str_type('replace'),
            str_type('the'), str_type(''))
        EQ(str_type(''), str_type('thethe'), str_type('replace'), str_type(
            'the'), str_type(''))
        EQ(str_type(''), str_type('thethethethe'), str_type('replace'),
            str_type('the'), str_type(''))
        EQ(str_type('aaaa'), str_type('theatheatheathea'), str_type(
            'replace'), str_type('the'), str_type(''))
        EQ(str_type('that'), str_type('that'), str_type('replace'),
            str_type('the'), str_type(''))
        EQ(str_type('thaet'), str_type('thaet'), str_type('replace'),
            str_type('the'), str_type(''))
        EQ(str_type('here and re'), str_type('here and there'), str_type(
            'replace'), str_type('the'), str_type(''))
        EQ(str_type('here and re and re'), str_type(
            'here and there and there'), str_type('replace'), str_type(
            'the'), str_type(''), sys.maxsize)
        EQ(str_type('here and re and re'), str_type(
            'here and there and there'), str_type('replace'), str_type(
            'the'), str_type(''), -1)
        EQ(str_type('here and re and re'), str_type(
            'here and there and there'), str_type('replace'), str_type(
            'the'), str_type(''), 3)
        EQ(str_type('here and re and re'), str_type(
            'here and there and there'), str_type('replace'), str_type(
            'the'), str_type(''), 2)
        EQ(str_type('here and re and there'), str_type(
            'here and there and there'), str_type('replace'), str_type(
            'the'), str_type(''), 1)
        EQ(str_type('here and there and there'), str_type(
            'here and there and there'), str_type('replace'), str_type(
            'the'), str_type(''), 0)
        EQ(str_type('here and re and re'), str_type(
            'here and there and there'), str_type('replace'), str_type(
            'the'), str_type(''))
        EQ(str_type('abc'), str_type('abc'), str_type('replace'), str_type(
            'the'), str_type(''))
        EQ(str_type('abcdefg'), str_type('abcdefg'), str_type('replace'),
            str_type('the'), str_type(''))
        EQ(str_type('bob'), str_type('bbobob'), str_type('replace'),
            str_type('bob'), str_type(''))
        EQ(str_type('bobXbob'), str_type('bbobobXbbobob'), str_type(
            'replace'), str_type('bob'), str_type(''))
        EQ(str_type('aaaaaaa'), str_type('aaaaaaabob'), str_type('replace'),
            str_type('bob'), str_type(''))
        EQ(str_type('aaaaaaa'), str_type('aaaaaaa'), str_type('replace'),
            str_type('bob'), str_type(''))
        EQ(str_type('Who goes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('o'), str_type('o'))
        EQ(str_type('WhO gOes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('o'), str_type('O'))
        EQ(str_type('WhO gOes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('o'), str_type('O'), sys.maxsize)
        EQ(str_type('WhO gOes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('o'), str_type('O'), -1)
        EQ(str_type('WhO gOes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('o'), str_type('O'), 3)
        EQ(str_type('WhO gOes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('o'), str_type('O'), 2)
        EQ(str_type('WhO goes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('o'), str_type('O'), 1)
        EQ(str_type('Who goes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('o'), str_type('O'), 0)
        EQ(str_type('Who goes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('a'), str_type('q'))
        EQ(str_type('who goes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('W'), str_type('w'))
        EQ(str_type('wwho goes there?ww'), str_type('WWho goes there?WW'),
            str_type('replace'), str_type('W'), str_type('w'))
        EQ(str_type('Who goes there!'), str_type('Who goes there?'),
            str_type('replace'), str_type('?'), str_type('!'))
        EQ(str_type('Who goes there!!'), str_type('Who goes there??'),
            str_type('replace'), str_type('?'), str_type('!'))
        EQ(str_type('Who goes there?'), str_type('Who goes there?'),
            str_type('replace'), str_type('.'), str_type('!'))
        EQ(str_type('Th** ** a t**sue'), str_type('This is a tissue'),
            str_type('replace'), str_type('is'), str_type('**'))
        EQ(str_type('Th** ** a t**sue'), str_type('This is a tissue'),
            str_type('replace'), str_type('is'), str_type('**'), sys.maxsize)
        EQ(str_type('Th** ** a t**sue'), str_type('This is a tissue'),
            str_type('replace'), str_type('is'), str_type('**'), -1)
        EQ(str_type('Th** ** a t**sue'), str_type('This is a tissue'),
            str_type('replace'), str_type('is'), str_type('**'), 4)
        EQ(str_type('Th** ** a t**sue'), str_type('This is a tissue'),
            str_type('replace'), str_type('is'), str_type('**'), 3)
        EQ(str_type('Th** ** a tissue'), str_type('This is a tissue'),
            str_type('replace'), str_type('is'), str_type('**'), 2)
        EQ(str_type('Th** is a tissue'), str_type('This is a tissue'),
            str_type('replace'), str_type('is'), str_type('**'), 1)
        EQ(str_type('This is a tissue'), str_type('This is a tissue'),
            str_type('replace'), str_type('is'), str_type('**'), 0)
        EQ(str_type('cobob'), str_type('bobob'), str_type('replace'),
            str_type('bob'), str_type('cob'))
        EQ(str_type('cobobXcobocob'), str_type('bobobXbobobob'), str_type(
            'replace'), str_type('bob'), str_type('cob'))
        EQ(str_type('bobob'), str_type('bobob'), str_type('replace'),
            str_type('bot'), str_type('bot'))
        EQ(str_type('ReyKKjaviKK'), str_type('Reykjavik'), str_type(
            'replace'), str_type('k'), str_type('KK'))
        EQ(str_type('ReyKKjaviKK'), str_type('Reykjavik'), str_type(
            'replace'), str_type('k'), str_type('KK'), -1)
        EQ(str_type('ReyKKjaviKK'), str_type('Reykjavik'), str_type(
            'replace'), str_type('k'), str_type('KK'), sys.maxsize)
        EQ(str_type('ReyKKjaviKK'), str_type('Reykjavik'), str_type(
            'replace'), str_type('k'), str_type('KK'), 2)
        EQ(str_type('ReyKKjavik'), str_type('Reykjavik'), str_type(
            'replace'), str_type('k'), str_type('KK'), 1)
        EQ(str_type('Reykjavik'), str_type('Reykjavik'), str_type('replace'
            ), str_type('k'), str_type('KK'), 0)
        EQ(str_type('A----B----C----'), str_type('A.B.C.'), str_type(
            'replace'), str_type('.'), str_type('----'))
        EQ(str_type('...м......&lt;'), str_type('...м......<'), str_type(
            'replace'), str_type('<'), str_type('&lt;'))
        EQ(str_type('Reykjavik'), str_type('Reykjavik'), str_type('replace'
            ), str_type('q'), str_type('KK'))
        EQ(str_type('ham, ham, eggs and ham'), str_type(
            'spam, spam, eggs and spam'), str_type('replace'), str_type(
            'spam'), str_type('ham'))
        EQ(str_type('ham, ham, eggs and ham'), str_type(
            'spam, spam, eggs and spam'), str_type('replace'), str_type(
            'spam'), str_type('ham'), sys.maxsize)
        EQ(str_type('ham, ham, eggs and ham'), str_type(
            'spam, spam, eggs and spam'), str_type('replace'), str_type(
            'spam'), str_type('ham'), -1)
        EQ(str_type('ham, ham, eggs and ham'), str_type(
            'spam, spam, eggs and spam'), str_type('replace'), str_type(
            'spam'), str_type('ham'), 4)
        EQ(str_type('ham, ham, eggs and ham'), str_type(
            'spam, spam, eggs and spam'), str_type('replace'), str_type(
            'spam'), str_type('ham'), 3)
        EQ(str_type('ham, ham, eggs and spam'), str_type(
            'spam, spam, eggs and spam'), str_type('replace'), str_type(
            'spam'), str_type('ham'), 2)
        EQ(str_type('ham, spam, eggs and spam'), str_type(
            'spam, spam, eggs and spam'), str_type('replace'), str_type(
            'spam'), str_type('ham'), 1)
        EQ(str_type('spam, spam, eggs and spam'), str_type(
            'spam, spam, eggs and spam'), str_type('replace'), str_type(
            'spam'), str_type('ham'), 0)
        EQ(str_type('bobob'), str_type('bobobob'), str_type('replace'),
            str_type('bobob'), str_type('bob'))
        EQ(str_type('bobobXbobob'), str_type('bobobobXbobobob'), str_type(
            'replace'), str_type('bobob'), str_type('bob'))
        EQ(str_type('BOBOBOB'), str_type('BOBOBOB'), str_type('replace'),
            str_type('bob'), str_type('bobby'))
        self.checkequal(str_type('one@two!three!'), str_type(
            'one!two!three!'), str_type('replace'), str_type('!'), str_type
            ('@'), 1)
        self.checkequal(str_type('onetwothree'), str_type('one!two!three!'),
            str_type('replace'), str_type('!'), str_type(''))
        self.checkequal(str_type('one@two@three!'), str_type(
            'one!two!three!'), str_type('replace'), str_type('!'), str_type
            ('@'), 2)
        self.checkequal(str_type('one@two@three@'), str_type(
            'one!two!three!'), str_type('replace'), str_type('!'), str_type
            ('@'), 3)
        self.checkequal(str_type('one@two@three@'), str_type(
            'one!two!three!'), str_type('replace'), str_type('!'), str_type
            ('@'), 4)
        self.checkequal(str_type('one!two!three!'), str_type(
            'one!two!three!'), str_type('replace'), str_type('!'), str_type
            ('@'), 0)
        self.checkequal(str_type('one@two@three@'), str_type(
            'one!two!three!'), str_type('replace'), str_type('!'), str_type
            ('@'))
        self.checkequal(str_type('one!two!three!'), str_type(
            'one!two!three!'), str_type('replace'), str_type('x'), str_type
            ('@'))
        self.checkequal(str_type('one!two!three!'), str_type(
            'one!two!three!'), str_type('replace'), str_type('x'), str_type
            ('@'), 2)
        self.checkequal(str_type('-a-b-c-'), str_type('abc'), str_type(
            'replace'), str_type(''), str_type('-'))
        self.checkequal(str_type('-a-b-c'), str_type('abc'), str_type(
            'replace'), str_type(''), str_type('-'), 3)
        self.checkequal(str_type('abc'), str_type('abc'), str_type(
            'replace'), str_type(''), str_type('-'), 0)
        self.checkequal(str_type(''), str_type(''), str_type('replace'),
            str_type(''), str_type(''))
        self.checkequal(str_type('abc'), str_type('abc'), str_type(
            'replace'), str_type('ab'), str_type('--'), 0)
        self.checkequal(str_type('abc'), str_type('abc'), str_type(
            'replace'), str_type('xy'), str_type('--'))
        self.checkequal(str_type(''), str_type('123'), str_type('replace'),
            str_type('123'), str_type(''))
        self.checkequal(str_type(''), str_type('123123'), str_type(
            'replace'), str_type('123'), str_type(''))
        self.checkequal(str_type('x'), str_type('123x123'), str_type(
            'replace'), str_type('123'), str_type(''))
        self.checkraises(TypeError, str_type('hello'), str_type('replace'))
        self.checkraises(TypeError, str_type('hello'), str_type('replace'), 42)
        self.checkraises(TypeError, str_type('hello'), str_type('replace'),
            42, str_type('h'))
        self.checkraises(TypeError, str_type('hello'), str_type('replace'),
            str_type('h'), 42)

    def test_replace_uses_two_way_maxcount(self):
        A, B = str_type('A') * 1000, str_type('B') * 1000
        AABAA = A + A + B + A + A
        ABBA = A + B + B + A
        self.checkequal(AABAA + ABBA, AABAA + ABBA, str_type('replace'),
            ABBA, str_type('ccc'), 0)
        self.checkequal(AABAA + str_type('ccc'), AABAA + ABBA, str_type(
            'replace'), ABBA, str_type('ccc'), 1)
        self.checkequal(AABAA + str_type('ccc'), AABAA + ABBA, str_type(
            'replace'), ABBA, str_type('ccc'), 2)

    @unittest.skipIf(sys.maxsize > 1 << 32 or struct.calcsize(str_type('P')
        ) != 4, str_type('only applies to 32-bit platforms'))
    def test_replace_overflow(self):
        A2_16 = str_type('A') * 2 ** 16
        self.checkraises(OverflowError, A2_16, str_type('replace'),
            str_type(''), A2_16)
        self.checkraises(OverflowError, A2_16, str_type('replace'),
            str_type('A'), A2_16)
        self.checkraises(OverflowError, A2_16, str_type('replace'),
            str_type('AA'), A2_16 + A2_16)

    def test_removeprefix(self):
        self.checkequal(str_type('am'), str_type('spam'), str_type(
            'removeprefix'), str_type('sp'))
        self.checkequal(str_type('spamspam'), str_type('spamspamspam'),
            str_type('removeprefix'), str_type('spam'))
        self.checkequal(str_type('spam'), str_type('spam'), str_type(
            'removeprefix'), str_type('python'))
        self.checkequal(str_type('spam'), str_type('spam'), str_type(
            'removeprefix'), str_type('spider'))
        self.checkequal(str_type('spam'), str_type('spam'), str_type(
            'removeprefix'), str_type('spam and eggs'))
        self.checkequal(str_type(''), str_type(''), str_type('removeprefix'
            ), str_type(''))
        self.checkequal(str_type(''), str_type(''), str_type('removeprefix'
            ), str_type('abcde'))
        self.checkequal(str_type('abcde'), str_type('abcde'), str_type(
            'removeprefix'), str_type(''))
        self.checkequal(str_type(''), str_type('abcde'), str_type(
            'removeprefix'), str_type('abcde'))
        self.checkraises(TypeError, str_type('hello'), str_type('removeprefix')
            )
        self.checkraises(TypeError, str_type('hello'), str_type(
            'removeprefix'), 42)
        self.checkraises(TypeError, str_type('hello'), str_type(
            'removeprefix'), 42, str_type('h'))
        self.checkraises(TypeError, str_type('hello'), str_type(
            'removeprefix'), str_type('h'), 42)
        self.checkraises(TypeError, str_type('hello'), str_type(
            'removeprefix'), (str_type('he'), str_type('l')))

    def test_removesuffix(self):
        self.checkequal(str_type('sp'), str_type('spam'), str_type(
            'removesuffix'), str_type('am'))
        self.checkequal(str_type('spamspam'), str_type('spamspamspam'),
            str_type('removesuffix'), str_type('spam'))
        self.checkequal(str_type('spam'), str_type('spam'), str_type(
            'removesuffix'), str_type('python'))
        self.checkequal(str_type('spam'), str_type('spam'), str_type(
            'removesuffix'), str_type('blam'))
        self.checkequal(str_type('spam'), str_type('spam'), str_type(
            'removesuffix'), str_type('eggs and spam'))
        self.checkequal(str_type(''), str_type(''), str_type('removesuffix'
            ), str_type(''))
        self.checkequal(str_type(''), str_type(''), str_type('removesuffix'
            ), str_type('abcde'))
        self.checkequal(str_type('abcde'), str_type('abcde'), str_type(
            'removesuffix'), str_type(''))
        self.checkequal(str_type(''), str_type('abcde'), str_type(
            'removesuffix'), str_type('abcde'))
        self.checkraises(TypeError, str_type('hello'), str_type('removesuffix')
            )
        self.checkraises(TypeError, str_type('hello'), str_type(
            'removesuffix'), 42)
        self.checkraises(TypeError, str_type('hello'), str_type(
            'removesuffix'), 42, str_type('h'))
        self.checkraises(TypeError, str_type('hello'), str_type(
            'removesuffix'), str_type('h'), 42)
        self.checkraises(TypeError, str_type('hello'), str_type(
            'removesuffix'), (str_type('lo'), str_type('l')))

    def test_capitalize(self):
        self.checkequal(str_type(' hello '), str_type(' hello '), str_type(
            'capitalize'))
        self.checkequal(str_type('Hello '), str_type('Hello '), str_type(
            'capitalize'))
        self.checkequal(str_type('Hello '), str_type('hello '), str_type(
            'capitalize'))
        self.checkequal(str_type('Aaaa'), str_type('aaaa'), str_type(
            'capitalize'))
        self.checkequal(str_type('Aaaa'), str_type('AaAa'), str_type(
            'capitalize'))
        self.checkraises(TypeError, str_type('hello'), str_type(
            'capitalize'), 42)

    def test_additional_split(self):
        self.checkequal([str_type('this'), str_type('is'), str_type('the'),
            str_type('split'), str_type('function')], str_type(
            'this is the split function'), str_type('split'))
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d '), str_type('split'))
        self.checkequal([str_type('a'), str_type('b c d')], str_type(
            'a b c d'), str_type('split'), None, 1)
        self.checkequal([str_type('a'), str_type('b'), str_type('c d')],
            str_type('a b c d'), str_type('split'), None, 2)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d'), str_type('split'), None, 3)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d'), str_type('split'), None, 4)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d'), str_type('split'), None, 
            sys.maxsize - 1)
        self.checkequal([str_type('a b c d')], str_type('a b c d'),
            str_type('split'), None, 0)
        self.checkequal([str_type('a b c d')], str_type('  a b c d'),
            str_type('split'), None, 0)
        self.checkequal([str_type('a'), str_type('b'), str_type('c  d')],
            str_type('a  b  c  d'), str_type('split'), None, 2)
        self.checkequal([], str_type('         '), str_type('split'))
        self.checkequal([str_type('a')], str_type('  a    '), str_type('split')
            )
        self.checkequal([str_type('a'), str_type('b')], str_type(
            '  a    b   '), str_type('split'))
        self.checkequal([str_type('a'), str_type('b   ')], str_type(
            '  a    b   '), str_type('split'), None, 1)
        self.checkequal([str_type('a    b   c   ')], str_type(
            '  a    b   c   '), str_type('split'), None, 0)
        self.checkequal([str_type('a'), str_type('b   c   ')], str_type(
            '  a    b   c   '), str_type('split'), None, 1)
        self.checkequal([str_type('a'), str_type('b'), str_type('c   ')],
            str_type('  a    b   c   '), str_type('split'), None, 2)
        self.checkequal([str_type('a'), str_type('b'), str_type('c')],
            str_type('  a    b   c   '), str_type('split'), None, 3)
        self.checkequal([str_type('a'), str_type('b')], str_type(
            '\n\ta \t\r b \x0b '), str_type('split'))
        aaa = str_type(' a ') * 20
        self.checkequal([str_type('a')] * 20, aaa, str_type('split'))
        self.checkequal([str_type('a')] + [aaa[4:]], aaa, str_type('split'),
            None, 1)
        self.checkequal([str_type('a')] * 19 + [str_type('a ')], aaa,
            str_type('split'), None, 19)
        for b in (str_type('arf\tbarf'), str_type('arf\nbarf'), str_type(
            'arf\rbarf'), str_type('arf\x0cbarf'), str_type('arf\x0bbarf')):
            self.checkequal([str_type('arf'), str_type('barf')], b,
                str_type('split'))
            self.checkequal([str_type('arf'), str_type('barf')], b,
                str_type('split'), None)
            self.checkequal([str_type('arf'), str_type('barf')], b,
                str_type('split'), None, 2)

    def test_additional_rsplit(self):
        self.checkequal([str_type('this'), str_type('is'), str_type('the'),
            str_type('rsplit'), str_type('function')], str_type(
            'this is the rsplit function'), str_type('rsplit'))
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d '), str_type('rsplit'))
        self.checkequal([str_type('a b c'), str_type('d')], str_type(
            'a b c d'), str_type('rsplit'), None, 1)
        self.checkequal([str_type('a b'), str_type('c'), str_type('d')],
            str_type('a b c d'), str_type('rsplit'), None, 2)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d'), str_type('rsplit'), None, 3)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d'), str_type('rsplit'), None, 4)
        self.checkequal([str_type('a'), str_type('b'), str_type('c'),
            str_type('d')], str_type('a b c d'), str_type('rsplit'), None, 
            sys.maxsize - 20)
        self.checkequal([str_type('a b c d')], str_type('a b c d'),
            str_type('rsplit'), None, 0)
        self.checkequal([str_type('a b c d')], str_type('a b c d  '),
            str_type('rsplit'), None, 0)
        self.checkequal([str_type('a  b'), str_type('c'), str_type('d')],
            str_type('a  b  c  d'), str_type('rsplit'), None, 2)
        self.checkequal([], str_type('         '), str_type('rsplit'))
        self.checkequal([str_type('a')], str_type('  a    '), str_type(
            'rsplit'))
        self.checkequal([str_type('a'), str_type('b')], str_type(
            '  a    b   '), str_type('rsplit'))
        self.checkequal([str_type('  a'), str_type('b')], str_type(
            '  a    b   '), str_type('rsplit'), None, 1)
        self.checkequal([str_type('  a    b   c')], str_type(
            '  a    b   c   '), str_type('rsplit'), None, 0)
        self.checkequal([str_type('  a    b'), str_type('c')], str_type(
            '  a    b   c   '), str_type('rsplit'), None, 1)
        self.checkequal([str_type('  a'), str_type('b'), str_type('c')],
            str_type('  a    b   c   '), str_type('rsplit'), None, 2)
        self.checkequal([str_type('a'), str_type('b'), str_type('c')],
            str_type('  a    b   c   '), str_type('rsplit'), None, 3)
        self.checkequal([str_type('a'), str_type('b')], str_type(
            '\n\ta \t\r b \x0b '), str_type('rsplit'), None, 88)
        aaa = str_type(' a ') * 20
        self.checkequal([str_type('a')] * 20, aaa, str_type('rsplit'))
        self.checkequal([aaa[:-4]] + [str_type('a')], aaa, str_type(
            'rsplit'), None, 1)
        self.checkequal([str_type(' a  a')] + [str_type('a')] * 18, aaa,
            str_type('rsplit'), None, 18)
        for b in (str_type('arf\tbarf'), str_type('arf\nbarf'), str_type(
            'arf\rbarf'), str_type('arf\x0cbarf'), str_type('arf\x0bbarf')):
            self.checkequal([str_type('arf'), str_type('barf')], b,
                str_type('rsplit'))
            self.checkequal([str_type('arf'), str_type('barf')], b,
                str_type('rsplit'), None)
            self.checkequal([str_type('arf'), str_type('barf')], b,
                str_type('rsplit'), None, 2)

    def test_strip_whitespace(self):
        self.checkequal(str_type('hello'), str_type('   hello   '),
            str_type('strip'))
        self.checkequal(str_type('hello   '), str_type('   hello   '),
            str_type('lstrip'))
        self.checkequal(str_type('   hello'), str_type('   hello   '),
            str_type('rstrip'))
        self.checkequal(str_type('hello'), str_type('hello'), str_type('strip')
            )
        b = str_type(' \t\n\r\x0c\x0babc \t\n\r\x0c\x0b')
        self.checkequal(str_type('abc'), b, str_type('strip'))
        self.checkequal(str_type('abc \t\n\r\x0c\x0b'), b, str_type('lstrip'))
        self.checkequal(str_type(' \t\n\r\x0c\x0babc'), b, str_type('rstrip'))
        self.checkequal(str_type('hello'), str_type('   hello   '),
            str_type('strip'), None)
        self.checkequal(str_type('hello   '), str_type('   hello   '),
            str_type('lstrip'), None)
        self.checkequal(str_type('   hello'), str_type('   hello   '),
            str_type('rstrip'), None)
        self.checkequal(str_type('hello'), str_type('hello'), str_type(
            'strip'), None)

    def test_strip(self):
        self.checkequal(str_type('hello'), str_type('xyzzyhelloxyzzy'),
            str_type('strip'), str_type('xyz'))
        self.checkequal(str_type('helloxyzzy'), str_type('xyzzyhelloxyzzy'),
            str_type('lstrip'), str_type('xyz'))
        self.checkequal(str_type('xyzzyhello'), str_type('xyzzyhelloxyzzy'),
            str_type('rstrip'), str_type('xyz'))
        self.checkequal(str_type('hello'), str_type('hello'), str_type(
            'strip'), str_type('xyz'))
        self.checkequal(str_type(''), str_type('mississippi'), str_type(
            'strip'), str_type('mississippi'))
        self.checkequal(str_type('mississipp'), str_type('mississippi'),
            str_type('strip'), str_type('i'))
        self.checkraises(TypeError, str_type('hello'), str_type('strip'), 
            42, 42)
        self.checkraises(TypeError, str_type('hello'), str_type('lstrip'), 
            42, 42)
        self.checkraises(TypeError, str_type('hello'), str_type('rstrip'), 
            42, 42)

    def test_ljust(self):
        self.checkequal(str_type('abc       '), str_type('abc'), str_type(
            'ljust'), 10)
        self.checkequal(str_type('abc   '), str_type('abc'), str_type(
            'ljust'), 6)
        self.checkequal(str_type('abc'), str_type('abc'), str_type('ljust'), 3)
        self.checkequal(str_type('abc'), str_type('abc'), str_type('ljust'), 2)
        self.checkequal(str_type('abc*******'), str_type('abc'), str_type(
            'ljust'), 10, str_type('*'))
        self.checkraises(TypeError, str_type('abc'), str_type('ljust'))

    def test_rjust(self):
        self.checkequal(str_type('       abc'), str_type('abc'), str_type(
            'rjust'), 10)
        self.checkequal(str_type('   abc'), str_type('abc'), str_type(
            'rjust'), 6)
        self.checkequal(str_type('abc'), str_type('abc'), str_type('rjust'), 3)
        self.checkequal(str_type('abc'), str_type('abc'), str_type('rjust'), 2)
        self.checkequal(str_type('*******abc'), str_type('abc'), str_type(
            'rjust'), 10, str_type('*'))
        self.checkraises(TypeError, str_type('abc'), str_type('rjust'))

    def test_center(self):
        self.checkequal(str_type('   abc    '), str_type('abc'), str_type(
            'center'), 10)
        self.checkequal(str_type(' abc  '), str_type('abc'), str_type(
            'center'), 6)
        self.checkequal(str_type('abc'), str_type('abc'), str_type('center'), 3
            )
        self.checkequal(str_type('abc'), str_type('abc'), str_type('center'), 2
            )
        self.checkequal(str_type('***abc****'), str_type('abc'), str_type(
            'center'), 10, str_type('*'))
        self.checkraises(TypeError, str_type('abc'), str_type('center'))

    def test_swapcase(self):
        self.checkequal(str_type('hEllO CoMPuTErS'), str_type(
            'HeLLo cOmpUteRs'), str_type('swapcase'))
        self.checkraises(TypeError, str_type('hello'), str_type('swapcase'), 42
            )

    def test_zfill(self):
        self.checkequal(str_type('123'), str_type('123'), str_type('zfill'), 2)
        self.checkequal(str_type('123'), str_type('123'), str_type('zfill'), 3)
        self.checkequal(str_type('0123'), str_type('123'), str_type('zfill'), 4
            )
        self.checkequal(str_type('+123'), str_type('+123'), str_type(
            'zfill'), 3)
        self.checkequal(str_type('+123'), str_type('+123'), str_type(
            'zfill'), 4)
        self.checkequal(str_type('+0123'), str_type('+123'), str_type(
            'zfill'), 5)
        self.checkequal(str_type('-123'), str_type('-123'), str_type(
            'zfill'), 3)
        self.checkequal(str_type('-123'), str_type('-123'), str_type(
            'zfill'), 4)
        self.checkequal(str_type('-0123'), str_type('-123'), str_type(
            'zfill'), 5)
        self.checkequal(str_type('000'), str_type(''), str_type('zfill'), 3)
        self.checkequal(str_type('34'), str_type('34'), str_type('zfill'), 1)
        self.checkequal(str_type('0034'), str_type('34'), str_type('zfill'), 4)
        self.checkraises(TypeError, str_type('123'), str_type('zfill'))

    def test_islower(self):
        self.checkequal(False, str_type(''), str_type('islower'))
        self.checkequal(True, str_type('a'), str_type('islower'))
        self.checkequal(False, str_type('A'), str_type('islower'))
        self.checkequal(False, str_type('\n'), str_type('islower'))
        self.checkequal(True, str_type('abc'), str_type('islower'))
        self.checkequal(False, str_type('aBc'), str_type('islower'))
        self.checkequal(True, str_type('abc\n'), str_type('islower'))
        self.checkraises(TypeError, str_type('abc'), str_type('islower'), 42)

    def test_isupper(self):
        self.checkequal(False, str_type(''), str_type('isupper'))
        self.checkequal(False, str_type('a'), str_type('isupper'))
        self.checkequal(True, str_type('A'), str_type('isupper'))
        self.checkequal(False, str_type('\n'), str_type('isupper'))
        self.checkequal(True, str_type('ABC'), str_type('isupper'))
        self.checkequal(False, str_type('AbC'), str_type('isupper'))
        self.checkequal(True, str_type('ABC\n'), str_type('isupper'))
        self.checkraises(TypeError, str_type('abc'), str_type('isupper'), 42)

    def test_istitle(self):
        self.checkequal(False, str_type(''), str_type('istitle'))
        self.checkequal(False, str_type('a'), str_type('istitle'))
        self.checkequal(True, str_type('A'), str_type('istitle'))
        self.checkequal(False, str_type('\n'), str_type('istitle'))
        self.checkequal(True, str_type('A Titlecased Line'), str_type(
            'istitle'))
        self.checkequal(True, str_type('A\nTitlecased Line'), str_type(
            'istitle'))
        self.checkequal(True, str_type('A Titlecased, Line'), str_type(
            'istitle'))
        self.checkequal(False, str_type('Not a capitalized String'),
            str_type('istitle'))
        self.checkequal(False, str_type('Not\ta Titlecase String'),
            str_type('istitle'))
        self.checkequal(False, str_type('Not--a Titlecase String'),
            str_type('istitle'))
        self.checkequal(False, str_type('NOT'), str_type('istitle'))
        self.checkraises(TypeError, str_type('abc'), str_type('istitle'), 42)

    def test_isspace(self):
        self.checkequal(False, str_type(''), str_type('isspace'))
        self.checkequal(False, str_type('a'), str_type('isspace'))
        self.checkequal(True, str_type(' '), str_type('isspace'))
        self.checkequal(True, str_type('\t'), str_type('isspace'))
        self.checkequal(True, str_type('\r'), str_type('isspace'))
        self.checkequal(True, str_type('\n'), str_type('isspace'))
        self.checkequal(True, str_type(' \t\r\n'), str_type('isspace'))
        self.checkequal(False, str_type(' \t\r\na'), str_type('isspace'))
        self.checkraises(TypeError, str_type('abc'), str_type('isspace'), 42)

    def test_isalpha(self):
        self.checkequal(False, str_type(''), str_type('isalpha'))
        self.checkequal(True, str_type('a'), str_type('isalpha'))
        self.checkequal(True, str_type('A'), str_type('isalpha'))
        self.checkequal(False, str_type('\n'), str_type('isalpha'))
        self.checkequal(True, str_type('abc'), str_type('isalpha'))
        self.checkequal(False, str_type('aBc123'), str_type('isalpha'))
        self.checkequal(False, str_type('abc\n'), str_type('isalpha'))
        self.checkraises(TypeError, str_type('abc'), str_type('isalpha'), 42)

    def test_isalnum(self):
        self.checkequal(False, str_type(''), str_type('isalnum'))
        self.checkequal(True, str_type('a'), str_type('isalnum'))
        self.checkequal(True, str_type('A'), str_type('isalnum'))
        self.checkequal(False, str_type('\n'), str_type('isalnum'))
        self.checkequal(True, str_type('123abc456'), str_type('isalnum'))
        self.checkequal(True, str_type('a1b3c'), str_type('isalnum'))
        self.checkequal(False, str_type('aBc000 '), str_type('isalnum'))
        self.checkequal(False, str_type('abc\n'), str_type('isalnum'))
        self.checkraises(TypeError, str_type('abc'), str_type('isalnum'), 42)

    def test_isascii(self):
        self.checkequal(True, str_type(''), str_type('isascii'))
        self.checkequal(True, str_type('\x00'), str_type('isascii'))
        self.checkequal(True, str_type('\x7f'), str_type('isascii'))
        self.checkequal(True, str_type('\x00\x7f'), str_type('isascii'))
        self.checkequal(False, str_type('\x80'), str_type('isascii'))
        self.checkequal(False, str_type('é'), str_type('isascii'))
        for p in range(8):
            self.checkequal(True, str_type(' ') * p + str_type('\x7f'),
                str_type('isascii'))
            self.checkequal(False, str_type(' ') * p + str_type('\x80'),
                str_type('isascii'))
            self.checkequal(True, str_type(' ') * p + str_type('\x7f') + 
                str_type(' ') * 8, str_type('isascii'))
            self.checkequal(False, str_type(' ') * p + str_type('\x80') + 
                str_type(' ') * 8, str_type('isascii'))

    def test_isdigit(self):
        self.checkequal(False, str_type(''), str_type('isdigit'))
        self.checkequal(False, str_type('a'), str_type('isdigit'))
        self.checkequal(True, str_type('0'), str_type('isdigit'))
        self.checkequal(True, str_type('0123456789'), str_type('isdigit'))
        self.checkequal(False, str_type('0123456789a'), str_type('isdigit'))
        self.checkraises(TypeError, str_type('abc'), str_type('isdigit'), 42)

    def test_title(self):
        self.checkequal(str_type(' Hello '), str_type(' hello '), str_type(
            'title'))
        self.checkequal(str_type('Hello '), str_type('hello '), str_type(
            'title'))
        self.checkequal(str_type('Hello '), str_type('Hello '), str_type(
            'title'))
        self.checkequal(str_type('Format This As Title String'), str_type(
            'fOrMaT thIs aS titLe String'), str_type('title'))
        self.checkequal(str_type('Format,This-As*Title;String'), str_type(
            'fOrMaT,thIs-aS*titLe;String'), str_type('title'))
        self.checkequal(str_type('Getint'), str_type('getInt'), str_type(
            'title'))
        self.checkraises(TypeError, str_type('hello'), str_type('title'), 42)

    def test_splitlines(self):
        self.checkequal([str_type('abc'), str_type('def'), str_type(''),
            str_type('ghi')], str_type('abc\ndef\n\rghi'), str_type(
            'splitlines'))
        self.checkequal([str_type('abc'), str_type('def'), str_type(''),
            str_type('ghi')], str_type('abc\ndef\n\r\nghi'), str_type(
            'splitlines'))
        self.checkequal([str_type('abc'), str_type('def'), str_type('ghi')],
            str_type('abc\ndef\r\nghi'), str_type('splitlines'))
        self.checkequal([str_type('abc'), str_type('def'), str_type('ghi')],
            str_type('abc\ndef\r\nghi\n'), str_type('splitlines'))
        self.checkequal([str_type('abc'), str_type('def'), str_type('ghi'),
            str_type('')], str_type('abc\ndef\r\nghi\n\r'), str_type(
            'splitlines'))
        self.checkequal([str_type(''), str_type('abc'), str_type('def'),
            str_type('ghi'), str_type('')], str_type(
            '\nabc\ndef\r\nghi\n\r'), str_type('splitlines'))
        self.checkequal([str_type(''), str_type('abc'), str_type('def'),
            str_type('ghi'), str_type('')], str_type(
            '\nabc\ndef\r\nghi\n\r'), str_type('splitlines'), False)
        self.checkequal([str_type('\n'), str_type('abc\n'), str_type(
            'def\r\n'), str_type('ghi\n'), str_type('\r')], str_type(
            '\nabc\ndef\r\nghi\n\r'), str_type('splitlines'), True)
        self.checkequal([str_type(''), str_type('abc'), str_type('def'),
            str_type('ghi'), str_type('')], str_type(
            '\nabc\ndef\r\nghi\n\r'), str_type('splitlines'), keepends=False)
        self.checkequal([str_type('\n'), str_type('abc\n'), str_type(
            'def\r\n'), str_type('ghi\n'), str_type('\r')], str_type(
            '\nabc\ndef\r\nghi\n\r'), str_type('splitlines'), keepends=True)
        self.checkraises(TypeError, str_type('abc'), str_type('splitlines'),
            42, 42)


class StringLikeTest(BaseTest):

    def test_hash(self):
        a = self.type2test(str_type('DNSSEC'))
        b = self.type2test(str_type(''))
        for c in a:
            b += c
            hash(b)
        self.assertEqual(hash(a), hash(b))

    def test_capitalize_nonascii(self):
        self.checkequal(str_type('ῼῳῳῳ'), str_type('ῳῳῼῼ'), str_type(
            'capitalize'))
        self.checkequal(str_type('Ⓟⓨⓣⓗⓞⓝ'), str_type('ⓅⓎⓉⒽⓄⓃ'), str_type(
            'capitalize'))
        self.checkequal(str_type('Ⓟⓨⓣⓗⓞⓝ'), str_type('ⓟⓨⓣⓗⓞⓝ'), str_type(
            'capitalize'))
        self.checkequal(str_type('Ⅰⅱⅲ'), str_type('ⅠⅡⅢ'), str_type(
            'capitalize'))
        self.checkequal(str_type('Ⅰⅱⅲ'), str_type('ⅰⅱⅲ'), str_type(
            'capitalize'))
        self.checkequal(str_type('ᴀᶆȡᾷ'), str_type('ᴀᶆȡᾷ'), str_type(
            'capitalize'))

    def test_startswith(self):
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type('he'))
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type('hello'))
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('hello world'))
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type(''))
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('ello'))
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type('ello'), 1)
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type('o'), 4)
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('o'), 5)
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type(''), 5)
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('lo'), 6)
        self.checkequal(True, str_type('helloworld'), str_type('startswith'
            ), str_type('lowo'), 3)
        self.checkequal(True, str_type('helloworld'), str_type('startswith'
            ), str_type('lowo'), 3, 7)
        self.checkequal(False, str_type('helloworld'), str_type(
            'startswith'), str_type('lowo'), 3, 6)
        self.checkequal(True, str_type(''), str_type('startswith'),
            str_type(''), 0, 1)
        self.checkequal(True, str_type(''), str_type('startswith'),
            str_type(''), 0, 0)
        self.checkequal(False, str_type(''), str_type('startswith'),
            str_type(''), 1, 0)
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type('he'), 0, -1)
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type('he'), -53, -1)
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('hello'), 0, -1)
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('hello world'), -1, -10)
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('ello'), -5)
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type('ello'), -4)
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('o'), -2)
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type('o'), -1)
        self.checkequal(True, str_type('hello'), str_type('startswith'),
            str_type(''), -3, -3)
        self.checkequal(False, str_type('hello'), str_type('startswith'),
            str_type('lo'), -9)
        self.checkraises(TypeError, str_type('hello'), str_type('startswith'))
        self.checkraises(TypeError, str_type('hello'), str_type(
            'startswith'), 42)
        self.checkequal(True, str_type('hello'), str_type('startswith'), (
            str_type('he'), str_type('ha')))
        self.checkequal(False, str_type('hello'), str_type('startswith'), (
            str_type('lo'), str_type('llo')))
        self.checkequal(True, str_type('hello'), str_type('startswith'), (
            str_type('hellox'), str_type('hello')))
        self.checkequal(False, str_type('hello'), str_type('startswith'), ())
        self.checkequal(True, str_type('helloworld'), str_type('startswith'
            ), (str_type('hellowo'), str_type('rld'), str_type('lowo')), 3)
        self.checkequal(False, str_type('helloworld'), str_type(
            'startswith'), (str_type('hellowo'), str_type('ello'), str_type
            ('rld')), 3)
        self.checkequal(True, str_type('hello'), str_type('startswith'), (
            str_type('lo'), str_type('he')), 0, -1)
        self.checkequal(False, str_type('hello'), str_type('startswith'), (
            str_type('he'), str_type('hel')), 0, 1)
        self.checkequal(True, str_type('hello'), str_type('startswith'), (
            str_type('he'), str_type('hel')), 0, 2)
        self.checkraises(TypeError, str_type('hello'), str_type(
            'startswith'), (42,))

    def test_endswith(self):
        self.checkequal(True, str_type('hello'), str_type('endswith'),
            str_type('lo'))
        self.checkequal(False, str_type('hello'), str_type('endswith'),
            str_type('he'))
        self.checkequal(True, str_type('hello'), str_type('endswith'),
            str_type(''))
        self.checkequal(False, str_type('hello'), str_type('endswith'),
            str_type('hello world'))
        self.checkequal(False, str_type('helloworld'), str_type('endswith'),
            str_type('worl'))
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('worl'), 3, 9)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('world'), 3, 12)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), 1, 7)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), 2, 7)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), 3, 7)
        self.checkequal(False, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), 4, 7)
        self.checkequal(False, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), 3, 8)
        self.checkequal(False, str_type('ab'), str_type('endswith'),
            str_type('ab'), 0, 1)
        self.checkequal(False, str_type('ab'), str_type('endswith'),
            str_type('ab'), 0, 0)
        self.checkequal(True, str_type(''), str_type('endswith'), str_type(
            ''), 0, 1)
        self.checkequal(True, str_type(''), str_type('endswith'), str_type(
            ''), 0, 0)
        self.checkequal(False, str_type(''), str_type('endswith'), str_type
            (''), 1, 0)
        self.checkequal(True, str_type('hello'), str_type('endswith'),
            str_type('lo'), -2)
        self.checkequal(False, str_type('hello'), str_type('endswith'),
            str_type('he'), -2)
        self.checkequal(True, str_type('hello'), str_type('endswith'),
            str_type(''), -3, -3)
        self.checkequal(False, str_type('hello'), str_type('endswith'),
            str_type('hello world'), -10, -2)
        self.checkequal(False, str_type('helloworld'), str_type('endswith'),
            str_type('worl'), -6)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('worl'), -5, -1)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('worl'), -5, 9)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('world'), -7, 12)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), -99, -3)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), -8, -3)
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), -7, -3)
        self.checkequal(False, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), 3, -4)
        self.checkequal(False, str_type('helloworld'), str_type('endswith'),
            str_type('lowo'), -8, -2)
        self.checkraises(TypeError, str_type('hello'), str_type('endswith'))
        self.checkraises(TypeError, str_type('hello'), str_type('endswith'), 42
            )
        self.checkequal(False, str_type('hello'), str_type('endswith'), (
            str_type('he'), str_type('ha')))
        self.checkequal(True, str_type('hello'), str_type('endswith'), (
            str_type('lo'), str_type('llo')))
        self.checkequal(True, str_type('hello'), str_type('endswith'), (
            str_type('hellox'), str_type('hello')))
        self.checkequal(False, str_type('hello'), str_type('endswith'), ())
        self.checkequal(True, str_type('helloworld'), str_type('endswith'),
            (str_type('hellowo'), str_type('rld'), str_type('lowo')), 3)
        self.checkequal(False, str_type('helloworld'), str_type('endswith'),
            (str_type('hellowo'), str_type('ello'), str_type('rld')), 3, -1)
        self.checkequal(True, str_type('hello'), str_type('endswith'), (
            str_type('hell'), str_type('ell')), 0, -1)
        self.checkequal(False, str_type('hello'), str_type('endswith'), (
            str_type('he'), str_type('hel')), 0, 1)
        self.checkequal(True, str_type('hello'), str_type('endswith'), (
            str_type('he'), str_type('hell')), 0, 4)
        self.checkraises(TypeError, str_type('hello'), str_type('endswith'),
            (42,))

    def test___contains__(self):
        self.checkequal(True, str_type(''), str_type('__contains__'),
            str_type(''))
        self.checkequal(True, str_type('abc'), str_type('__contains__'),
            str_type(''))
        self.checkequal(False, str_type('abc'), str_type('__contains__'),
            str_type('\x00'))
        self.checkequal(True, str_type('\x00abc'), str_type('__contains__'),
            str_type('\x00'))
        self.checkequal(True, str_type('abc\x00'), str_type('__contains__'),
            str_type('\x00'))
        self.checkequal(True, str_type('\x00abc'), str_type('__contains__'),
            str_type('a'))
        self.checkequal(True, str_type('asdf'), str_type('__contains__'),
            str_type('asdf'))
        self.checkequal(False, str_type('asd'), str_type('__contains__'),
            str_type('asdf'))
        self.checkequal(False, str_type(''), str_type('__contains__'),
            str_type('asdf'))

    def test_subscript(self):
        self.checkequal(str_type('a'), str_type('abc'), str_type(
            '__getitem__'), 0)
        self.checkequal(str_type('c'), str_type('abc'), str_type(
            '__getitem__'), -1)
        self.checkequal(str_type('a'), str_type('abc'), str_type(
            '__getitem__'), 0)
        self.checkequal(str_type('abc'), str_type('abc'), str_type(
            '__getitem__'), slice(0, 3))
        self.checkequal(str_type('abc'), str_type('abc'), str_type(
            '__getitem__'), slice(0, 1000))
        self.checkequal(str_type('a'), str_type('abc'), str_type(
            '__getitem__'), slice(0, 1))
        self.checkequal(str_type(''), str_type('abc'), str_type(
            '__getitem__'), slice(0, 0))
        self.checkraises(TypeError, str_type('abc'), str_type('__getitem__'
            ), str_type('def'))
        for idx_type in (str_type('def'), object()):
            expected_msg = str_type("string indices must be integers, not '{}'"
                ).format(type(idx_type).__name__)
            self.checkraises(TypeError, str_type('abc'), str_type(
                '__getitem__'), idx_type, expected_msg=expected_msg)

    def test_slice(self):
        self.checkequal(str_type('abc'), str_type('abc'), str_type(
            '__getitem__'), slice(0, 1000))
        self.checkequal(str_type('abc'), str_type('abc'), str_type(
            '__getitem__'), slice(0, 3))
        self.checkequal(str_type('ab'), str_type('abc'), str_type(
            '__getitem__'), slice(0, 2))
        self.checkequal(str_type('bc'), str_type('abc'), str_type(
            '__getitem__'), slice(1, 3))
        self.checkequal(str_type('b'), str_type('abc'), str_type(
            '__getitem__'), slice(1, 2))
        self.checkequal(str_type(''), str_type('abc'), str_type(
            '__getitem__'), slice(2, 2))
        self.checkequal(str_type(''), str_type('abc'), str_type(
            '__getitem__'), slice(1000, 1000))
        self.checkequal(str_type(''), str_type('abc'), str_type(
            '__getitem__'), slice(2000, 1000))
        self.checkequal(str_type(''), str_type('abc'), str_type(
            '__getitem__'), slice(2, 1))
        self.checkraises(TypeError, str_type('abc'), str_type('__getitem__'
            ), str_type('def'))

    def test_extended_getslice(self):
        s = string.ascii_letters + string.digits
        indices = 0, None, 1, 3, 41, sys.maxsize, -1, -2, -37
        for start in indices:
            for stop in indices:
                for step in indices[1:]:
                    L = list(s)[start:stop:step]
                    self.checkequal(str_type('').join(L), s, str_type(
                        '__getitem__'), slice(start, stop, step))

    def test_mul(self):
        self.checkequal(str_type(''), str_type('abc'), str_type('__mul__'), -1)
        self.checkequal(str_type(''), str_type('abc'), str_type('__mul__'), 0)
        self.checkequal(str_type('abc'), str_type('abc'), str_type(
            '__mul__'), 1)
        self.checkequal(str_type('abcabcabc'), str_type('abc'), str_type(
            '__mul__'), 3)
        self.checkraises(TypeError, str_type('abc'), str_type('__mul__'))
        self.checkraises(TypeError, str_type('abc'), str_type('__mul__'),
            str_type(''))

    def test_join(self):
        self.checkequal(str_type('a b c d'), str_type(' '), str_type('join'
            ), [str_type('a'), str_type('b'), str_type('c'), str_type('d')])
        self.checkequal(str_type('abcd'), str_type(''), str_type('join'), (
            str_type('a'), str_type('b'), str_type('c'), str_type('d')))
        self.checkequal(str_type('bd'), str_type(''), str_type('join'), (
            str_type(''), str_type('b'), str_type(''), str_type('d')))
        self.checkequal(str_type('ac'), str_type(''), str_type('join'), (
            str_type('a'), str_type(''), str_type('c'), str_type('')))
        self.checkequal(str_type('w x y z'), str_type(' '), str_type('join'
            ), Sequence())
        self.checkequal(str_type('abc'), str_type('a'), str_type('join'), (
            str_type('abc'),))
        self.checkequal(str_type('z'), str_type('a'), str_type('join'),
            UserList([str_type('z')]))
        self.checkequal(str_type('a.b.c'), str_type('.'), str_type('join'),
            [str_type('a'), str_type('b'), str_type('c')])
        self.assertRaises(TypeError, str_type('.').join, [str_type('a'),
            str_type('b'), 3])
        for i in [5, 25, 125]:
            self.checkequal(((str_type('a') * i + str_type('-')) * i)[:-1],
                str_type('-'), str_type('join'), [str_type('a') * i] * i)
            self.checkequal(((str_type('a') * i + str_type('-')) * i)[:-1],
                str_type('-'), str_type('join'), (str_type('a') * i,) * i)


        class LiesAboutLengthSeq(Sequence):

            def __init__(self):
                self.seq = [str_type('a'), str_type('b'), str_type('c')]

            def __len__(self):
                return 8
        self.checkequal(str_type('a b c'), str_type(' '), str_type('join'),
            LiesAboutLengthSeq())
        self.checkraises(TypeError, str_type(' '), str_type('join'))
        self.checkraises(TypeError, str_type(' '), str_type('join'), None)
        self.checkraises(TypeError, str_type(' '), str_type('join'), 7)
        self.checkraises(TypeError, str_type(' '), str_type('join'), [1, 2,
            bytes()])
        try:

            def f():
                yield 4 + str_type('')
            self.fixtype(str_type(' ')).join(f())
        except TypeError as e:
            if str_type('+') not in str_type(e):
                self.fail(str_type('join() ate exception message'))
        else:
            self.fail(str_type('exception not raised'))

    def test_formatting(self):
        self.checkequal(str_type('+hello+'), str_type('+%s+'), str_type(
            '__mod__'), str_type('hello'))
        self.checkequal(str_type('+10+'), str_type('+%d+'), str_type(
            '__mod__'), 10)
        self.checkequal(str_type('a'), str_type('%c'), str_type('__mod__'),
            str_type('a'))
        self.checkequal(str_type('a'), str_type('%c'), str_type('__mod__'),
            str_type('a'))
        self.checkequal(str_type('"'), str_type('%c'), str_type('__mod__'), 34)
        self.checkequal(str_type('$'), str_type('%c'), str_type('__mod__'), 36)
        self.checkequal(str_type('10'), str_type('%d'), str_type('__mod__'), 10
            )
        self.checkequal(str_type('\x7f'), str_type('%c'), str_type(
            '__mod__'), 127)
        for ordinal in (-100, 2097152):
            self.checkraises((ValueError, OverflowError), str_type('%c'),
                str_type('__mod__'), ordinal)
        longvalue = sys.maxsize + 10
        slongvalue = str_type(longvalue)
        self.checkequal(str_type(' 42'), str_type('%3ld'), str_type(
            '__mod__'), 42)
        self.checkequal(str_type('42'), str_type('%d'), str_type('__mod__'),
            42.0)
        self.checkequal(slongvalue, str_type('%d'), str_type('__mod__'),
            longvalue)
        self.checkcall(str_type('%d'), str_type('__mod__'), float(longvalue))
        self.checkequal(str_type('0042.00'), str_type('%07.2f'), str_type(
            '__mod__'), 42)
        self.checkequal(str_type('0042.00'), str_type('%07.2F'), str_type(
            '__mod__'), 42)
        self.checkraises(TypeError, str_type('abc'), str_type('__mod__'))
        self.checkraises(TypeError, str_type('%(foo)s'), str_type('__mod__'
            ), 42)
        self.checkraises(TypeError, str_type('%s%s'), str_type('__mod__'),
            (42,))
        self.checkraises(TypeError, str_type('%c'), str_type('__mod__'), (
            None,))
        self.checkraises(ValueError, str_type('%(foo'), str_type('__mod__'), {}
            )
        self.checkraises(TypeError, str_type('%(foo)s %(bar)s'), str_type(
            '__mod__'), (str_type('foo'), 42))
        self.checkraises(TypeError, str_type('%d'), str_type('__mod__'),
            str_type('42'))
        self.checkraises(TypeError, str_type('%d'), str_type('__mod__'), 42 +
            0.0j)
        self.checkequal(str_type('bar'), str_type('%((foo))s'), str_type(
            '__mod__'), {str_type('(foo)'): str_type('bar')})
        self.checkequal(103 * str_type('a') + str_type('x'), str_type('%sx'
            ), str_type('__mod__'), 103 * str_type('a'))
        self.checkraises(TypeError, str_type('%*s'), str_type('__mod__'), (
            str_type('foo'), str_type('bar')))
        self.checkraises(TypeError, str_type('%10.*f'), str_type('__mod__'),
            (str_type('foo'), 42.0))
        self.checkraises(ValueError, str_type('%10'), str_type('__mod__'),
            (42,))
        self.checkraises(ValueError, str_type('%%%df') % 2 ** 64, str_type(
            '__mod__'), 3.2)
        self.checkraises(ValueError, str_type('%%.%df') % 2 ** 64, str_type
            ('__mod__'), 3.2)
        self.checkraises(OverflowError, str_type('%*s'), str_type('__mod__'
            ), (sys.maxsize + 1, str_type('')))
        self.checkraises(OverflowError, str_type('%.*f'), str_type(
            '__mod__'), (sys.maxsize + 1, 1.0 / 7))


        class X(object):
            pass
        self.checkraises(TypeError, str_type('abc'), str_type('__mod__'), X())

    @support.cpython_only
    def test_formatting_c_limits(self):
        _testcapi = import_helper.import_module(str_type('_testcapi'))
        SIZE_MAX = (1 << _testcapi.PY_SSIZE_T_MAX.bit_length() + 1) - 1
        self.checkraises(OverflowError, str_type('%*s'), str_type('__mod__'
            ), (_testcapi.PY_SSIZE_T_MAX + 1, str_type('')))
        self.checkraises(OverflowError, str_type('%.*f'), str_type(
            '__mod__'), (_testcapi.INT_MAX + 1, 1.0 / 7))
        self.checkraises(OverflowError, str_type('%*s'), str_type('__mod__'
            ), (SIZE_MAX + 1, str_type('')))
        self.checkraises(OverflowError, str_type('%.*f'), str_type(
            '__mod__'), (_testcapi.UINT_MAX + 1, 1.0 / 7))

    def test_floatformatting(self):
        for prec in range(100):
            format = str_type('%%.%if') % prec
            value = 0.01
            for x in range(60):
                value = value * 3.14159265359 / 3.0 * 10.0
                self.checkcall(format, str_type('__mod__'), value)

    def test_inplace_rewrites(self):
        self.checkequal(str_type('a'), str_type('A'), str_type('lower'))
        self.checkequal(True, str_type('A'), str_type('isupper'))
        self.checkequal(str_type('A'), str_type('a'), str_type('upper'))
        self.checkequal(True, str_type('a'), str_type('islower'))
        self.checkequal(str_type('a'), str_type('A'), str_type('replace'),
            str_type('A'), str_type('a'))
        self.checkequal(True, str_type('A'), str_type('isupper'))
        self.checkequal(str_type('A'), str_type('a'), str_type('capitalize'))
        self.checkequal(True, str_type('a'), str_type('islower'))
        self.checkequal(str_type('A'), str_type('a'), str_type('swapcase'))
        self.checkequal(True, str_type('a'), str_type('islower'))
        self.checkequal(str_type('A'), str_type('a'), str_type('title'))
        self.checkequal(True, str_type('a'), str_type('islower'))

    def test_partition(self):
        self.checkequal((str_type('this is the par'), str_type('ti'),
            str_type('tion method')), str_type(
            'this is the partition method'), str_type('partition'),
            str_type('ti'))
        S = str_type('http://www.python.org')
        self.checkequal((str_type('http'), str_type('://'), str_type(
            'www.python.org')), S, str_type('partition'), str_type('://'))
        self.checkequal((str_type('http://www.python.org'), str_type(''),
            str_type('')), S, str_type('partition'), str_type('?'))
        self.checkequal((str_type(''), str_type('http://'), str_type(
            'www.python.org')), S, str_type('partition'), str_type('http://'))
        self.checkequal((str_type('http://www.python.'), str_type('org'),
            str_type('')), S, str_type('partition'), str_type('org'))
        self.checkraises(ValueError, S, str_type('partition'), str_type(''))
        self.checkraises(TypeError, S, str_type('partition'), None)

    def test_rpartition(self):
        self.checkequal((str_type('this is the rparti'), str_type('ti'),
            str_type('on method')), str_type(
            'this is the rpartition method'), str_type('rpartition'),
            str_type('ti'))
        S = str_type('http://www.python.org')
        self.checkequal((str_type('http'), str_type('://'), str_type(
            'www.python.org')), S, str_type('rpartition'), str_type('://'))
        self.checkequal((str_type(''), str_type(''), str_type(
            'http://www.python.org')), S, str_type('rpartition'), str_type('?')
            )
        self.checkequal((str_type(''), str_type('http://'), str_type(
            'www.python.org')), S, str_type('rpartition'), str_type('http://'))
        self.checkequal((str_type('http://www.python.'), str_type('org'),
            str_type('')), S, str_type('rpartition'), str_type('org'))
        self.checkraises(ValueError, S, str_type('rpartition'), str_type(''))
        self.checkraises(TypeError, S, str_type('rpartition'), None)

    def test_none_arguments(self):
        s = str_type('hello')
        self.checkequal(2, s, str_type('find'), str_type('l'), None)
        self.checkequal(3, s, str_type('find'), str_type('l'), -2, None)
        self.checkequal(2, s, str_type('find'), str_type('l'), None, -2)
        self.checkequal(0, s, str_type('find'), str_type('h'), None, None)
        self.checkequal(3, s, str_type('rfind'), str_type('l'), None)
        self.checkequal(3, s, str_type('rfind'), str_type('l'), -2, None)
        self.checkequal(2, s, str_type('rfind'), str_type('l'), None, -2)
        self.checkequal(0, s, str_type('rfind'), str_type('h'), None, None)
        self.checkequal(2, s, str_type('index'), str_type('l'), None)
        self.checkequal(3, s, str_type('index'), str_type('l'), -2, None)
        self.checkequal(2, s, str_type('index'), str_type('l'), None, -2)
        self.checkequal(0, s, str_type('index'), str_type('h'), None, None)
        self.checkequal(3, s, str_type('rindex'), str_type('l'), None)
        self.checkequal(3, s, str_type('rindex'), str_type('l'), -2, None)
        self.checkequal(2, s, str_type('rindex'), str_type('l'), None, -2)
        self.checkequal(0, s, str_type('rindex'), str_type('h'), None, None)
        self.checkequal(2, s, str_type('count'), str_type('l'), None)
        self.checkequal(1, s, str_type('count'), str_type('l'), -2, None)
        self.checkequal(1, s, str_type('count'), str_type('l'), None, -2)
        self.checkequal(0, s, str_type('count'), str_type('x'), None, None)
        self.checkequal(True, s, str_type('endswith'), str_type('o'), None)
        self.checkequal(True, s, str_type('endswith'), str_type('lo'), -2, None
            )
        self.checkequal(True, s, str_type('endswith'), str_type('l'), None, -2)
        self.checkequal(False, s, str_type('endswith'), str_type('x'), None,
            None)
        self.checkequal(True, s, str_type('startswith'), str_type('h'), None)
        self.checkequal(True, s, str_type('startswith'), str_type('l'), -2,
            None)
        self.checkequal(True, s, str_type('startswith'), str_type('h'),
            None, -2)
        self.checkequal(False, s, str_type('startswith'), str_type('x'),
            None, None)

    def test_find_etc_raise_correct_error_messages(self):
        s = str_type('hello')
        x = str_type('x')
        self.assertRaisesRegex(TypeError, str_type('^find\\b'), s.find, x,
            None, None, None)
        self.assertRaisesRegex(TypeError, str_type('^rfind\\b'), s.rfind, x,
            None, None, None)
        self.assertRaisesRegex(TypeError, str_type('^index\\b'), s.index, x,
            None, None, None)
        self.assertRaisesRegex(TypeError, str_type('^rindex\\b'), s.rindex,
            x, None, None, None)
        self.assertRaisesRegex(TypeError, str_type('^count\\b'), s.count, x,
            None, None, None)
        self.assertRaisesRegex(TypeError, str_type('^startswith\\b'), s.
            startswith, x, None, None, None)
        self.assertRaisesRegex(TypeError, str_type('^endswith\\b'), s.
            endswith, x, None, None, None)
        self.checkequal(10, str_type('...м......<'), str_type('find'),
            str_type('<'))


class MixinStrUnicodeTest:

    def test_bug1001011(self):
        t = self.type2test


        class subclass(t):
            pass
        s1 = subclass(str_type('abcd'))
        s2 = t().join([s1])
        self.assertIsNot(s1, s2)
        self.assertIs(type(s2), t)
        s1 = t(str_type('abcd'))
        s2 = t().join([s1])
        self.assertIs(s1, s2)
