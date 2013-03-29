import itertools
import random
import json
import logging
from collections import defaultdict, Iterable
import itertools
from functools import lru_cache

log = logging.getLogger('catan')
log.setLevel(logging.DEBUG)

def flatten(l):
	return list(itertools.chain(*l))

def listify(gen):
	"Convert a generator into a function which returns a list"
	def patched(*args, **kwargs):
		return list(gen(*args, **kwargs))
	return patched

def get_ident(*ident_in):
	ident_in = tuple(sorted(ident_in))

	if len(ident_in) == 1:
		ident = ident_in[0]
	else:
		ident = ident_in

	return ident

class Board(object):
	def __init__(self, Hex, Vertex, Path):
		self.Hex, self.Vertex, self.Path = Hex, Vertex, Path

		self.hexes = list(Hex.objects.values())
		self.vertices = list(Vertex.objects.values())
		self.paths = list(Path.objects.values())

		self.land_hexes = [hx for hx in self.hexes if not hx.is_sea]

	def as_dict(self):
		return {
			'type'    : 'board',
			'hexes'   : [hx.as_dict() for hx in self.land_hexes],
			'vertices': [v.as_dict()  for v  in self.vertices  ],
			'paths'   : [p.as_dict()  for p  in self.paths     ],
		}

class Building(object):
	def __init__(self, owner, building):
		self.owner = owner
		self.building = building

	def as_dict(self):
		return {
			'type'    : 'board',
			'owner'   : self.owner,
			'building': self.building,
		}

# Make it easier to keep track of which sea is where.
def Sea(hex1, hex2):
	hex1, hex2 = sorted([hex1, hex2])
	return 10000 + 100*hex1 + hex2 

