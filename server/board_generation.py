import itertools
import random
import functools

def flatten(l):
	return list(itertools.chain(*l))

def get_ident(*ident_in):
	"""
	Normalise id by ordering tuples, converting string (JavaScript) notation
	to tuple
		e.g. 1_3_4__4_5_6 -> ((1,3,4), (4,5,6))
		or (3, 2) -> (2, 3)
	"""

	if isinstance(ident_in[0], list):
		ident_in = ident_in[0]

	new_ident_in = []

	for ident in ident_in:
		new_ident = ident
		if isinstance(ident, str):
			if '__' in ident:
				for x in ident.split('__'):
					new_ident_in.append(get_ident(x))
			elif '_' in ident:
				new_ident_in.append(get_ident(ident.split('_')))
			else:
				new_ident_in.append(int(ident))
		else:
			new_ident_in.append(ident)

	ident_in = new_ident_in
	ident_in = tuple(sorted(ident_in))

	if len(ident_in) == 1:
		ident = ident_in[0]
	else:
		ident = ident_in

	return ident

class Board(object):
	def __init__(self, Hex, Vertex, Path, CacheObj):
		self.Hex, self.Vertex, self.Path = Hex, Vertex, Path
		self.CacheObj = CacheObj

		self.hexes = list(Hex.objects.values())
		self.vertices = list(Vertex.objects.values())
		self.paths = list(Path.objects.values())
		self.ports = []

		self.land_hexes = [hx for hx in self.hexes if not hx.is_sea]

	def as_dict(self):
		return {
			'type'    : 'board',
			'hexes'   : [hx.as_dict() for hx   in self.land_hexes],
			'vertices': [v.as_dict()  for v    in self.vertices  ],
			'paths'   : [p.as_dict()  for p    in self.paths     ],
			'ports'   : [port         for port in self.ports     ],
		}

# Make it easier to keep track of which sea is where.
def Sea(hex1, hex2):
	hex1, hex2 = sorted([hex1, hex2])
	return 10000 + 100*hex1 + hex2 

