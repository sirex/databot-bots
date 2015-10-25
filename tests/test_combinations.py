import unittest

from botlib.combinations import combinations, _combinations, strjoin


class TokenizerTests(unittest.TestCase):

    def test_permute(self):
        self.assertEqual(list(_combinations(2, 5)), [
            (1,),  # a bcde
            (2,),  # ab cde
            (3,),  # abc de
            (4,),  # abcd e
        ])

        self.assertEqual(list(_combinations(2, 2)), [
            (1,),  # a b
        ])

        self.assertEqual(list(_combinations(3, 5)), [
            (1, 2),  # a b cde
            (1, 3),  # a bc de
            (1, 4),  # a bcd e
            (2, 3),  # ab c de
            (2, 4),  # ab cd e
            (3, 4),  # abc d e
        ])

        self.assertEqual(list(_combinations(4, 5)), [
            (1, 2, 3),  # a b c de
            (1, 2, 4),  # a b cd e
            (1, 3, 4),  # a bc d e
            (2, 3, 4),  # ab c d e
        ])

        self.assertEqual(list(_combinations(5, 6)), [
            (1, 2, 3, 4),  # a b c d ef
            (1, 2, 3, 5),  # a b c de f
            (1, 2, 4, 5),  # a b cd e f
            (1, 3, 4, 5),  # a bc d e f
            (2, 3, 4, 5),  # ab c d e f
        ])

        self.assertEqual(list(_combinations(5, 7)), [
            (1, 2, 3, 4),  # a b c d efg
            (1, 2, 3, 5),  # a b c de fg
            (1, 2, 3, 6),  # a b c def g
            (1, 2, 4, 6),  # a b cd ef g
            (1, 2, 5, 6),  # a b cde f g
            (1, 3, 5, 6),  # a bc de f g
            (1, 4, 5, 6),  # a bcd e f g
            (2, 3, 4, 5),  # ab c d e fg
            (2, 3, 4, 6),  # ab c d ef g
            (2, 3, 5, 6),  # ab c de f g
            (2, 4, 5, 6),  # ab cd e f g
            (3, 4, 5, 6),  # abc d e f g
        ])

    def test_tokenizer(self):
        self.maxDiff = None

        self.assertEqual(list(combinations(1, 'ab')), [
            ('ab',),
        ])
        self.assertEqual(list(combinations(2, 'ab')), [
            ('a', 'b'),
        ])
        self.assertEqual(list(combinations(2, 'abc')), [
            ('a', 'bc'),
            ('ab', 'c'),
        ])
        self.assertEqual(list(combinations(2, 'abcd')), [
            ('a', 'bcd'),
            ('ab', 'cd'),
            ('abc', 'd'),
        ])
        self.assertEqual(list(combinations(3, 'abcd')), [
            ('a', 'b', 'cd'),
            ('a', 'bc', 'd'),
            ('ab', 'c', 'd'),
        ])
        self.assertEqual(list(combinations(3, 'abcde')), [
            ('a', 'b', 'cde'),
            ('a', 'bc', 'de'),
            ('a', 'bcd', 'e'),
            ('ab', 'c', 'de'),
            ('ab', 'cd', 'e'),
            ('abc', 'd', 'e'),
        ])
        self.assertEqual(list(combinations(2, 'abcdefghijklmn')), [
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
        self.assertEqual(list(combinations(9, 'abcdefghij')), [
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
        self.assertEqual(list(combinations(2, 'a')), [])
        self.assertEqual(list(strjoin(combinations(2, ['swedbank', 'lizingas', 'uab']))), [
            ('swedbank', 'lizingas uab'),
            ('swedbank lizingas', 'uab'),
        ])
        self.assertEqual(list(strjoin(combinations(1, ['swedbank', 'lizingas', 'uab']))), [
            ('swedbank lizingas uab',),
        ])
