import unittest

from board_generation import get_ident


class GetIdentTest(unittest.TestCase):
	
	def test_get_ident(self):
		self.assertEqual(get_ident(1), 1)
		self.assertEqual(get_ident('1'), 1)
		self.assertEqual(get_ident([1]), 1)
		self.assertEqual(get_ident(['1']), 1)

		self.assertEqual(get_ident(1,2), (1,2))
		self.assertEqual(get_ident([1,2]), (1,2))
		self.assertEqual(get_ident('1_2'), (1,2))

		self.assertEqual(get_ident('1_2__3_4'), ((1,2), (3,4)))
		self.assertEqual(get_ident([[1,2], [3,4]]), ((1,2), (3,4)))

if __name__ == '__main__':
	unittest.main()