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

def starting_phase(self):
	pl = self.current_player

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

def start_of_turn(self):
	valid_moves = [{
		'type': 'roll',
	}]

	#TODO dev cards
	
	move = yield valid_moves
	while not is_valid(move, valid_moves):
		log.debug('invalid move')
		move = yield valid_moves

	self.do_move(self.current_player, move)

def rest_of_turn(self):
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

		move = yield valid_moves
		while not is_valid(move, valid_moves):
			log.debug('invalid move')
			move = yield valid_moves

		if move['type'] == 'end_turn':
			break
			
		self.do_move(pl, move)