def create_board():

	class CatanObj(object):
		objects = None
		count = 0
		initialised = False

		@classmethod
		def get(cls, *ident_in):
			ident = get_ident(*ident_in)

			if cls.objects is None:
				cls.objects = {}

			if ident in cls.objects:
				return cls.objects[ident]

			return cls(*ident_in)

		def __init__(self, *ident_in):
			if self.initialised: 
				raise Exception('Should not be creating new objects after initialisation.')

			ident = get_ident(*ident_in)

			self.id = ident

			self.__class__.count += 1
			self.number = self.__class__.count

			objs = self.__class__.objects

			if objs is None:
				objs = self.__class__.objects = {}

			if ident in objs:
				raise Exception('Duplicate ID for {cls}: {ident}'.format(
					cls=self.__class__,
					ident=ident
				))

			objs[ident] = self

			print ('created ' + str(self) + ' - ' + str(ident))

		def __str__(self):
			return '{cls}<{id}>'.format(cls=self.__class__.__name__, id=self.id)
		__repr__ = __str__

	class Hex(CatanObj):
		tile = None
		value = None
		port = None
		port_path = None
		being_robbed = False
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
		hex_adj_graph = {
			1 : [2 , 12, 13,     Sea(1 , 1 ), Sea(1 , 2 ), Sea(1 , 12)],
			2 : [1 , 3 , 13 ,14, Sea(1 , 2 ), Sea(2 , 3 )],
			3 : [2 , 4 , 14,     Sea(2 , 3 ), Sea(3 , 3 ), Sea(3 , 4 )],
			4 : [3 , 5 , 14, 15, Sea(3 , 4 ), Sea(4 , 5 )],
			5 : [4 , 6 , 15,     Sea(4 , 5 ), Sea(5 , 5 ), Sea(5 , 6 )],
			6 : [5 , 7 , 15, 16, Sea(5 , 6 ), Sea(6 , 7 )],
			7 : [6 , 8 , 16,     Sea(6 , 7 ), Sea(7 , 7 ), Sea(7 , 8 )],
			8 : [7 , 9 , 16, 17, Sea(7 , 8 ), Sea(8 , 9 )],
			9 : [8 , 10, 17,     Sea(8 , 9 ), Sea(9 , 9 ), Sea(9 , 10)],
			10: [9 , 11, 17, 18, Sea(9 , 10), Sea(10, 11)],
			11: [10, 12, 18,     Sea(10, 11), Sea(11, 11), Sea(11, 12)],
			12: [1 , 11, 13, 18, Sea(11, 12), Sea(1 , 12)],
			13: [1 , 2 , 12, 14, 18, 19],
			14: [2 , 3 , 4 , 13, 15, 19],
			15: [4 , 5 , 6 , 15, 16, 19],
			16: [6 , 7 , 8 , 15, 17, 19],
			17: [8 , 9 , 10, 16, 18, 19],
			18: [10, 11, 12, 13, 17, 19],
			19: [13, 14, 15, 16, 17, 18],

			Sea(1 , 1 ): [Sea(1 , 2 ), Sea(1 , 12), 1 ],
			Sea(1 , 2 ): [Sea(1 , 1 ), Sea(2 , 3 ), 1 , 2 ],
			Sea(2 , 3 ): [Sea(1 , 2 ), Sea(3 , 3 ), 2 , 3 ],
			Sea(3 , 3 ): [Sea(2 , 3 ), Sea(3 , 4 ), 3 ],
			Sea(3 , 4 ): [Sea(3 , 3 ), Sea(4 , 5 ), 3 , 4 ],
			Sea(4 , 5 ): [Sea(3 , 4 ), Sea(5 , 5 ), 4 , 5 ],
			Sea(5 , 5 ): [Sea(4 , 5 ), Sea(5 , 6 ), 5 ],
			Sea(5 , 6 ): [Sea(5 , 5 ), Sea(6 , 7 ), 5 , 6 ],
			Sea(6 , 7 ): [Sea(5 , 6 ), Sea(7 , 7 ), 6 , 7 ],
			Sea(7 , 7 ): [Sea(6 , 7 ), Sea(7 , 8 ), 7 ],
			Sea(7 , 8 ): [Sea(7 , 7 ), Sea(8 , 9 ), 7 , 8 ],
			Sea(8 , 9 ): [Sea(7 , 8 ), Sea(9 , 9 ), 8 , 9 ],
			Sea(9 , 9 ): [Sea(8 , 9 ), Sea(9 , 10), 9 ],
			Sea(9 , 10): [Sea(9 , 9 ), Sea(10, 11), 9 , 10],
			Sea(10, 11): [Sea(9 , 10), Sea(11, 11), 10, 11],
			Sea(11, 11): [Sea(10, 11), Sea(11, 12), 11],
			Sea(11, 12): [Sea(11, 11), Sea(1 , 12), 11, 12],
			Sea(1 , 12): [Sea(11, 12), Sea(1 , 1 ), 1 , 12],
		}

		@property
		def vertices(self):
			return {v for v in Vertex.objects.values() if self in v.hexes}

		@property
		def is_sea(self):
			return self.id > 100

		def __init__(self, ident):
			super().__init__(ident)
			ident = self.id

			self.adj_hexes = list(map(Hex.get, Hex.hex_adj_graph[ident]))

		@classmethod
		def create_vertices(cls):
			# Every group of 3 hexes has a vertex
			for hx in Hex.objects.values():
				for hx2 in hx.adj_hexes:
					for hx3 in [h for h in hx2.adj_hexes if h in hx.adj_hexes]:
						if len({hx.id, hx2.id, hx3.id}) == 3:
							Vertex.get(hx.id, hx2.id, hx3.id)

		def as_dict(self):
			return {
				'id': self.id,
				'tile': self.tile,
				'value': self.value,
				'port': self.port,
				'port_path': self.port_path.as_dict() if self.port_path else None,
				'being_robbed': self.being_robbed,
			}

	class Vertex(CatanObj):
		built = None
		probabilities = {
			0 : 0,
			2 : 1,
			3 : 2,
			4 : 3,
			5 : 4,
			6 : 5,
			8 : 5,
			9 : 4,
			10: 3,
			11: 2,
			12: 1
		}

		@property
		def probability(self):
			return sum(Vertex.probabilities[hx.value] for hx in self.hexes
			                                                 if not hx.is_sea)


		@property
		def paths(self):
			return [p for p in Path.objects.values() if self in p.verts]

		@property
		def adj_verts(self):
			return [v for v in Vertex.objects.values()
			           if v in itertools.chain(p.verts for p in self.paths)
			          and v is not self]

		def is_free(self):
			return not [v.built for v in self.adj_verts if v.built] \
			   and not self.built

		def __init__(self, hex1, hex2, hex3):
			super().__init__(hex1, hex2, hex3)

			self.hexes = {Hex.get(hx) for hx in (hex1, hex2, hex3)}

			for vert in Vertex.objects.values():
				num_shared_hexes = len(vert.hexes & self.hexes)

				if num_shared_hexes == 2:
					Path(self.id, vert.id)

		def as_dict(self):
			return {
				'id': self.id,
				'built': self.built.as_dict() if self.built else None,
				'probability': self.probability,
				'blocked': not self.is_free,
			}

	class Path(CatanObj):
		port = None
		built = None

		@property
		def next_coastal_path(self):
			coastal_paths = {p for p in self.paths if p.is_coastal}
			next_path = max(p.id for p in coastal_paths)

			if next_path < self.id:
				# We have wrapped around
				next_path = min(p.id for p in coastal_paths)

			return Path.get(next_path)

		@property
		def is_coastal(self):
			return bool(hx for hx in self.hexes if hx.is_sea)

		@property
		def hexes(self):
			vert1, vert2 = self.verts
			return vert1.hexes & vert2.hexes

		@property
		def paths(self):
			return {p for p in Path.objects.values()
			                if p.verts & self.verts}

		def __init__(self, vert1, vert2):
			super().__init__(vert1, vert2)
			self.verts = {Vertex.get(v) for v in (vert1, vert2)}

		def as_dict(self):
			return {
				'id': self.id,
				'built': self.built.as_dict() if self.built else None,
				'port': self.port,
			}

	# Creating 1 hex creates them all
	Hex.get(1)
	# Creating vertices creates paths
	Hex.create_vertices()
	CatanObj.initialised = True

	return Board(Hex, Vertex, Path)

