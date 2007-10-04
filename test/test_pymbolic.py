import unittest




class TestPymbolic(unittest.TestCase):
    def test_expand(self):
        from pymbolic import var, expand

        x = var("x")
        u = (x+1)**5
        print expand(u)

            
if __name__ == '__main__':
    unittest.main()
