import re
import pathlib
import collections
import argparse
import itertools
import gramtool

from databot.commands import CommandsManager, Command
from botlib.combinations import combinations, strjoin

pattern_re = re.compile(r'({[^}]+})', re.UNICODE)
norm_re = re.compile(r'\W+', re.UNICODE)


FLAGS = {
    'title': str.title,
    'lemma': lambda v: (gramtool.get_lemma(v) or v),
    'genitive': lambda v: (gramtool.change_form(v, case='genitive') or v),
}


def norm(value):
    return norm_re.sub(' ', value).strip().lower()


class IndexFinder(object):

    def __init__(self, index, debug_info=None):
        self.index = index
        self.index = self.create_index(index)
        self.aliases, self.patterns = self.create_aliases(index, debug_info)

    def create_index(self, index):
        result = {}
        for name, data in index.items():
            result[name] = {norm(value): (key, value) for key, value in data['index']}
        return result

    def create_aliases(self, index, debug_info=None):
        index_aliases = collections.defaultdict(dict)
        index_patterns = collections.defaultdict(list)
        for name, data in index.items():
            for i, (choice, aliases) in enumerate(data['aliases']):
                patterns = []
                for j, alias in enumerate(aliases):
                    if '{' in alias:
                        try:
                            _patterns = self.parse_patterns(alias)
                        except re.error as e:
                            raise ValueError('\n'.join([
                                "Error while parsing %r index alias:" % name,
                                "  %r <- %r" % (choice, alias),
                                "%s" % e,
                            ]))
                        else:
                            patterns.append(_patterns)

                        if debug_info is not None:
                            for pattern in _patterns:
                                if isinstance(pattern, tuple) and pattern[0] not in index:
                                    filename, _, linenos = debug_info[name]['aliases'][i]
                                    lineno = linenos[j]
                                    raise ValueError('\n'.join([
                                        "Error while parsing %s:%d:" % (filename, lineno),
                                        "  %s" % alias,
                                        "Specified index '%s' does not exists." % pattern[0],
                                    ]))
                    else:
                        index_aliases[name][norm(alias)] = choice
                if patterns:
                    index_patterns[name].append((self.parse_patterns(choice), patterns))
        return index_aliases, index_patterns

    def parse_expr(self, expr):
        name, flags = expr.split(':', 1) if ':' in expr else (expr, '')
        flags = tuple(filter(None, map(str.strip, flags.split(','))))
        for flag in flags:
            if flag not in FLAGS:
                raise ValueError("Unknown flag '%s' in '%s' expression." % (flag, expr))
        return name, flags

    def parse_patterns(self, value):
        result = []
        for token in pattern_re.split(value):
            token = token
            if token.startswith('{'):
                name, flags = self.parse_expr(token[1:-1])
                name = int(name) if name.isnumeric() else name
                result.append((name, flags))
            elif token:
                result.append(token)
        return result

    def check_groups(self, match):
        for name, value in match.groupdict().items():
            if value not in self.index[name]:
                return False
        return True

    def pattern_finder(self, patterns, value, stack=None):
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
        stack = stack or set()

        for comb in strjoin(combinations(n_patterns, value)):
            skip = False

            # First check all raw strings, if at least one raw string does not match, skip.
            for i, (token, pattern) in enumerate(zip(comb, patterns)):
                if isinstance(pattern, str):
                    pattern = pattern.strip()
                    if token == pattern:
                        choices[i].append(token)
                    else:
                        skip = True
                        break
            if skip:
                continue

            # Find all indexes.
            for i, (token, pattern) in enumerate(zip(comb, patterns)):
                if isinstance(pattern, tuple):
                    appended = False
                    name, flags = pattern
                    token = self.handle_flags(token, flags)
                    if (name, token) not in stack:
                        for item in self.find(name, token, stack | {(name, token)}):
                            choices[i].append(item)
                            appended = True
                    if not appended:
                        break

        # Finally generate all possible combinations from found indexes and matching raw strings.
        for option in itertools.product(*choices):
            yield [(k, v) for k, v in zip(patterns, option) if isinstance(k, tuple)]

    def pattern_to_str(self, pattern):
        result = []
        for group in pattern:
            if isinstance(group, tuple):
                name, flags = group
                expr = '%s:%s' % (name, ','.join(flags)) if flags else name
                result.append('{%s}' % expr)
            else:
                result.append(group)
        return ''.join(result)

    def replace(self, groups, replacement):
        args = []
        kwargs = {}
        for (name, flags), (id, value, index, source) in groups:
            args.append(value)
            kwargs[name] = value

        result = []
        for token in replacement:
            if isinstance(token, tuple):
                name, flags = token
                if isinstance(name, int):
                    value = args[name]
                else:
                    value = kwargs[name]
                value = self.handle_flags(value, flags)
                result.append(value)
            else:
                result.append(token)

        return ''.join(result)

    def handle_flags(self, value, flags):
        for flag in flags:
            value = FLAGS[flag](value)
        return value

    def find(self, name, value, stack=None):
        idx = self.index[name]
        value = norm(value)
        stack = stack or set()

        if value in idx:
            yield idx[value] + (name, 'index',)

        if value in self.aliases[name]:
            _value = self.aliases[name][value]
            yield idx.get(norm(_value), (None, _value)) + (name, 'alias',)

        value = value.split()
        for replacement, patterns in self.patterns[name]:
            for pattern in patterns:
                for groups in self.pattern_finder(pattern, value, stack):
                    if replacement == ['(extends)']:
                        (((_name, flags), (id, _value, _index, _source)),) = groups
                        yield (id, _value, _index, 'extends')
                    else:
                        _value = self.replace(groups, replacement)
                        yield idx.get(norm(_value), (None, _value)) + (name, 'pattern',)


def load_index(index):
    result = {}
    debug_info = {}
    index = index if isinstance(index, pathlib.Path) else pathlib.Path(index)
    for path in index.iterdir():
        if not path.is_dir():
            continue

        result[path.name] = {'index': [], 'aliases': []}
        debug_info[path.name] = {'aliases': []}
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
                for i, line in enumerate(f, 1):
                    line = line.rstrip()
                    if not line:
                        continue
                    if line.startswith(' '):
                        aliases.append((i, line.strip()))
                    else:
                        if target:
                            line_numbers, aliases = zip(*aliases) if aliases else ([], [])
                            result[path.name]['aliases'].append((target, list(aliases)))
                            debug_info[path.name]['aliases'][-1][2].extend(line_numbers)
                        target, aliases = line, []
                        debug_info[path.name]['aliases'].append((str(path / 'aliases.txt'), i, []))
                if target:
                    line_numbers, aliases = zip(*aliases)
                    result[path.name]['aliases'].append((target, list(aliases)))
                    debug_info[path.name]['aliases'][-1][2].extend(line_numbers)

    return result, debug_info


class UpdateCommand(Command):

    def run(self, args):
        index = pathlib.Path(args.index_path)
        finder = IndexFinder(*load_index(index))
        for path in index.iterdir():
            if not path.is_dir():
                continue

            if (path / 'missing.txt').exists():
                print("Update %r index:" % path.name)
                missing = set()
                with (path / 'missing.txt').open() as f:
                    for line in f:
                        found = False
                        line = line.strip()
                        print('  %s' % line)
                        for id, value, name, source in finder.find(path.name, line):
                            found = True
                            print('      - %r, %r, %s, %s' % (id, value, name, source))
                        if not found:
                            missing.add(line)
                        else:
                            print()
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