def generate_board(port_start_offset=0):
	board = create_board()
	Hex, Vertex, Path = board.Hex, board.Vertex, board.Path

	port_start_sea_hex = Hex.get(Sea(1,2))
	port_start_v1, port_start_v2 = [v for v in port_start_sea_hex.vertices
	                                        if Hex.get(2) in v.hexes]

	port_start = Path.get(port_start_v1.id, port_start_v2.id)

	for i in range(port_start_offset):
		port_start = port_start.next_coastal_path

	tiles = [
		['desert']		* 1,
		['fields']		* 4,
		['forest']		* 4,
		['pasture']		* 4,
		['hills']		* 3,
		['mountains']	* 3,
	]

	ports = [
		['general']	* 4,
		['wheat']	* 1,
		['wood']	* 1,
		['wool']	* 1,
		['clay']	* 1,
		['ore']		* 1,
	]

	values = [
		[2]	* 1,
		[3]	* 2,
		[4]	* 2,
		[5]	* 2,
		[6]	* 2,
		[8]	* 2,
		[9]	* 2,
		[10]* 2,
		[11]* 2,
		[12]* 1,
	]

	tiles = flatten(tiles)
	random.shuffle(tiles)

	values = flatten(values)
	random.shuffle(values)

	ports = flatten(ports)
	random.shuffle(ports)

	# Assign ports
	port_path = port_start
	for port in ports:
		port_hex = [hx for hx in port_path.hexes 
		                      if not hx.is_sea][0]

		port_path.port = port
		port_hex.port = port
		port_hex.port_path = port_path

		for i in range(3):
			port_path = port_path.next_coastal_path

	# Assign tiles
	for hx, tile in zip([hx for hx in board.land_hexes], tiles):
		print('assigned',hx,tile)
		hx.tile = tile

	hexes = [hx for hx in board.land_hexes 
	                   if not hx.tile == 'desert']

	desert_hex = [hx for hx in board.land_hexes if hx.tile == 'desert'][0]
	desert_hex.being_robbed = True
	desert_hex.value = 0

	# Assign values
	for hx, value in zip(hexes, values):
		hx.value = value

	return board

