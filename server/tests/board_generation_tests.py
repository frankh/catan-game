import unittest

from board_generation import get_ident, generate_board


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

class BoardGenTest(unittest.TestCase):

	def setUp(self):
		self.board = generate_board()

	def test_hex_count(self):
		self.assertEqual(len(self.board.land_hexes), 19)
		
	def test_vert_count(self):
		self.assertEqual(len(self.board.vertices), 54)
		
	def test_path_count(self):
		self.assertEqual(len(self.board.paths), 72)

	def test_verts_unbuilt(self):
		for v in self.board.vertices:
			self.assertTrue(v.is_free())

if __name__ == '__main__':
	unittest.main()
