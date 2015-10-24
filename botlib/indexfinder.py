import re
import pathlib
import collections

pattern_re = re.compile(r'{[^}]+}', re.UNICODE)


class IndexFinder(object):

    def __init__(self, index):
        self.index = index
        self.index = self.create_index(index)
        self.aliases, self.patterns = self.create_aliases(index)

    def create_index(self, index):
        result = {}
        for name, data in index.items():
            result[name] = {value: key for key, value in data['index']}
        return result

    def create_aliases(self, index):
        index_aliases = collections.defaultdict(dict)
        index_patterns = collections.defaultdict(list)
        for name, data in index.items():
            for choice, aliases in data['aliases']:
                patterns = []
                for alias in aliases:
                    if '{' in alias:
                        patterns.append(self.create_regex(alias))
                    else:
                        index_aliases[name][alias] = choice
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
        return re.compile('^%s$' % pattern, re.UNICODE)

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

        if value in idx:
            yield idx[value], value

        if value in self.aliases[name]:
            _value = self.aliases[name][value]
            yield idx.get(_value), _value

        for replacement, patterns in self.patterns[name]:
            for regex in patterns:
                match = regex.search(value)
                if match and self.check_groups(match):
                    _value = match.expand(replacement)
                    yield idx.get(_value), _value


def load_index(path):
    result = {}
    path = pathlib.Path(path)
    for index_path in path.iterdir():
        result[index_path.name] = {'index': [], 'aliases': []}
        if (index_path / 'choices.txt').exists():
            with (index_path / 'choices.txt').open() as f:
                for line in f:
                    line = line.strip()
                    id, name = line.split(',', 1)
                    result[index_path.name]['index'].append((int(id), name.strip()))
        if (index_path / 'aliases.txt').exists():
            with (index_path / 'aliases.txt').open() as f:
                target, aliases = None, []
                for line in f:
                    line = line.rstrip()
                    if not line:
                        continue
                    if line.startswith(' '):
                        aliases.append(line.strip())
                    else:
                        if target:
                            result[index_path.name]['aliases'].append((target, aliases))
                        target, aliases = line, []
                if target:
                    result[index_path.name]['aliases'].append((target, aliases))
    return result
