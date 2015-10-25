import unittest

from botlib.combinations import combinations, combination_states


class TokenizerTests(unittest.TestCase):

    def test_permute(self):
        self.assertEqual(list(combination_states(2, 5)), [
            (1,),  # a bcde
            (2,),  # ab cde
            (3,),  # abc de
            (4,),  # abcd e
        ])

        self.assertEqual(list(combination_states(2, 2)), [
            (1,),  # a b
        ])

        self.assertEqual(list(combination_states(3, 5)), [
            (1, 2),  # a b cde
            (1, 3),  # a bc de
            (1, 4),  # a bcd e
            (2, 3),  # ab c de
            (2, 4),  # ab cd e
            (3, 4),  # abc d e
        ])

        self.assertEqual(list(combination_states(4, 5)), [
            (1, 2, 3),  # a b c de
            (1, 2, 4),  # a b cd e
            (1, 3, 4),  # a bc d e
            (2, 3, 4),  # ab c d e
        ])

        self.assertEqual(list(combination_states(5, 6)), [
            (1, 2, 3, 4),  # a b c d ef
            (1, 2, 3, 5),  # a b c de f
            (1, 2, 4, 5),  # a b cd e f
            (1, 3, 4, 5),  # a bc d e f
            (2, 3, 4, 5),  # ab c d e f
        ])

        self.assertEqual(list(combination_states(5, 7)), [
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
