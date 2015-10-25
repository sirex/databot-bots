import re
import pathlib
import collections
import argparse

from databot.commands import CommandsManager, Command

pattern_re = re.compile(r'{[^}]+}', re.UNICODE)
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
                            patterns.append(self.create_regex(alias))
                        except re.error as e:
                            raise ValueError('\n'.join([
                                "Error while parsing %r index alias:" % name,
                                "  %r <- %r" % (choice, alias),
                                "%s" % e,
                            ]))
                    else:
                        index_aliases[name][norm(alias)] = choice
                if patterns:
                    index_patterns[name].append((self.create_replacement_template(choice), patterns))
        return index_aliases, index_patterns

    def parse_expr(self, expr):
        name, flags = expr.split(':', 1) if ':' in expr else (expr, '')
        flags = flags.split(',')
        return name, flags

    def create_regex(self, value):
        pattern = value
        for place_holder in pattern_re.findall(value):
            name, flags = self.parse_expr(place_holder[1:-1])
            pattern = pattern.replace(place_holder, r'\b(?P<%s>\w+)\b' % name)
        return re.compile('^%s$' % pattern, re.UNICODE | re.IGNORECASE)

    def create_replacement_template(self, value):
        tempalte = value
        for place_holder in pattern_re.findall(value):
            name, flags = self.parse_expr(place_holder[1:-1])
            tempalte = tempalte.replace(place_holder, r'\g<%s>' % name)
        return tempalte

    def check_groups(self, match):
        for name, value in match.groupdict().items():
            if value not in self.index[name]:
                return False
        return True

    def find(self, name, value):
        idx = self.index[name]
        value = norm(value)

        if value in idx:
            yield idx[value]

        if value in self.aliases[name]:
            _value = self.aliases[name][value]
            yield idx.get(norm(_value), (None, _value))

        for replacement, patterns in self.patterns[name]:
            for regex in patterns:
                match = regex.search(value)
                if match:
                    for name, value in match.groupdict().items():
                        if value not in self.index[name]:
                            return False

                    _value = match.expand(replacement)
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
