import itertools
import random
import json
import logging
from collections import defaultdict, Iterable
import itertools

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

def create_board():

	class CatanObj(object):
		objects = None
		count = 0

		# TODO use create function not init to test if already exists.

		@classmethod
		def get(cls, *ident_in):
			ident = get_ident(*ident_in)

			if cls.objects is None:
				cls.objects = {}

			if ident in cls.objects:
				return cls.objects[ident]

			return cls(*ident_in)

		def __init__(self, *ident_in):
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

	class Sea(int):
		seas = {}
		count = 0

		def __new__(cls, hex1, hex2):
			if (hex1, hex2) in cls.seas:
				return cls.seas[(hex1, hex2)]

			Sea.count += 1

			inst = super().__new__(cls, 100+Sea.count)
			inst.hexes = (hex1, hex2)
			cls.seas[(hex1, hex2)] = inst

			return inst

		def __str__(self):
			return 'Sea_{h1}_{h2}'.format(h1=self.hexes[0], h2=self.hexes[1])
		repr = __str__

	class Hex(CatanObj):
		SEA = 1
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


		def __init__(self, ident):
			super().__init__(ident)
			ident = self.id

			self.adj_hexes = list(map(Hex.get, Hex.hex_adj_graph[ident]))

		@classmethod
		def create_vertices(cls):
			for hx in Hex.objects.values():
				for hx2 in hx.adj_hexes:
					for hx3 in [h for h in hx2.adj_hexes if h in hx.adj_hexes]:
						if len({hx.id, hx2.id, hx3.id}) == 3:
							Vertex.get(hx.id, hx2.id, hx3.id)

	class Vertex(CatanObj):
		def __init__(self, hex1, hex2, hex3):
			super().__init__(hex1, hex2, hex3)

			self.hexes = {hex1, hex2, hex3}

			for vert in Vertex.objects.values():
				num_shared_hexes = len(vert.hexes & self.hexes)

				if num_shared_hexes == 2:
					Path(self.id, vert.id)

	class Path(CatanObj):
		def __init__(self, vert1, vert2):
			super().__init__(vert1, vert2)
			self.verts = (vert1, vert2)

	Hex.get(1)
	Hex.create_vertices()

	return {
		'hexes': list(Hex.objects.values()),
		'vertices': list(Vertex.objects.values()),
		'paths': list(Path.objects.values()),
	}


def generate_board():
	board = create_board()

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

	return {
		'tiles': tiles, 
		'values': values,
		'ports': ports,
	}

class Game(object):
	started = False

	def __init__(self):
		self.players = []
		self.password = None
		self.board = generate_board()

class DefaultGame(Game):
	def __init__(self):
		super().__init__()


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
			'type': 'board',
			'board': game.board	,
		}));
		log.debug(username+" joined "+game_id)

	def on_message(self, message):
		log.debug(str('temp')+'>'+message)
		message = json.loads(message)

	def write_message(self, message):
		log.debug(str('temp')+'<'+message)
		super().write_message(message);


	def on_close(self):
		pass
		# if hasattr(self, 'game'):
		# 	if self.game.started:
		# 		self.player.connected = False
		# 		self.player.connection = None
		# 	else:
		# 		self.game.players.remove(self.player)

socket_app = tornado.web.Application([
	(r"/socket/(?P<username>\w+)/(?P<game_id>\w+)(?:/(?P<password>\w+))?", ClientSocket),
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
