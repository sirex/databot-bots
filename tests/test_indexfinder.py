import unittest

from botlib.indexfinder import IndexFinder, load_index


class LoadIndexTests(unittest.TestCase):

    def test_load_index(self):
        self.maxDiff = None
        self.assertEqual(load_index('tests/fixtures/index'), {
            'bank': {
                'index': [
                    (1, 'danske'),
                    (2, 'dnb'),
                    (3, 'seb'),
                    (4, 'swedbank'),
                ],
                'aliases': [],
            },
            'company': {
                'index': [
                    (1, 'danske bankas'),
                    (2, 'dnb bankas'),
                    (3, 'seb bankas'),
                    (4, 'swedbank bankas'),
                ],
                'aliases': [
                    ('{bank} bankas', [
                        '{bank}',
                        '{bank} bank',
                        'bankas {bank}',
                        '{bank:genitive} lizingas',
                    ])
                ],
            },
        })


class IndexFinderTests(unittest.TestCase):

    def setUp(self):
        self.index = IndexFinder({})

    def assertIndex(self, index, value, result):
        self.assertEqual(list(self.index.find(index, value)), result)

    def test_create_regex(self):
        self.assertEqual(self.index.create_regex('bankas {company}').pattern, r'^bankas \b(?P<company>\w+)\b$')

    def test_create_replacement_template(self):
        self.assertEqual(self.index.create_replacement_template('bankas {company}'), r'bankas \g<company>')

    def test_parse_expr(self):
        self.assertEqual(self.index.parse_expr('company:genitive'), ('company', ['genitive']))

    def test_find(self):
        self.index = IndexFinder(load_index('tests/fixtures/index'))
        self.assertIndex('bank', 'unknown', [])
        self.assertIndex('bank', 'unknown', [])
        self.assertIndex('bank', 'seb', [(3, 'seb')])
        self.assertIndex('company', 'dnb bankas', [(2, 'dnb bankas')])
        self.assertIndex('company', 'dnb', [(2, 'dnb bankas')])
        self.assertIndex('company', 'danske bank', [(1, 'danske bankas')])
        self.assertIndex('company', 'bankas swedbank', [(4, 'swedbank bankas')])
        self.assertIndex('company', 'dnb lizingas', [(2, 'dnb bankas')])
