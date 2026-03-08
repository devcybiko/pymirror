def _add(t, d):
    """Increment each element of the tuple by the corresponding element in d."""
    return tuple(a + b for a, b in zip(t, d))


def _sub(t1, t2):
    """Calculate the difference between two tuples."""
    return tuple(a - b for a, b in zip(t1, t2))


def _scale(t1, s):
    return tuple(x * s for x in t1)


def _div(t1, t2):
    return tuple(x / y for x, y in zip(t1, t2))


def _mul(t1, t2):
    return tuple(x * y for x, y in zip(t1, t2))

def _norm(t1):
    ## take the norm of the tuple
    return sum(x * x for x in t1) ** 0.5

