import unittest

from board_generation import get_ident, generate_board, Sea


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

# Hex numbers start from top and spiral clockwise
#        __
#     __/1 \__
#  __/12\__/2 \__
# /11\__/13\__/3 \
# \__/18\__/14\__/
# /10\__/19\__/4 \
# \__/17\__/15\__/
# /9 \__/16\__/5 \
# \__/8 \__/6 \__/
#    \__/7 \__/
#       \__/

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

	def test_path_is_coastal(self):
		coast_1 = (1 , 12        , Sea(1 , 12))
		coast_2 = (12, Sea(1, 12), Sea(11, 12))
		coast_3 = (1 , Sea(1, 1 ), Sea(1 , 12))
		path_1 = self.board.Path.get(coast_1, coast_2)

		self.assertFalse(self.board.Path.get('1_2_13__2_13_14').is_coastal)
		self.assertTrue(path_1.is_coastal)

		self.assertEqual(path_1.next_coastal_path, self.board.Path.get(
			coast_1, coast_3))

if __name__ == '__main__':
	unittest.main()
