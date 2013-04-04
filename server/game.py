import random
import json

from board_generation import generate_board
import dice_gen


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

tile_resource_map = {
	'forest': 'wood',
	'fields': 'wheat',
	'hills': 'clay',
	'pasture': 'wool',
	'mountains': 'ore',
	'desert': None,
	None: None,
}

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
		self.longest_road = 0
		self.has_longest_road = 0
		self.victory_points = 0
		self.ready = False

	def get_connected_locations(self):
		current_verts = [v for v in self.game.board.vertices if v.built and v.built.owner == self]
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

	def get_connected_vertices(self):
		visited_verts, visited_paths = self.get_connected_locations()

		return visited_verts

	def get_connected_paths(self):
		visited_verts, visited_paths = self.get_connected_locations()

		return visited_paths

	def send(self, msg):
		self.connection.write_message(json.dumps(msg))

	@property
	def num_buildings(self):
		return len([v for v in self.game.board.vertices
			                if v.built and v.built.owner is self])

	@property
	def num_roads(self):
		return len([p for p in self.game.board.paths
			                if p.built and p.built.owner is self])

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
	1: 'blue',
	2: 'red',
	3: 'green',
	4: 'yellow',
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

	def maybe_start(self):
		if not [p for p in self.players if not p.ready]\
		   and len(self.players) == self.max_players   \
		   and not self.started:
			self.start()

	def start(self):
		self.started = True
		self.turn_generator = self.turns(random.choice(self.players))
		self.gen = self.turn()
		moves = next(self.gen)
		self.current_player.send({
			'type': 'moves',
			'moves': moves
		})

	def broadcast(self, message):
		for player in self.players:
			player.send(message)

	def recv_move(self, player, move):
		if player == self.current_player:
			moves = self.gen.send(move)
			self.current_player.send({
				'type': 'moves',
				'moves': moves
			})

	def turn(self):

		plurals = {
			'locations': 'location'
		}

		def is_valid(move, valid_moves):
			for valid in valid_moves:
				def valid_key():
					for key in valid:
						plural = False

						if key in plurals:
							plural = True

						if (plurals[key] if plural else key) not in move:
							return False

						if plural:
							if move[plurals[key]] not in valid[key]:
								return False
						else:
							if move[key] != valid[key]:
								return False
					return True

				if move['type'] != valid['type']:
					continue

				if not valid_key():
					print(move, 'not in', valid_moves)
					continue

				return True

			return False

		while True:
			self.current_player = next(self.turn_generator)
			pl = self.current_player
			
			self.broadcast({
				'type': 'current_player',
				'player': pl.as_dict()
			})

			move = None

			if pl.num_buildings < 2:
				print('settle', self.current_player.id)
				# Starting phase.

				## PLACE SETTLEMENT
				valid_moves = [{
					'type': 'place',
					'build': 'settlement',
					'locations': [v.id_dict() for v in self.board.vertices 
					                                if v.is_free()]
				}]

				move = yield valid_moves

				while not is_valid(move, valid_moves):
					raise Exception('invalid')
					move = yield valid_moves

				self.do_move(self.current_player, move)
				print('road', self.current_player.id)

				placed_vertex = self.board.Vertex.get(move['location']['id'])
				if pl.num_buildings == 2:
					# Give starting resources
					for hx in placed_vertex.hexes:
						res = tile_resource_map[hx.tile]
						if res:
							pl.cards[res] += 1

				## PLACE ROAD
				valid_moves = [{
					'type': 'place',
					'build': 'road',
					'locations': [path.id_dict() for path in placed_vertex.paths
					                                      if not path.built]
				}]

				move = yield valid_moves
				while not is_valid(move, valid_moves):
					raise Exception('invalid')
					move = yield valid_moves

				self.do_move(self.current_player, move)
				print('done', self.current_player.id)
			else:
				valid_moves = [{
					'type': 'roll',
				}]
				
				move = yield valid_moves
				while not is_valid(move, valid_moves):
					log.debug('invalid move')
					move = yield valid_moves

				self.do_move(self.current_player, move)

				#Actual turn!
				while move['type'] != 'end_turn':
					valid_moves = [{
						'type': 'end_turn'
					}]

					cards = self.current_player.cards

					if cards['wood'] and cards['clay']:
						# can build road
						valid_paths = [p for p in pl.get_connected_paths() if not p.built]

						valid_moves.append({
							'type': 'build',
							'build': 'road',
							'locations': [p.id_dict() for p in valid_paths]
						})

						if cards['wool'] and cards['wheat']:
							#can build settlement
							valid_verts = [v for v in pl.get_connected_vertices() if v.is_free()]
							valid_moves.append({
								'type': 'build',
								'build': 'settlement',
								'locations': [v.id_dict() for v in valid_verts]
							})

					if cards['wheat'] >= 2 and cards['ore'] >= 3:
						# can build city
						valid_verts = [v for v in pl.get_connected_vertices() 
						                       if v.built 
						                      and v.built.building == 'settlement'
						                      and v.built.owner == pl]

						valid_moves.append({
							'type': 'build',
							'build': 'city',
							'locations': [v.id_dict() for v in valid_verts]
						})


					if cards['wheat'] and cards['wool'] and cards['ore']:
						# can build dev card
						valid_moves.append({
							'type': 'build',
							'build': 'dev_card'
						})

					move = yield valid_moves
					while not is_valid(move, valid_moves):
						log.debug('invalid move')
						move = yield valid_moves

					self.do_move(pl, move)


	def do_move(self, player, move):
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
		self.players.append(player)
		player.id = len(self.players)
		player.color = player_colors[player.id]

		if len(self.players) == self.max_players:
			self.maybe_start()

	def as_dict(self):
		return {
			'board': self.board.as_dict(),
			'players': [p.as_dict() for p in self.players],
		}
