import unittest

from botlib.compositions import compositions, strjoin


class TokenizerTests(unittest.TestCase):

    def test_tokenizer(self):
        self.maxDiff = None

        self.assertEqual(list(compositions(1, 'ab')), [
            ('ab',),
        ])
        self.assertEqual(list(compositions(2, 'ab')), [
            ('a', 'b'),
        ])
        self.assertEqual(list(compositions(2, 'abc')), [
            ('a', 'bc'),
            ('ab', 'c'),
        ])
        self.assertEqual(list(compositions(2, 'abcd')), [
            ('a', 'bcd'),
            ('ab', 'cd'),
            ('abc', 'd'),
        ])
        self.assertEqual(list(compositions(3, 'abcd')), [
            ('a', 'b', 'cd'),
            ('a', 'bc', 'd'),
            ('ab', 'c', 'd'),
        ])
        self.assertEqual(list(compositions(3, 'abcde')), [
            ('a', 'b', 'cde'),
            ('a', 'bc', 'de'),
            ('a', 'bcd', 'e'),
            ('ab', 'c', 'de'),
            ('ab', 'cd', 'e'),
            ('abc', 'd', 'e'),
        ])
        self.assertEqual(list(compositions(2, 'abcdefghijklmn')), [
            ('a', 'bcdefghijklmn'),
            ('ab', 'cdefghijklmn'),
            ('abc', 'defghijklmn'),
            ('abcd', 'efghijklmn'),
            ('abcde', 'fghijklmn'),
            ('abcdef', 'ghijklmn'),
            ('abcdefg', 'hijklmn'),
            ('abcdefgh', 'ijklmn'),
            ('abcdefghi', 'jklmn'),
            ('abcdefghij', 'klmn'),
            ('abcdefghijk', 'lmn'),
            ('abcdefghijkl', 'mn'),
            ('abcdefghijklm', 'n'),
        ])
        self.assertEqual(list(compositions(9, 'abcdefghij')), [
            ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'ij'),
            ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'hi', 'j'),
            ('a', 'b', 'c', 'd', 'e', 'f', 'gh', 'i', 'j'),
            ('a', 'b', 'c', 'd', 'e', 'fg', 'h', 'i', 'j'),
            ('a', 'b', 'c', 'd', 'ef', 'g', 'h', 'i', 'j'),
            ('a', 'b', 'c', 'de', 'f', 'g', 'h', 'i', 'j'),
            ('a', 'b', 'cd', 'e', 'f', 'g', 'h', 'i', 'j'),
            ('a', 'bc', 'd', 'e', 'f', 'g', 'h', 'i', 'j'),
            ('ab', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'),
        ])
        self.assertEqual(list(compositions(2, 'a')), [])
        self.assertEqual(list(strjoin(compositions(2, ['swedbank', 'lizingas', 'uab']))), [
            ('swedbank', 'lizingas uab'),
            ('swedbank lizingas', 'uab'),
        ])
        self.assertEqual(list(strjoin(compositions(1, ['swedbank', 'lizingas', 'uab']))), [
            ('swedbank lizingas uab',),
        ])
