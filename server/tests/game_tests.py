import unittest

import random
import json
from collections import Counter
from contextlib import contextmanager

from game import Game, Player
from utils import random_move, repeat
import const
import dice_gen

class TestDiceGen(dice_gen.NoRobberDiceGen):
	next = None

	def roll(self):
		if self.next is None:
			return super().roll()

		ret = self.next
		self.next = None
		return ret

class TestConnection(object):
	def __init__(self, game):
		self.moves = None
		self.trade_offer = None
		self.player = Player('token', 'test_player1', game)
		self.player.connection = self

	def on_message(self, message):
		pass

	def write_message(self, message):
		message = json.loads(message)

		if message['type'] == 'moves':
			self.moves = message['moves']
		if message['type'] == 'trade_offer':
			self.trade_offer = message['trade']

class TestGame(Game):
	def __init__(self, name, max_players=2):
		super().__init__(name=name)
		self.max_players = max_players
		self.dice_gen = TestDiceGen()

class PlayerTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.game = TestGame(name="test_game_2")

		cls.c1 = TestConnection(cls.game)
		cls.c2 = TestConnection(cls.game)
		cls.player1 = cls.c1.player
		cls.player2 = cls.c2.player

		cls.game.add_player(cls.player1)

	def test_cards_list(self):
		self.assertEqual(self.player1.cards_list, [])	

		self.player1.cards['wood'] = 3
		# Must increase action number to clear the per action cache.
		self.game.action_number += 1

		self.assertEqual(self.player1.cards_list, ['wood', 'wood', 'wood'])	

	@repeat(300)
	def test_cards_list_random(self):
		self.game.action_number += 1

		for res in const.resources:
			self.player1.cards[res] = random.randint(0, 5)

		self.assertEqual(sum(self.player1.cards.values()), len(self.player1.cards_list))

