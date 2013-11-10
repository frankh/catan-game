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
#
class BoardGenTest(unittest.TestCase):
	def setUp(self):
		self.board = generate_board()

	def test_nonexist(self):
		with self.assertRaises(Exception):
			self.board.Hex(123)

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

		def max_path_hex(p):
			def max_land_hex(v):
				return max(h.id for h in v.hexes if not h.is_sea)
			return max(max_land_hex(v) for v in p.verts)

		self.assertEqual(path_1.next_coastal_path, self.board.Path.get(
			coast_1, coast_3))

		num_coastal_paths = len([p for p in self.board.paths if p.is_coastal])

		cur_path = path_1
		paths = []
		# Do a loop, we should come back to the start
		for unused in range(num_coastal_paths):
			cur_path = cur_path.next_coastal_path
			
			paths.append(cur_path)
			# All next_coastal_paths should be coastal
			self.assertTrue(cur_path.is_coastal)

		self.assertEqual(cur_path, path_1)
		self.assertEqual(len(paths), len(set(paths)))

	def test_validators(self):
		import board_validators
		import itertools
		from inspect import getmembers, isfunction

		validators_list = [name for (name, value) in getmembers(board_validators) if isfunction(value)]

		for i in range(len(validators_list)+1):
			for comb in itertools.combinations(validators_list, i):
				import sys
				sys.stdout.flush()
				generate_board(validators=comb)


if __name__ == '__main__':
	unittest.main()
