import operator
import pytools




class Vector:
    """An immutable sequence that you can compute with."""
    def __init__(self, *content):
        self._Content = content

    def __nonzero__(self):
        for i in self._Content:
            if i:
                return False
        return True

    def __len__(self):
        return len(self._Content)

    def __getitem__(self, index):
        return self._Content[index]

    def __neg__(self):
        return Vector(*tuple(-x for x in self))

    def __add__(self, other):
        if len(other) != len(self):
            raise ValueError, "can't add values of differing lengths"
        return Vector(*tuple(x+y for x, y in zip(self, other)))

    def __radd__(self, other):
        if len(other) != len(self):
            raise ValueError, "can't add values of differing lengths"
        return Vector(*tuple(y+x for x, y in zip(self, other)))

    def __sub__(self, other):
        if len(other) != len(self):
            raise ValueError, "can't subtract values of differing lengths"
        return Vector(*tuple(x-y for x, y in zip(self, other)))

    def __rsub__(self, other):
        if len(other) != len(self):
            raise ValueError, "can't subtract values of differing lengths"
        return Vector(*tuple(y-x for x, y in zip(self, other)))

    def __mul__(self, other):
        # vector-matrix
        try:
            if len(other.shape) == 2:
                h, w = other.shape
                return Vector(*tuple(
                    sum(self[i]*other[i,j] for i in range(h))
                    for j in range(w)))
        except AttributeError:
            pass
                
        try:
            # inner product (vector-vector)
            if len(other) != len(self):
                raise ValueError, "can't multiply values of differing lengths"
            return sum(x*y for x, y in zip(self, other))
        except TypeError:
            # vector-scalar
            return Vector(*tuple(x*other for x in self))

    def __rmul__(self, other):
        # matrix-vector
        try:
            if len(other.shape) == 2:
                h, w = other.shape
                return Vector(*tuple(
                    sum(other[i,j]*self[j] for j in range(w))
                    for i in range(h)))
        except AttributeError:
            pass

        try:
            # inner product (vector-vector)
            if len(other) != len(self):
                raise ValueError, "can't multiply values of differing lengths"
            return sum(y*x for x, y in zip(self, other))
        except TypeError:
            # scalar-vector
            return Vector(*tuple(other*x for x in self))

    def __div__(self, other):
        return Vector(*tuple(operator.div(x, other) for x in self))

    def __truediv__(self, other):
        return Vector(*tuple(operator.truediv(x, other) for x in self))

    def __floordiv__(self, other):
        return Vector(*tuple(x//other for x in self))

    def __str__(self):
        return "[%s]" % ", ".join(str(x) for x in self)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join(repr(x) for x in self))

    def __hash__(self):
        return hash(self._Content) ^ 0xaccfff2
        





class SparseVector(pytools.DictionaryWithDefault):
    def __init__(self):
        DictionaryWithDefault.__init__(self, lambda x: 0.)

    def add_to(self, other, factor = 1.):
        for key in self:
            other[key] += factor * self[key]

    def add_to_matrix_column(self, matrix, column, factor = 1.):
        for key in self:
            matrix[key, column] += factor * self[key]

    def add_to_matrix_row(self, matrix, row, factor = 1.):
        for key in self:
            matrix[row, key] += factor * self[key]

    def conjugate(self):
        result = SparseVector()
        for key in self:
            result[key] = (self[key]+0j).conjugate()
        return result

    def __radd__(self, other):
        result = other.copy()
        for key in self:
            result[key] += self[key]
        return result

    def __add__(self, other):
        result = other.copy()
        for key in self:
            result[key] += self[key]
        return result

    def __rsub__(self, other):
        result = other.copy()
        for key in self:
            result[key] -= self[key]
        return result

    def __sub__(self, other):
        result = other.copy()
        for key in self:
            result[key] = self[key] - result[key]
        return result

    def __mul__(self, other):
        result = SparseVector()
        for key in self:
            result[key] = other * self[key]
        return result

    def __rmul__(self, other):
        result = SparseVector()
        for key in self:
            result[key] = other * self[key]
        return result




if __name__ == "__main__":
    import pylinear.array as num
    A = num.array([[45,3],[17,4]])
    v = Vector(1,2,3)
    w = Vector(5,1,4)
    print v, w
    print w/3.
    print A.T*v - v*A

