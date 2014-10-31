class SizeError(RuntimeError):
    pass

class BoolFunc:
    def __init__(self):
        raise NotImplementedError()

    def __rshift__(self, func):
        if not isinstance(func, BoolFunc):
            raise ValueError('Not a boolean function')
        if isinstance(func, Seq):
            return func.__lshift__(self)
        else:
            return Seq([self, func])

    def __lshift__(self, func):
        if not isinstance(func, BoolFunc):
            raise ValueError('Not a boolean function')
        if isinstance(func, Seq):
            return func.__rshift__(self)
        else:
            return Seq([func, self])

    def __add__(self, func):
        if not isinstance(func, BoolFunc):
            raise ValueError('Not a boolean function')
        if isinstance(func, Cat):
            return Cat([self] + func._funcs)
        else:
            return Cat([self, func])

    def size(self, hint=None):
        if hint is not None and hint != self._size:
            raise SizeError(hint - self._size)
        return self._size


class Seq(BoolFunc):
    def __init__(self, seq=None):
        self._seq = seq or []

    def __rshift__(self, func):
        if not isinstance(func, BoolFunc):
            raise ValueError('Not a boolean function')
        if isinstance(func, Seq):
            return Seq(self._seq + func._seq)
        else:
            return Seq(self._seq + [func])

    def __lshift__(self, func):
        if not isinstance(func, BoolFunc):
            raise ValueError('Not a boolean function')
        if isinstance(func, Seq):
            return Seq(func._seq + self._seq)
        else:
            return Seq([func] + self._seq)

    def size(self, hint=None):
        s = hint
        for f in self._seq:
            s2 = f.size(hint=s)
            if s is None:
                s = s2
            elif s != s2:
                raise SizeError(s - s2)
        if hint is None and s is not None:
            return self.size(hint=s)
        else:
            return s

    def __str__(self):
        return '[%s]' % ', '.join(map(str, self._seq))

class Cat(BoolFunc):
    def __init__(self, funcs=None):
        self._funcs = funcs or []

    def size(self, hint=None):
        sizes = [f.size() for f in self._funcs]
        if hint is not None:
            n = sizes.count(None)
            if n > 2:
                raise SizeError()
            elif n == 1:
                i = sizes.index(None)
                s = sum(sizes[:i]) + sum(sizes[i+1:])
                sizes[i] = self._funcs.size(hint=hint-s)
                return hint
            s = sum(sizes)
            if hint != s:
                raise SizeError(hint - s)
            else:
                return hint
                
        return sum(sizes)

    def __add__(self, func):
        if not isinstance(func, BoolFunc):
            raise ValueError('Not a boolean function')
        if isinstance(func, Cat):
            return Cat(self._funcs + func._funcs)
        else:
            return Cat(self._funcs + [func])        

    def __str__(self):
        return ' ++ '.join(map(str, self._funcs))
        

class Const(BoolFunc):
    def __init__(self, const):
        if isinstance(const, bytes):
            self._const = const
        elif isinstance(const, str):
            self._const = const.encode()
        else:
            raise ValueError('Not a byte buffer')
        self._size = len(self._const) * 8

    def __str__(self):
        return 'const %s' % ''.join('{:02x}'.format(b) for b in self._const)

class Sbox(BoolFunc):
    def __init__(self, table):
        try:
            size = len(table)
        except:
            raise ValueError('Not a substitution table')
        self._size = 0
        while size > 1:
            if size & 1:
                raise ValueError('Not a power of two')
            self._size += 1
            size >>= 1
        self._table = table

    def __str__(self):
        return 'sbox [...]'

class Perm(BoolFunc):
    def __init__(self, perm, block=None):
        try:
            self._size = len(perm)
        except:
            raise ValueError('Not a permutation table')
        assert(all(isinstance(i, int) for i in perm))
        self._block = block
        self._perm = perm

    def size(self, hint=None):
        if hint is not None:
            if self._block is None:
                if hint % self._size == 0:
                    self._block = hint // self._size
                    return hint
                else:
                    raise SizeError(hint % self._size)
            elif self._block * self._size != hint:
                raise SizeError(hint - self._block * self._size)
            else:
                return hint
        elif self._block is None:
            return None
        else:
            return self._size * self._block

    def __str__(self):
        return 'perm %s' % str(self._perm)

class Slice(BoolFunc):
    def __init__(self, start, end):
        if not (isinstance(start, int) and isinstance(end, int) and end >= start):
            raise ValueError('Invalid slice bounds')
        self._start = start
        self._end = end

    def size(self, hint=None):
        s = self._end - self._start
        if hint is not None and hint != s:
            raise SizeError(hint - s)
        return s

    def __str__(self):
        return "[%d:%d]" % (self._start, self._end)

class Map(BoolFunc):
    def __init__(self, func, blocks=None):
        if not isinstance(func, BoolFunc):
            raise ValueError('Not a boolean function')
        self._blocks = blocks
        self._func = func

    def size(self, hint=None):
        if hint is not None:
            if self._blocks is None:
                s = self._func.size()
                if hint % s == 0:
                    self._blocks = hint // s
                    return hint
                else:
                    raise SizeError(hint % s)
            elif hint % self._blocks != 0:
                raise SizeError(hint % self._blocks)
            else:
                s = hint // self._blocks
                assert(self._func.size(s) == s)
                return hint
        elif self._blocks is None:
            return None
        else:
            return self._func.size() * self._blocks

    def __str__(self):
        return 'map %s' % str(self._func)

class BinOp(BoolFunc):
    def __init__(self, func, trunc=None):
        if not isinstance(func, BoolFunc):
            raise ValueError('Not a boolean function')
        self._func = func
        self._trunc = trunc
        
    def size(self, hint=None):
        if self._trunc is None:
            return self._func.size(hint)
        elif hint is None:
            return self._func.size(self._trunc)
        elif hint != self._trunc:
            raise SizeError(hint - self._trunc)
        else:
            return hint

    def __str__(self):
        return '%s %s' % (self._op, str(self._func))

class XOR(BinOp):
    _op = '^'

class ModMul(BinOp):
    _op = '*'

class ModAdd(BinOp):
    _op = '+'
