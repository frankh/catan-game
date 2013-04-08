import random
import json
from collections import defaultdict

from utils import timed, cached_per_action
from board_generation import generate_board, flatten
import dice_gen

from const import tile_resource_map, resources

class Building(object):
	def __init__(self, owner, building):
		self.owner = owner
		self.building = building

	def as_dict(self):
		return {
			'type'    : 'building',
			'owner'   : self.owner.as_dict(),
			'building': self.building,
		}

	@property
	def resource_cost(self):
		d = {
			'wool': 0,
			'wheat': 0,
			'clay': 0,
			'wood': 0,
			'ore': 0,
		}

		if self.building == 'settlement':
			d['wheat'] = 1
			d['wool'] = 1
			d['clay'] = 1
			d['wood'] = 1
		elif self.building == 'road':
			d['clay'] = 1
			d['wood'] = 1
		elif self.building == 'city':
			d['ore'] = 3
			d['wheat'] = 2

		return d

class Player(object):

	def __init__(self, connection, name, game):
		self.connection = connection
		self.game = game
		self.name = name
		self.cards = {
			'wood': 0,
			'wheat': 0,
			'clay': 0,
			'wool': 0,
			'ore': 0,
		}
		self.dev_cards = []
		self.num_soldiers = 0
		self.has_longest_road = 0
		self.has_largest_army = 0
		self.ready = False

	@cached_per_action
	def get_connected_locations(self):
		current_verts = [v for v in self.game.board.vertices
		                         if v.built 
		                        and v.built.owner is self]
		visited_verts = set(current_verts)
		visited_paths = set()

		while current_verts:
			vert = current_verts.pop()
			visited_verts.add(vert)

			visited_paths.update(p for p in vert.paths if not p.built)

			for p in vert.paths:
				if p.built and p.built.owner == self:
					current_verts += [v for v in p.verts if v not in visited_verts]

		return visited_verts, visited_paths

	@cached_per_action
	def get_connected_vertices(self):
		visited_verts, visited_paths = self.get_connected_locations()

		return visited_verts

	@cached_per_action
	def get_connected_paths(self):
		visited_verts, visited_paths = self.get_connected_locations()

		return visited_paths

	def send(self, msg):
		self.connection.write_message(json.dumps(msg))

	@property
	@cached_per_action
	def victory_points_settlements(self):
		return len([v for v in self.game.board.vertices
		                    if v.built 
		                   and v.built.building == 'settlement' 
		                   and v.built.owner == self])

	@property
	@cached_per_action
	def victory_points_cities(self):
		return len([v for v in self.game.board.vertices
		                    if v.built 
		                   and v.built.building == 'city' 
		                   and v.built.owner == self])

	@property
	@cached_per_action
	def victory_point_dev_cards(self):
		return 0

	@property
	@cached_per_action
	def victory_points(self):
		points = 0

		if self.has_longest_road:
			points += 2
		if self.has_largest_army:
			points += 2

		points += self.victory_points_cities
		points += self.victory_points_settlements
		points += self.victory_point_dev_cards

		return points

	@property
	@cached_per_action
	@timed
	def longest_road(self):
		cached_calls = {}

		def cache(func):
			def wrapped(v, l, visited_paths):
				key = (v.id, l, tuple([p.id for p in visited_paths]))
				if key in cached_calls:
					return cached_calls[key]

				cached_calls[key] = func(v, l, visited_paths)
				return cached_calls[key]

			return wrapped

		@cache
		def longest_road_from_point(v, l, visited_paths):
			if v.built and v.built.owner is not self:
				return l

			next_paths = (p for p in v.paths 
			                      if p.built and p.built.owner == self
			                     and p not in visited_paths)

			res = [l]

			for p in next_paths:
				next_vert = [v1 for v1 in p.verts if v1 is not v][0]

				res.append(longest_road_from_point(next_vert, l+1, visited_paths | {p}))


			return max(res)

		ret = max([longest_road_from_point(v, 0, set()) for v
		           in self.game.board.vertices 
			       if [p for p in v.paths if p.built and p.built.owner == self]
			      ] or [0])

		return ret

	@property
	@cached_per_action
	def num_buildings(self):
		return len([v for v in self.game.board.vertices
			                if v.built and v.built.owner is self])

	@property
	@cached_per_action
	def num_roads(self):
		return len([p for p in self.game.board.paths
			                if p.built and p.built.owner is self])

	@cached_per_action
	def as_dict(self):
		return {
			'type': 'player',
			'name': self.name,
			'icon': 'human',
			'num_cards': sum(self.cards.values()),
			'cards': self.cards,
			'num_dev_cards': len(self.dev_cards),
			'dev_cards': self.dev_cards,
			'num_soldiers': self.num_soldiers,
			'longest_road': self.longest_road,
			'has_longest_road': self.has_longest_road,
			'victory_points': self.victory_points,
			'player_id': self.id,
			'color': self.color,
		}

