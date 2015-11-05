from itertools import combinations


def compositions(k, tokens):
    """Generate all compositions of tokens with fixed number of terms k.

    Number of compositions for given k and tokens:

        len(list(compositions(k, tokens))) == binomial(len(tokens) - 2, k - 1)

    See: https://en.wikipedia.org/wiki/Composition_(combinatorics)

    """
    n = len(tokens)

    if 1 == k <= n:
        yield (tokens,)

    if 1 < k <= n:
        for s in combinations(range(1, len(tokens)), k - 1):
            yield tuple([tokens[i:j] for i, j in zip((0,) + s, s + (n,))])


def strjoin(items):
    for item in items:
        yield tuple(map(' '.join, item))