class Player(object):
	def __init__(self, connection, name, game):
		self.connection = connection
		self.game = game
		self.name = name
		self.cards = []
		self.dev_cards = []
		self.num_soldiers = 0
		self.longest_road = 0
		self.has_longest_road = 0
		self.victory_points = 0
		self.ready = False

	def send(self, msg):
		self.connection.write_message(json.dumps(msg))

	@property
	def num_settlements(self):
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
			'num_cards': len(self.cards),
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

	def maybe_start(self):
		if not [p for p in self.players if not p.ready]\
		   and len(self.players) == self.max_players:
			self.start()

	def start(self):
		self.started = True
		self.turn_generator = self.turns(random.choice(self.players))

		moves = next(self.turn())
		self.current_player.send({
			'type': 'moves',
			'moves': moves
		})

	def turn(self):
		while True:
			self.current_player = next(self.turn_generator)
			pl = self.current_player
			move = None

			if pl.num_settlements < 2 or pl.num_roads < 2:
				print('starting', self.current_player)
				# Starting phase.
				build = 'settlement'
				locations = [
					v for v in self.board.vertices if v.is_free()
				]

				if pl.num_roads < pl.num_settlements:
					build = 'road'
					locations = list(itertools.chain(
						[v.paths for v in self.board.vertices 
						               if v.built and v.built.owner is pl]
					))

				valid_moves = [{
					'type': 'place',
					'build': build,
					'location': location.as_dict()
				} for location in locations]

				move = yield valid_moves
				while move not in valid_moves:
					move = yield valid_moves

			self.do_move(self.current_player, move)

	def do_move(self, player, move):
		if move['type'] == 'build':
			if move['location'].built is not None:
				raise Exception('Tried to build over existing building')

			move['location'].built = Building(player, move['build'])


	def turns(self, first_player):
		num_players = len(self.players)
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

class DefaultGame(Game):

	def __init__(self):
		super().__init__()
		self.max_players = 1

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.websocket
games = {
	'1': DefaultGame()
}

class ClientSocket(tornado.websocket.WebSocketHandler):

	def open(self, username, game_id, password):
		username = username.decode('utf-8')
		game_id = game_id.decode('utf-8')
		
		if password:
			password = password.decode('utf-8')

		global games
		if game_id not in games:
			self.write_message(json.dumps(
				{
					'type': 'error',
					'error': {
						'type': 'NO_GAME',
						'msg': 'Game doesn\'t exist',
					 }
				 })
			)
			self.close()
			return
			
		game = games[game_id]
		self.game = game
		self.player = Player(self, username, game)
		game.add_player(self.player)

		if game.password and game.password != password:
			self.write_message(json.dumps(
				{
					'type': 'error',
					'error': {
						'type': 'BAD_PASSWORD',
						'msg': 'Wrong password',
					 }
				 })
			)
			self.close()
			return

		self.write_message(json.dumps({
			'type': 'game',
			'game': game.as_dict(),
		}));
		log.debug(username+" joined "+game_id)

	def on_message(self, message):
		log.debug(str('temp')+'>'+message)
		message = json.loads(message)

		if( message['type'] == 'ready' ):
			self.game.set_ready(self.player)
		
	def write_message(self, message):
		log.debug(str('temp')+'<'+message)
		super().write_message(message);


	def on_close(self):
		if hasattr(self, 'game'):
			self.game.players.remove(self.player)

socket_app = tornado.web.Application([
	(r"/socket/(?P<username>\w+)/(?P<game_id>\w+)(?:/(?P<password>\w+))?", 
	 ClientSocket),
])

if __name__ == '__main__':
	try:
		tornado.options.enable_pretty_logging()
		socket_app.listen(8080)
		log.debug('Listening on port 8080')
		iol = tornado.ioloop.IOLoop.instance()
		tornado.ioloop.PeriodicCallback(lambda: None,500,iol).start()
		iol.start()
	except BaseException as e:
		for game in games.values():
			game.killed = True
		raise e
