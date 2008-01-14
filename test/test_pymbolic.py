import unittest




class TestPymbolic(unittest.TestCase):
    def test_expand(self):
        from pymbolic import var, expand

        x = var("x")
        u = (x+1)**5
        expand(u)

    def test_substitute(self):
        from pymbolic import parse, substitute, evaluate
        u = parse("5+x.min**2")
        xmin = parse("x.min")
        assert evaluate(substitute(u, {xmin:25})) == 630
            
if __name__ == '__main__':
    unittest.main()
