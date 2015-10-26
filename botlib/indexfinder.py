import re
import pathlib
import collections
import argparse
import itertools

from databot.commands import CommandsManager, Command
from botlib.combinations import combinations, strjoin

pattern_re = re.compile(r'({[^}]+})', re.UNICODE)
norm_re = re.compile(r'\W+', re.UNICODE)


def norm(value):
    return norm_re.sub(' ', value).strip().lower()


class IndexFinder(object):

    def __init__(self, index):
        self.index = index
        self.index = self.create_index(index)
        self.aliases, self.patterns = self.create_aliases(index)

    def create_index(self, index):
        result = {}
        for name, data in index.items():
            result[name] = {norm(value): (key, value) for key, value in data['index']}
        return result

    def create_aliases(self, index):
        index_aliases = collections.defaultdict(dict)
        index_patterns = collections.defaultdict(list)
        for name, data in index.items():
            for choice, aliases in data['aliases']:
                patterns = []
                for alias in aliases:
                    if '{' in alias:
                        try:
                            patterns.append(self.parse_patterns(alias))
                        except re.error as e:
                            raise ValueError('\n'.join([
                                "Error while parsing %r index alias:" % name,
                                "  %r <- %r" % (choice, alias),
                                "%s" % e,
                            ]))
                    else:
                        index_aliases[name][norm(alias)] = choice
                if patterns:
                    index_patterns[name].append((choice, patterns))
        return index_aliases, index_patterns

    def parse_expr(self, expr):
        name, flags = expr.split(':', 1) if ':' in expr else (expr, '')
        flags = tuple(filter(None, map(str.strip, flags.split(','))))
        return name, flags

    def parse_patterns(self, value):
        result = []
        for token in pattern_re.split(value):
            token = token.strip()
            if token.startswith('{'):
                name, flags = self.parse_expr(token[1:-1])
                result.append((name, flags))
            elif token:
                result.append(token)
        return result

    def check_groups(self, match):
        for name, value in match.groupdict().items():
            if value not in self.index[name]:
                return False
        return True

    def pattern_finder(self, patterns, value):
        """Search for all possible matches for given pattern and value.

        How does this work.

        For example you have these indexes defined:

            company-type/
                aliases.txt:
                    UAB
                        Uždaroji akcinė bendrovė
                    IĮ
                        Individuali įmonė
                choices.txt:
                    1,UAB
                    2,IĮ
            company/
                aliases.txt:
                    {company}
                        {company-type} {company}
                    Programuotojų artelė
                        Programmers of Vilnius
                choices.txt:
                    1,Programuotojų artelė

        Then you call:

            pattern_finder([('company-type', ()), ('company', ())], 'uždaroji akcinė bendrovė programmers of vilnius')

        Finder will collect all posible combinations for 'uždaroji akcinė bendrovė programmers of vilnius' and two
        patterns:

            ('uždaroji', 'akcinė bendrovė programmers of vilnius')
            ('uždaroji akcinė', 'bendrovė programmers of vilnius')
            ('uždaroji akcinė bendrovė', 'programmers of vilnius')
            ('uždaroji akcinė bendrovė programmers', 'of vilnius')
            ('uždaroji akcinė bendrovė programmers of', 'vilnius')

        Then for each conbination you collect possible pattern choices, first for raw strings that match. In our case
        there is not raw strings, only two patterns, so nothing will happen here.

        Then collect all possible choices for given patterns, by searching index specified in each pattern for value
        from generated combinations. In our case, only 'uždaroji akcinė bendrovė' will give 'uab' and 'programmers of
        vilnius' will give 'programuotojų artelė', all other combination values will not return any results.

            [['uab'], ['programuotojų artelė']]

        And finally generate all possible combinations:

            {'company-type': 'uab', 'company': 'programuotojų artelė'}

        Arguments:
        - patterns: list, example: [('bank', ()), 'bankas']
        - value: str, normalized value (see norm), example: 'dnb bankas'

        Returns generator with all possible values.
        """
        n_patterns = len(patterns)
        choices = [[] for i in range(n_patterns)]

        for comb in strjoin(combinations(n_patterns, value)):
            skip = False

            # First check all raw strings, if at least one raw string does not match, skip.
            for i, (token, pattern) in enumerate(zip(comb, patterns)):
                if token == pattern:
                    choices[i].append(token)
                elif isinstance(pattern, str):
                    skip = True
                    break
            if skip:
                continue

            # Find all indexes.
            for i, (token, pattern) in enumerate(zip(comb, patterns)):
                print(token, pattern)
                if isinstance(pattern, tuple):
                    appended = False
                    name, flags = pattern
                    for id, _value in self.find(name, token):
                        choices[i].append(norm(_value))
                        appended = True
                    if not appended:
                        break

        # Finally generate all possible combinations from found indexes and matching raw strings.
        for option in itertools.product(*choices):
            yield {k[0]: v for k, v in zip(patterns, option) if isinstance(k, tuple)}

    def find(self, name, value):
        idx = self.index[name]
        value = norm(value)

        if value in idx:
            yield idx[value]

        if value in self.aliases[name]:
            _value = self.aliases[name][value]
            yield idx.get(norm(_value), (None, _value))

        value = value.split()
        for replacement, patterns in self.patterns[name]:
            for pattern in patterns:
                for groups in self.pattern_finder(patterns, value):
                    _value = replacement.format(**groups)
                    yield idx.get(norm(_value), (None, _value))


def load_index(index):
    result = {}
    index = index if isinstance(index, pathlib.Path) else pathlib.Path(index)
    for path in index.iterdir():
        result[path.name] = {'index': [], 'aliases': []}
        if (path / 'choices.txt').exists():
            with (path / 'choices.txt').open() as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    try:
                        id, name = line.split(',', 1)
                    except ValueError as e:
                        raise ValueError('\n'.join([
                            "Error while parsing %s:%d:" % ((path / 'choices.txt'), i),
                            "  %s" % line,
                            "%s" % e,
                        ]))
                    result[path.name]['index'].append((int(id), name.strip()))
        if (path / 'aliases.txt').exists():
            with (path / 'aliases.txt').open() as f:
                target, aliases = None, []
                for line in f:
                    line = line.rstrip()
                    if not line:
                        continue
                    if line.startswith(' '):
                        aliases.append(line.strip())
                    else:
                        if target:
                            result[path.name]['aliases'].append((target, aliases))
                        target, aliases = line, []
                if target:
                    result[path.name]['aliases'].append((target, aliases))
    return result


class UpdateCommand(Command):

    def run(self, args):
        index = pathlib.Path(args.index_path)
        finder = IndexFinder(load_index(index))
        for path in index.iterdir():
            if (path / 'missing.txt').exists():
                print("Update %r index:" % path.name)
                missing = set()
                with (path / 'missing.txt').open() as f:
                    for line in f:
                        line = line.strip()
                        result = list(finder.find(path.name, line))
                        if result:
                            print('  %r -> %r' % (line, result))
                        else:
                            missing.add(line)
                # with (path / 'missing.txt').open('w') as f:
                #     for line in sorted(missing):
                #         f.write('%s\n' % line)
        print('Done.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=str, default='index', dest='index_path', help="Path to index directory.")

    sps = parser.add_subparsers(dest='command')

    cmgr = CommandsManager(None, sps)
    cmgr.register('update', UpdateCommand)

    args = parser.parse_args()

    cmgr.run(args.command, args, default=None)
