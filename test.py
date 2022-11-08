import unittest

if __name__ == '__main__':
	tests = unittest.defaultTestLoader.discover(start_dir='', pattern='*_test.py')
	unittest.TextTestRunner().run(tests)
