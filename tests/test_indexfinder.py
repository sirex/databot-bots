import unittest

from botlib.indexfinder import IndexFinder, load_index


class LoadIndexTests(unittest.TestCase):

    def test_load_index(self):
        self.maxDiff = None
        data, debug_info = load_index('tests/fixtures/index')
        self.assertEqual(data, {
            'bank': {
                'index': [
                    (1, 'Danske'),
                    (2, 'DNB'),
                    (3, 'SEB'),
                    (4, 'Swedbank'),
                ],
                'aliases': [
                    ('{bank}', [
                        '{bank} bankas',
                        '{bank} bank',
                        'bankas {bank}',
                        '{bank:lemma} lizingas',
                    ]),
                ],
            },
            'company-type': {
                'index': [
                    (1, 'UAB'),
                    (2, 'IĮ'),
                ],
                'aliases': [
                    ('UAB', ['Uždaroji akcinė bendrovė']),
                    ('IĮ', ['Individuali įmonė']),
                ],
            },
            'company': {
                'index': [
                    (1, 'Danske bankas'),
                    (2, 'DNB bankas'),
                    (3, 'SEB bankas'),
                    (4, 'Swedbank bankas'),
                    (5, 'Programuotojų artelė'),
                ],
                'aliases': [
                    ('{bank} bankas', ['{bank}']),
                    ('{company}', ['{company-type} {company}']),
                    ('Programuotojų artelė', ['Programmers of Vilnius']),
                ],
            },
        })