player_colors = {
	0: 'blue',
	1: 'red',
	2: 'green',
	3: 'yellow',
}

class Game(object):
	started = False
	max_players = 4

	def __init__(self):
		self.players = []
		self.password = None
		self.board = generate_board()
		self.current_player = None
		self.started = False
		self.dice_gen = dice_gen.RandomDiceGen()
		self.action_number = 0
		self.active_trades = defaultdict(dict)

	def maybe_start(self):
		"""
		Start the game if everyone is ready, the game is full and we
		haven't already started.
		"""
		if not [p for p in self.players if not p.ready]\
		   and len(self.players) == self.max_players   \
		   and not self.started:
			self.start()

	def start(self):
		"""
		Start the game!
		"""
		self.started = True
		self.turn_generator = self.turns(random.choice(self.players))
		self.gen = self.turn()
		moves = next(self.gen)
		self.current_player.send({
			'type': 'moves',
			'moves': moves
		})

	def broadcast(self, message):
		"""
		Sends a message to all the players in the game.
		"""
		for player in self.players:
			player.send(message)

	def recv_move(self, player, move):
		"""
		Sent every time the client performs a move.

		If it's not the current player's turn do nothing, there are
		no valid out of turn moves in Catan.

		Otherwise send to the generator, which will validate and performs
		the move, update the current player if necessary, and return the (new)
		current players valid moves which we then send back to the player.
		"""
		if player == self.current_player:
			moves = self.gen.send(move)
			self.current_player.send({
				'type': 'moves',
				'moves': moves
			})

	def recv_trade(self, player, trade):
		"""
		Sent every time the client updates the player's trade offer.

		trade shoud look like: 
		{
			'give': {
				'ore': 2,
				..etc (ONLY non 0 values)
			},
			'want': {
				'wheat': 1,
				..etc (ONLY non 0 values)
			},
			'player_id': <None> or <player_id>,
			'turn': <action_number>
		}

		The player's active trade is set to this trade if it is valid.
		Invalid trades (invalid player, invalid resource etc) are silently 
		dropped.

		If the player_id is not None, and the specified player's active trade
		mirrors this trade, the trade is done. Note that this means the 
		target active trade must also specify this player id and the turn
		numbers must match.

		For the trade to go through it must be one of the players turns.
		"""
		def valid_trade(player, trade):
			"""
			Returns true if the format of the trade is as expected, 
			otherwise false.
			"""
			try:
				pl_id = trade['player_id']
				if pl_id is not None:
					pl = self.players[int(pl_id)]

				turn = int(trade['turn'])
				if turn != self.action_number:
					# Outdated trade
					return False

				# Make sure all the resources are real ones.
				for key in itertools.chain(trade['give'], trade['want']):
					if key not in resources:
						return False

				# Check if player has enough resources.
				for res in trade['give']:
					if player.cards[res] < trade['give']['res']:
						return False

				return True
			except (KeyError, TypeError, IndexError, ValueError):
				return False

		if not valid_trade(player, trade):
			# Just silently ignore invalid trades for now.
			# Most likely scenario is a wierd edge-case bug that
			# wouldn't be worth telling user about
			return

		self.active_trades[player] = trade

		traded = False
		t_player = None
		if trade['player_id']:
			t_player = self.players[int(trade['player_id'])]

			matched_trade = self.active_trades[t_player.id]

			# Both players must have initiated the trade this turn
			# Both players must be giving what the other wants
			# The trades must be targetting each other
			# Can only trade on your turn.
			# Theoretically the matched trade could no longer be valid
			# if the player has somehow changed number of cards in their
			# hand (not sure how that would be possible...but make sure)
			if  matched_trade \
			and matched_trade['turn'] == trade['turn'] \
			and matched_trade['give'] == trade['want'] \
			and matched_trade['want'] == trade['give'] \
			and int(matched_trade['player_id']) == player.id \
			and self.current_player in (player, t_player) \
			and valid_trade(t_player, matched_trade):
				# Do the trade!
				# Both players must have enough cards because of the 
				# valid_trade checks
				self.do_trade(trade, player, t_player)
				traded = True
				
		# Only send the trade offer if we haven't performed the trade.
		# The client should reset the trade offers of the 2 parties in a trade.
		if not traded:
			self.broadcast({
				'type': 'trade_offer',
				'player': player.as_dict(),
				'trade': trade,
			})

	def turn(self):

		while True:
			self.action_number += 1
			self.current_player = next(self.turn_generator)

			self.broadcast({
				'type': 'current_player',
				'player': self.current_player.as_dict()
			})

			from turn_generators import \
				starting_phase, \
				start_of_turn,  \
				rest_of_turn

			if self.current_player.num_buildings < 2:
				yield from starting_phase(self)
			else:
				yield from start_of_turn(self)
				yield from rest_of_turn(self)


	def do_trade(self, trade, player_from, player_to):
		self.action_number += 1
		
		for res in trade['give']:
			player_from.cards[res] -= trade['give'][res]
			player_to.cards[res] += trade['give'][res]
		for res in trade['want']:
			player_from.cards[res] += trade['want'][res]
			player_to.cards[res] -= trade['want'][res]

		self.broadcast({
			'type': 'trade',
			'trade': {
				'give': trade['give'],
				'want': trade['want'],
				'player_from': player_from.as_dict(),
				'player_to': player_to.as_dict(),
			}
		})


	def do_move(self, player, move):
		self.action_number += 1

		if move['type'] == 'place':
			location = None

			if( move['location']['type'] == 'vertex'):
				location = self.board.Vertex.get(move['location']['id'])

			elif( move['location']['type'] == 'path'):
				location = self.board.Path.get(move['location']['id'])

			if location.built is not None:
				raise Exception('Tried to build over existing building')

			# TODO check building type
			location.built = Building(player, move['build'])

		elif move['type'] == 'build':
			print('building', move)
			location = None

			if( move['location']['type'] == 'vertex'):
				location = self.board.Vertex.get(move['location']['id'])

			elif( move['location']['type'] == 'path'):
				location = self.board.Path.get(move['location']['id'])

			if location.built is not None:
				if move['build'] != 'city' or location.built.building != 'settlement':
					raise Exception('Tried to build over existing building')

			# TODO check building type
			location.built = Building(player, move['build'])

			player.cards = {
				key: val - location.built.resource_cost[key] 
				     for key, val in player.cards.items()
			}

		elif move['type'] == 'roll':
			die1, die2 = self.dice_gen.roll()
			result = die1 + die2

			gen_hexes = [hx for hx in self.board.land_hexes if hx.value == result]
			for hx in gen_hexes:
				res = tile_resource_map[hx.tile]

				if res:
					for vert in hx.vertices:
						if vert.built:
							building = vert.built.building
							res_count = 0

							if building == 'settlement':
								res_count = 1
							elif building == 'city':
								res_count = 2
							else:
								raise Exception('invalid building type')

							if hx.being_robbed:
								#TODO
								pass
							else:
								# TODO message
								vert.built.owner.cards[res] += res_count

			self.broadcast({
				'type': 'roll',
				'values': [die1, die2],
				'result': result,
				'gen_hexes': [hx.as_dict() for hx in gen_hexes],
			})

		self.broadcast({
			'type': 'game',
			'game': self.as_dict()
		})

	def turns(self, first_player):
		num_players = len(self.players)
		random.shuffle(self.players)
		start_index = self.players.index(first_player)

		for i in range(num_players):
			player = self.players[(start_index+i)%num_players]
			yield player

		for i in range(num_players):
			player = self.players[(start_index-1-i)%num_players]
			yield player

		current_player = start_index
		while True:
			player = self.players[current_player]
			yield player
			current_player = (current_player + 1) % num_players

	def set_ready(self,player):
		player.ready = True
		self.maybe_start()

	def add_player(self, player):
		player.id = len(self.players)
		self.players.append(player)
		player.color = player_colors[player.id]

		if len(self.players) == self.max_players:
			self.maybe_start()

	def as_dict(self):
		return {
			'board': self.board.as_dict(),
			'players': [p.as_dict() for p in self.players],
			'turn': self.action_number,
		}