import traits
  
  
  

def integer_power(x, n, one=1):
    # http://c2.com/cgi/wiki?IntegerPowerAlgorithm
    assert isinstance(n, int)

    if n < 0:
        raise RuntimeError, "the integer power algorithm does not work for negative numbers"
      
    aux = one
  
    while n > 0:
        if n & 1:
            aux *= x
            if n == 1:
                return aux
        x = x * x
        n //= 2
  
  
  
def gcd(q, r):
    return extended_euclidean(q, r)[0]




def extended_euclidean(q, r):
    """Return a tuple (p, a, b) such that p = aq + br, 
    where p is the greatest common divisor.
    """

    # see [Davenport], Appendix, p. 214

    t = traits.common_traits(q, r)
    
    if t.norm(q) < t.norm(r):
        p, a, b = extended_euclidean(r, q)
        return p, b, a
  
    Q = 1, 0
    R = 0, 1
  
    while r:
        quot, t = divmod(q, r)
        T = Q[0] - quot*R[0], Q[1] - quot*R[1]
        q, r = r, t
        Q, R = R, T
  
    return q, Q[0], Q[1]
  
  
  
  
if __name__ == "__main__":
    import integer
    q = integer.Integer(14)
    r = integer.Integer(22)
    gcd, a, b = extended_euclidean(q, r)
    print gcd, "=", a, "*", q, "+", b, "*", r
    print a*q + b*r