def create_board():

	class CacheObj(object):
		cache_val = 0

	def cached_copy(func):
		"""
		Wrapper that causes the function to always return the same value.

		If the value is not immutable it returns a copy.
		"""

		cache = {}
		@functools.wraps(func)
		def wrapper(self, *args, **kwargs):
			key = CacheObj.cache_val, func.__qualname__, self.id

			if key not in cache:
				cache[key] = func(self, *args, **kwargs)

			if isinstance(cache[key], list):
				cache[key] = list(cache[key])

			return cache[key]

		return wrapper

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
				raise Exception('Should not be creating new'
				' objects after initialisation. ({cls}, {args})'.format(
					cls=self.__class__.__name__,
					args=ident_in)
				)

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

		def id_dict(self):
			d = self.as_dict()

			return {
				'type': d['type'],
				'id': d['id'],
			}

		@property
		def str_id(self):
			if isinstance(self.id, int):
				return str(self.id)

			def tuple_to_str(tup):
				l = []
				depth = 1
				for x in tup:
					if isinstance(x, tuple):
						x, sub_depth = tuple_to_str(x)
						depth = max(1+sub_depth, depth)
					else:
						x = str(x)
					l.append(x)

				return ('_'*depth).join(l), depth

			return tuple_to_str(self.id)[0]


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
		@cached_copy
		def vertices(self):
			return frozenset(v for v in Vertex.objects.values() 
			                         if self in v.hexes)

		@property
		def is_sea(self):
			return self.id > 100

		def __init__(self, ident):
			super().__init__(ident)
			ident = self.id

			self.adj_hexes = frozenset(map(Hex.get, Hex.hex_adj_graph[ident]))

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
				'type': 'hex',
				'tile': self.tile,
				'value': self.value,
				'port': self.port,
				'port_path': self.port_path.as_dict() if self.port_path else None,
				'being_robbed': self.being_robbed,
			}

	class Vertex(CatanObj):
		built = None
		port = None
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
		@cached_copy
		def probability(self):
			return sum(Vertex.probabilities[hx.value] for hx in self.hexes
			                                                 if not hx.is_sea)
		@property
		@cached_copy
		def paths(self):
			return [p for p in Path.objects.values() if self in p.verts]

		@property
		@cached_copy
		def adj_verts(self):
			return [v for v in Vertex.objects.values()
			           if v in itertools.chain(*[p.verts for p in self.paths])
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
				'id': self.str_id,
				'built': self.built.as_dict() if self.built else None,
				'probability': self.probability,
				'blocked': not self.is_free(),
				'type': 'vertex',
			}

	coastal_path_cache = None
	class Path(CatanObj):
		port = None
		built = None

		@property
		@cached_copy
		def next_coastal_path(self):
			# This is essentially static data, but keep the generation func
			# in case it ever changes.
			# Cache once globally, not just per board.
			if coastal_path_cache is not None:
				return Path.get(coastal_path_cache[self.id])

			paths = [p for p in self.paths if p.is_coastal]

			def max_path_hex(p):
				def max_land_hex(v):
					return max(h.id for h in v.hexes if not h.is_sea)
				return max(max_land_hex(v) for v in p.verts)

			def min_path_hex(p):
				def min_land_hex(v):
					return min(h.id for h in v.hexes if not h.is_sea)
				return min(min_land_hex(v) for v in p.verts)

			p1_max_hex = max_path_hex(paths[0])
			p2_max_hex = max_path_hex(paths[1])
			p1_min_hex = min_path_hex(paths[0])
			p2_min_hex = min_path_hex(paths[1])

			next_path_idx = 0

			if p2_max_hex > p1_max_hex:
				next_path_idx = 1
			elif p2_max_hex == p1_max_hex:
				if p2_min_hex > p1_min_hex:
					next_path_idx = 1

			if max_path_hex(paths[next_path_idx]) == 12 \
			and max_path_hex(paths[1-next_path_idx]) in (12, 1) \
			and max_path_hex(self) == 12 or max_path_hex(self) == 1:
				# We have wrapped around
				next_path_idx = 1 - next_path_idx

			return paths[next_path_idx]

		@property
		@cached_copy
		def is_coastal(self):
			return bool([hx for hx in self.hexes if hx.is_sea])

		@property
		@cached_copy
		def hexes(self):
			vert1, vert2 = self.verts
			return frozenset(vert1.hexes & vert2.hexes)

		@property
		@cached_copy
		def paths(self):
			return frozenset(p for p in Path.objects.values()
			                if p.verts & self.verts
			               and p is not self)

		def __init__(self, vert1, vert2):
			super().__init__(vert1, vert2)
			self.verts = {Vertex.get(v) for v in (vert1, vert2)}

		def as_dict(self):
			return {
				'id': self.str_id,
				'built': self.built.as_dict() if self.built else None,
				'port': self.port,
				'type': 'path',
			}

	# Creating 1 hex creates them all
	Hex.get(1)
	# Creating vertices creates paths
	Hex.create_vertices()
	CatanObj.initialised = True

	board = Board(Hex, Vertex, Path, CacheObj)

	path_map = {}
	for path in board.paths:
		if path.is_coastal:
			path_map[path.id] = path.next_coastal_path.id

	coastal_path_cache = path_map

	return board

def generate_board(port_start_offset=0, validators=None):
	if validators is None:
		validators = ['desert_on_coast','no_same_value_adjacent','no_red_adjacent',
			'no_double_red_resource','no_same_value_resource','no_13_plus_vertex']
		validators = []
	
	board = create_board()
	def unvalidated_gen_board():
		board.CacheObj.cache_val += 1
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

		port_types = [
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

		port_types = flatten(port_types)
		random.shuffle(port_types)


		ports = []
		port_spacing = [3,3,4,3,3,4,3,3,4]

		# Assign ports
		port_path = port_start
		for port_type in port_types:
			port_hex = [hx for hx in port_path.hexes 
			                      if not hx.is_sea][0]

			# if port_path.port:
			# 	raise Exception('Path already has a port')

			port_path.port = port_type
			port_hex.port = port_type
			port_hex.port_path = port_path

			for vert in port_path.verts:
				vert.port = port_type

			ports.append({
				'id': len(ports),
				'port_type': port_type,
				'path': port_path.as_dict(),
				'hex': port_hex.as_dict(),
			})

			for i in range(port_spacing.pop(0)):
				port_path = port_path.next_coastal_path

		board.ports = ports

		# Assign tiles
		for hx, tile in zip([hx for hx in board.land_hexes], tiles):
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

	board = unvalidated_gen_board()

	while True:
		for validator in validators:
			import board_validators
			validator = getattr(board_validators, validator)
			if not validator(board):
				board = unvalidated_gen_board()
				break
		else:
			break

	return board