class GameTest(unittest.TestCase):
	@contextmanager
	def assert_moves(self, moves=1):
		action = self.game.action_number
		yield
		if moves > 0:
			self.assertLessEqual(action+moves, self.game.action_number)
		else:
			self.assertEqual(action, self.game.action_number)


	@classmethod
	def setUpClass(cls):
		cls.game = TestGame(name="test_game_1")

		cls.c1 = TestConnection(cls.game)
		cls.c2 = TestConnection(cls.game)
		cls.player1 = cls.c1.player
		cls.player2 = cls.c2.player

		cls.dice_gen = cls.game.dice_gen

	def test_1_started(self):
		self.assertFalse(self.game.started)
		# Add first player - shouldn't start
		self.game.add_player(self.player1)
		self.assertFalse(self.game.started)
		# Ready first player - shouldn't start
		self.game.set_ready(self.player1)
		self.assertFalse(self.game.started)
		# Add 2nd player - shouldn't start
		self.game.add_player(self.player2)
		self.assertFalse(self.game.started)
		# Ready 2nd player - should start
		self.game.set_ready(self.player2)
		self.assertTrue(self.game.started)

		self.assertTrue(self.c1.moves or self.c2.moves)

	def test_2_placement(self):
		conn = self.c1 if self.c1.moves else self.c2

		with self.assert_moves():
			self.game.recv_move(conn.player, random_move(conn.moves))
		# Make sure we built a building
		self.assertEqual(conn.player.num_buildings, 1)
		self.assertEqual(conn.player.longest_road, 0)

		with self.assert_moves():
			self.game.recv_move(conn.player, random_move(conn.moves))
		# Make sure we built a road
		self.assertEqual(conn.player.longest_road, 1)

		# This move should be invalid, make sure nothing changes
		with self.assert_moves(0):
			self.game.recv_move(conn.player, random_move(conn.moves))

		self.assertEqual(conn.player.num_buildings, 1)
		self.assertEqual(conn.player.longest_road, 1)

		conn.moves = None

	def test_3_placement2(self):
		conn = self.c1 if self.c1.moves else self.c2

		# Do all starting moves. Should build 2 houses and 2 roads
		with self.assert_moves(4):
			self.game.recv_move(conn.player, random_move(conn.moves))
			self.game.recv_move(conn.player, random_move(conn.moves))
			self.game.recv_move(conn.player, random_move(conn.moves))
			self.game.recv_move(conn.player, random_move(conn.moves))
		self.assertEqual(conn.player.num_buildings, 2)
		self.assertIn(conn.player.longest_road, (1,2))

		# Check no more valid moves
		with self.assert_moves(0):
			for i in range(20):
				self.game.recv_move(conn.player, random_move(conn.moves))

		conn.moves = None

	def test_4_cant_trade_yet(self):
		with self.assert_moves(0):
			self.game.recv_trade(self.player1, {
				'give': { 'ore': 1 },
				'want': { 'wood': 1 },
				'player_id': None,
				'turn': self.game.action_number,
			})

		self.assertFalse(self.c2.trade_offer)

	def test_5_finish_placement(self):
		conn = self.c1 if self.c1.moves else self.c2

		with self.assert_moves(2):
			self.game.recv_move(conn.player, random_move(conn.moves))
			self.game.recv_move(conn.player, random_move(conn.moves))
		self.assertEqual(conn.player.num_buildings, 2)
		self.assertIn(conn.player.longest_road, (1,2))

		for i in range(10):
			self.assertEqual(random_move(conn.moves)['type'], 'roll')

		with self.assert_moves():
			self.game.recv_move(conn.player, random_move(conn.moves))

	def test_6_can_trade(self):
		self.player1.cards['wood'] += 1
		self.player2.cards['wheat'] += 1

		self.game.recv_trade(self.player1, {
			'give': {'wood': 1},
			'want': {'ore': 4},
			'player_id': self.player2.id,
			'turn': self.game.action_number,
		})
		self.assertTrue(self.c2.trade_offer)

	def test_7_trade(self):
		self.player1.cards['wheat'] += 1
		self.player2.cards['ore'] += 1

		p1_cards = dict(self.player1.cards)
		p2_cards = dict(self.player2.cards)

		with self.assert_moves(1):
			self.game.recv_trade(self.player1, {
				'give': {'wheat': 1},
				'want': {'ore': 1},
				'player_id': self.player2.id,
				'turn': self.game.action_number,
			})
			self.game.recv_trade(self.player2, {
				'give': {'ore': 1},
				'want': {'wheat': 1},
				'player_id': self.player1.id,
				'turn': self.game.action_number,
			})

		self.assertEqual(self.player2.cards['wheat'], p2_cards['wheat']+1)
		self.assertEqual(self.player2.cards['ore'], p2_cards['ore']-1)
		self.assertEqual(self.player1.cards['ore'], p1_cards['ore']+1)
		self.assertEqual(self.player1.cards['wheat'], p1_cards['wheat']-1)

	def test_8_cant_give(self):
		"""
		You shouldn't be able to do trades where you give something for
		nothing
		"""
		with self.assert_moves(0):
			self.game.recv_trade(self.player1, {
				'give': {'ore': 1},
				'want': {},
				'player_id': self.player2.id,
				'turn': self.game.action_number,
			})
			self.game.recv_trade(self.player2, {
				'give': {},
				'want': {'ore': 1},
				'player_id': self.player1.id,
				'turn': self.game.action_number,
			})

	def test_9_0_negative_trade(self):
		with self.assert_moves(0):
			self.game.recv_trade(self.player1, {
				'give': {'ore': -1},
				'want': {'wheat': -1},
				'player_id': self.player2.id,
				'turn': self.game.action_number,
			})
			self.game.recv_trade(self.player2, {
				'give': {'wheat': -1},
				'want': {'ore': -1},
				'player_id': self.player1.id,
				'turn': self.game.action_number,
			})

	def test_9_1_outdated_trade(self):
		self.player1.cards['wheat'] += 1
		self.player2.cards['ore'] += 1

		self.game.recv_trade(self.player1, {
			'give': {'wheat': 1},
			'want': {'ore': 1},
			'player_id': self.player2.id,
			'turn': self.game.action_number,
		})

		with self.assert_moves(2):
			self.game.recv_move(self.game.current_player, {'type': 'end_turn'})
			self.game.recv_move(self.game.current_player, {'type': 'roll'})

		with self.assert_moves(0):
			self.game.recv_trade(self.player2, {
				'give': {'ore': 1},
				'want': {'wheat': 1},
				'player_id': self.player1.id,
				'turn': self.game.action_number,
			})

		with self.assert_moves(1):
			self.game.recv_trade(self.player1, {
				'give': {'wheat': 1},
				'want': {'ore': 1},
				'player_id': self.player2.id,
				'turn': self.game.action_number,
			})

	def test_9_2_port_trade(self):
		pl = self.game.current_player

		for res in const.resources:
			pl.cards[res] += 5

		with self.assert_moves(0):
			# Don't let trade 1:1
			self.game.recv_trade(pl, {
				'give': {'ore': 1},
				'want': {'wheat': 1},
				'player_id': None,
				'port': True,
				'turn': self.game.action_number,
			})

		with self.assert_moves(0):
			# Don't let trade at 5:1 either
			self.game.recv_trade(pl, {
				'give': {'ore': 5},
				'want': {'wheat': 1},
				'player_id': None,
				'port': True,
				'turn': self.game.action_number,
			})

		if not pl.get_ports():
			# Can trade at 4:1
			with self.assert_moves(1):
				self.game.recv_trade(pl, {
					'give': {'ore': 4},
					'want': {'wheat': 1},
					'player_id': None,
					'port': True,
					'turn': self.game.action_number,
				})

		elif pl.get_ports() - {'general'}:
			for port_res in (pl.get_ports() - {'general'}):
				get_res = 'wheat'
				if port_res == get_res:
					get_res = 'ore'

				with self.assert_moves(1):
					# Can trade at 2:1
					self.game.recv_trade(pl, {
						'give': { port_res: 2},
						'want': { get_res: 1},
						'player_id': None,
						'port': True,
						'turn': self.game.action_number,
					})

		elif 'general' in pl.get_ports():
			with self.assert_moves(0):
				# Don't let trade at 4:1 with a port
				self.game.recv_trade(pl, {
					'give': {'ore': 4},
					'want': {'wheat': 1},
					'player_id': None,
					'port': True,
					'turn': self.game.action_number,
				})

			with self.assert_moves(1):
				# Can trade at 3:1 with a port
				self.game.recv_trade(pl, {
					'give': {'ore': 3},
					'want': {'wheat': 1},
					'player_id': None,
					'port': True,
					'turn': self.game.action_number,
				})

	def test_9_3_cant_give_same_res(self):
		self.player1.cards['ore'] += 1
		self.player2.cards['ore'] += 1

		with self.assert_moves(0):
			self.game.recv_trade(self.player2, {
				'give': {'ore': 1},
				'want': {'ore': 1},
				'player_id': self.player1.id,
				'turn': self.game.action_number,
			})

			self.game.recv_trade(self.player1, {
				'give': {'ore': 1},
				'want': {'ore': 1},
				'player_id': self.player2.id,
				'turn': self.game.action_number,
			})

	@repeat(3)
	def test_9_4_move_robber(self):
		with self.assert_moves(1):
			self.game.recv_move(self.game.current_player, {'type': 'end_turn'})

		self.dice_gen.next = 3, 4
		conn = self.game.current_player.connection
		self.game.recv_move(conn.player, {'type': 'roll'})

		discard_players = [p for p in (self.player1, self.player2)
		                           if len(p.cards_list) > 7]

		if discard_players:
			self.assertTrue(self.game.waiting_for_discards)
		else:
			self.assertFalse(self.game.waiting_for_discards)

		for p in discard_players:
			with self.assert_moves(1):
				self.game.recv_move(p, 
					{
						'type': 'discard',
						'_cards': dict(Counter(
							random.sample(p.cards_list, len(p.cards_list) // 2)))
					}
				)

		# Move the robber.
		with self.assert_moves(1):
			self.game.recv_move(conn.player, random_move(conn.moves))


		if 'steal_from' in [move['type'] for move in conn.moves]:
			with self.assert_moves(1):
				self.game.recv_move(conn.player, random_move(conn.moves))


	def test_9_5_dev_cards(self):
		# Sorting by classname will put Knights first.
		self.game.dev_card_deck.cards.sort(key=lambda a:a.__class__.__name__, reverse=True)

		with self.assert_moves(1):
			self.game.recv_move(self.game.current_player, {'type': 'end_turn'})

		self.dice_gen.next = 1, 1
		conn = self.game.current_player.connection
		conn.player.cards['ore'] += 1
		conn.player.cards['wool'] += 1
		conn.player.cards['wheat'] += 1

		self.game.recv_move(conn.player, {'type': 'roll'})

		with self.assert_moves(1):
			self.game.recv_move(conn.player, {'type': 'build', 'build': 'dev_card'})

		self.assertEqual(len(conn.player.dev_cards), 1)
		self.assertEqual(conn.player.dev_cards[0].name, 'Knight')


if __name__ == '__main__':
	unittest.main()