class IndexFinderTests(unittest.TestCase):

    def setUp(self):
        self.index = IndexFinder({})

    def assertIndex(self, index, value, result):
        self.assertEqual(list(self.index.find(index, value)), result)

    def test_parse_patterns(self):
        self.assertEqual(self.index.parse_patterns('bankas {finance}'), ['bankas ', ('finance', ())])
        self.assertEqual(self.index.parse_patterns('{city:lemma}'), [('city', ('lemma',))])
        self.assertEqual(self.index.parse_patterns('(extends)'), ['(extends)'])

    def test_parse_expr(self):
        self.assertEqual(self.index.parse_expr('company'), ('company', ()))
        self.assertEqual(self.index.parse_expr('company:genitive'), ('company', ('genitive',)))

    def test_patterns(self):
        self.index = IndexFinder(*load_index('tests/fixtures/index'))
        pattern = [('company-type', ()), ('company', ())]
        value = 'uždaroji akcinė bendrovė programmers of vilnius'
        self.assertEqual(list(self.index.pattern_finder(pattern, value.split())), [
            [
                (('company-type', ()), (1, 'UAB', 'company-type', 'alias')),
                (('company', ()), (5, 'Programuotojų artelė', 'company', 'alias')),
            ],
        ])

    def test_replace(self):
        groups = [(('city', ('lemma',)), (None, 'Vilnius', 'city', 'extends'))]
        replacement = [('city', ('genitive', 'title')), ' filialas']
        self.assertEqual(self.index.replace(groups, replacement), 'Vilniaus filialas')

    def test_parse_and_replace(self):
        parse = self.index.parse_patterns
        groups = [(parse('{city:lemma}')[0], (None, 'Vilnius', 'city', 'extends'))]
        replacement = parse('{city:genitive,title} filialas')
        self.assertEqual(self.index.replace(groups, replacement), 'Vilniaus filialas')

    def test_find_from_index(self):
        self.index = IndexFinder({
            'a': {
                'index': [(1, 'x')],
                'aliases': [],
            },
        })
        self.assertIndex('a', 'x', [(1, 'x', 'a', 'index')])

    def test_find_from_alias(self):
        self.index = IndexFinder({
            'a': {
                'index': [(1, 'x')],
                'aliases': [('x', ['y'])],
            },
        })
        self.assertIndex('a', 'y', [(1, 'x', 'a', 'alias')])

    def test_find_from_alias_without_index(self):
        self.index = IndexFinder({
            'a': {
                'index': [],
                'aliases': [('x', ['y'])],
            },
        })
        self.assertIndex('a', 'y', [(None, 'x', 'a', 'alias')])

    def test_find_from_pattern(self):
        self.index = IndexFinder({
            'a': {
                'index': [(1, 'x')],
                'aliases': [('{a}', ['{a} y'])],
            },
        })
        self.assertIndex('a', 'x y', [(1, 'x', 'a', 'pattern')])

    def test_find_from_pattern_without_index(self):
        self.index = IndexFinder({
            'a': {
                'index': [],
                'aliases': [('{a}', ['{a} y'])],
            },
        })
        self.assertIndex('a', 'x y', [])

    def test_find_from_pattern_and_alias(self):
        self.index = IndexFinder({
            'a': {
                'index': [],
                'aliases': [
                    ('x', ['z']),
                    ('{a}', ['{a} y']),
                ],
            },
        })
        self.assertIndex('a', 'z y', [(None, 'x', 'a', 'pattern')])

    def test_find_from_positional_alias_target(self):
        self.index = IndexFinder({
            'a': {
                'index': [],
                'aliases': [
                    ('{0}', ['{b}']),
                ],
            },
            'b': {
                'index': [(1, 'x')],
                'aliases': [],
            },
        })
        self.assertIndex('a', 'x', [(None, 'x', 'a', 'pattern')])

    def test_extends(self):
        self.index = IndexFinder({
            'a': {
                'index': [],
                'aliases': [
                    ('(extends)', ['{b}']),
                ],
            },
            'b': {
                'index': [],
                'aliases': [
                    ('(extends)', ['{c}']),
                ],
            },
            'c': {
                'index': [],
                'aliases': [
                    ('(extends)', ['{d}']),
                ],
            },
            'd': {
                'index': [(1, 'x')],
                'aliases': [],
            },
        })
        self.assertIndex('a', 'x', [(1, 'x', 'd', 'extends')])

    def test_lemma(self):
        self.index = IndexFinder({
            'city': {
                'index': [(1, 'Vilnius')],
                'aliases': [
                    ('{city}', ['{city:lemma}']),
                ],
            },
        })
        self.assertIndex('city', 'Vilniaus', [(1, 'Vilnius', 'city', 'pattern')])
        self.assertIndex('city', 'Notacity', [])

    def test_change_form(self):
        self.index = IndexFinder({
            'surname': {
                'index': [(1, 'Graužinienė')],
                'aliases': [],
            },
            'enterprise': {
                'index': [],
                'aliases': [
                    ('{surname:genitive,title} IĮ', ['{surname:lemma} iį']),
                ],
            },
        })
        self.assertIndex('enterprise', 'Graužinienės IĮ', [(None, 'Graužinienės IĮ', 'enterprise', 'pattern')])

    def test_recursive_index(self):
        self.index = IndexFinder({
            'a': {
                'index': [],
                'aliases': [('{b}', ['{b}'])],
            },
            'b': {
                'index': [],
                'aliases': [('{a}', ['{a}'])],
            },
        })
        self.assertIndex('a', 'x', [])

    def test_siauliu_banko_lizingas(self):
        self.index = IndexFinder({
            'finance': {
                'index': [(1, 'Šiaulių bankas')],
                'aliases': [
                    ('{finance}', ['{finance:lemma} lizingas']),
                ],
            },
        })
        self.assertIndex('finance', 'ŠIAULIŲ BANKO LIZINGAS', [(1, 'Šiaulių bankas', 'finance', 'pattern')])

    def test_danske(self):
        self.index = IndexFinder(*load_index('tests/fixtures/index'))
        self.assertIndex('bank', 'danske bank', [(1, 'Danske', 'bank', 'pattern')])

    def test_find(self):
        self.index = IndexFinder(*load_index('tests/fixtures/index'))
        self.assertIndex('bank', 'unknown', [])
        self.assertIndex('bank', 'unknown', [])
        self.assertIndex('bank', 'dnb', [(2, 'DNB', 'bank', 'index')])
        self.assertIndex('bank', 'seb', [(3, 'SEB', 'bank', 'index')])
        self.assertIndex('bank', 'danske bank', [(1, 'Danske', 'bank', 'pattern')])
        self.assertIndex('company', 'dnb bankas', [
            (2, 'DNB bankas', 'company', 'index'),
            (2, 'DNB bankas', 'company', 'pattern'),
        ])
        self.assertIndex('company', 'dnb', [(2, 'DNB bankas', 'company', 'pattern')])
        self.assertIndex('company', 'danske bank', [(1, 'Danske bankas', 'company', 'pattern')])
        self.assertIndex('company', 'bankas swedbank', [(4, 'Swedbank bankas', 'company', 'pattern')])
        self.assertIndex('company', 'dnb lizingas', [(2, 'DNB bankas', 'company', 'pattern')])
