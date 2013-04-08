import unittest

from game import Game, Player

class TestConnection(object):
	def on_message(self, message):
		pass

	def write_message(self, message):
		pass

class TestGame(Game):
	def __init__(self):
		super().__init__()
		self.max_players = 1

class GameTest(unittest.TestCase):
	def setUp(self):
		self.game = TestGame()
		self.player = Player(TestConnection(), 'test_player', self.game)

	def test_started(self):
		self.assertFalse(self.game.started)
		self.game.add_player(self.player)
		self.assertFalse(self.game.started)

		self.game.set_ready(self.player)
		self.assertTrue(self.game.started)

	def runTest(self):
		self.test_started()

if __name__ == '__main__':
	unittest.main()