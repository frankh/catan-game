import unittest

from utils import random_move

class RandomMoveTest(unittest.TestCase):
	def test_random_move(self):
		moves = [{}]

		self.assertIn(random_move(moves), moves)