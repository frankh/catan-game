import logging

from const import tile_resource_map

log = logging.getLogger('catan')


# Determine if a move is in the list of valid moves.
def is_valid(move, valid_moves):
	plurals = {
		'locations': 'location'
	}

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

def get_move(valid_moves):
	move = yield valid_moves

	while not is_valid(move, valid_moves):
		log.warning('Invalid Move')
		move = yield valid_moves

	return move

def starting_phase(self):
	pl = self.current_player

	## PLACE SETTLEMENT
	valid_moves = [{
		'type': 'place',
		'build': 'settlement',
		'locations': [v.id_dict() for v in self.board.vertices 
		                                if v.is_free()]
	}]

	move = yield from get_move(valid_moves)

	self.do_move(self.current_player, move)

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

	move = yield from get_move(valid_moves)

	self.do_move(self.current_player, move)

def rolled_robber(self):
	#TODO discards
	yield from move_robber(self)

def move_robber(self):
	valid_moves = [{
		'type': 'move_robber',
		'locations': [hx.id_dict() for hx in self.board.land_hexes
		                                  if not hx.being_robbed],
	}]

	move = yield from get_move(valid_moves)
	[hx for hx in self.board.land_hexes if hx.being_robbed][0].being_robbed = False

	hx = self.board.Hex.get(move['location']['id'])
	hx.being_robbed = True
	target_players = {v.built.owner for v in hx.vertices if v.built}
	target_players -= {self.current_player}

	target_players = {player for player in target_players 
	 			      if max(val for val in player.cards.values()) == 0}

	if target_players:
		valid_moves = [{
			'type': 'steal_from',
			'player': player
		} for player in target_players]

		move = yield from get_move(valid_moves)
		self.do_move(self.current_player, move)


def start_of_turn(self):
	self.can_trade = False

	valid_moves = [{
		'type': 'roll',
	}]

	#TODO dev cards
	
	move = yield from get_move(valid_moves)

	if move['type'] == 'roll':
		die1, die2 = self.dice_gen.roll()
		result = die1 + die2

		self.broadcast({
			'type': 'roll',
			'values': [die1, die2],
			'result': result,
		})

		if result == 7:
			yield from rolled_robber(self)

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
			'type': 'resource_generation',
			'hexes': [hx.as_dict() for hx in gen_hexes],
		})

		self.do_move(self.current_player, move)

def rest_of_turn(self):
	self.can_trade = True

	pl = self.current_player

	#Actual turn!
	while True:
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

		move = yield from get_move(valid_moves)

		if move['type'] == 'end_turn':
			break
			
		self.do_move(pl, move)