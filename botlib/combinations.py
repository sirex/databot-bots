def combination_states(n, s):
    state = list(range(1, n))
    final = list(range(s - n + 1, s))

    yield tuple(state)

    while state[0] < final[0]:
        for i in range(n - 2, -1, -1):
            if state[i] < final[i]:
                state[i] += 1
                if i == 0:
                    state = list(range(state[0], n + state[0] - 1))
                yield tuple(state)
                break


def combinations(n, tokens):
    if n == 1:
        yield (tokens,)

    if n > 1:
        c = len(tokens)
        for s in combination_states(n, len(tokens)):
            yield tuple([tokens[i:j] for i, j in zip((0,) + s, s + (c,))])
