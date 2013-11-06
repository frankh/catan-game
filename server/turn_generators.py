import logging

from const import tile_resource_map

log = logging.getLogger('catan')


# Determine if a move is in the list of valid moves.
def is_valid(move, valid_moves, *validators):
	if move is None:
		return False

	plurals = {
		'locations': 'location'
	}

	for valid in valid_moves:
		def valid_key():
			for key in valid:
				if key.startswith('_'):
					continue

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
			continue

		if not all(validator(move, valid) for validator in validators):
			continue

		return True

	return False

def get_move(self, valid_moves, *extra_validators):
	move = yield valid_moves

	while not is_valid(move, valid_moves, *extra_validators):
		log.warning('Invalid Move')
		if self.phase == 'main':
			valid_moves = update_build_moves(self, valid_moves)

		move = yield valid_moves

	return move

def update_build_moves(self, moves):
	valid_moves = [m for m in moves if m['type'] != 'build']

	pl = self.current_player
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

	return valid_moves

def starting_phase(self):
	self.phase = 'setup'
	pl = self.current_player

	## PLACE SETTLEMENT
	valid_moves = [{
		'type': 'place',
		'build': 'settlement',
		'locations': [v.id_dict() for v in self.board.vertices 
		                                if v.is_free()]
	}]

	move = yield from get_move(self, valid_moves)

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

	move = yield from get_move(self, valid_moves)

	self.do_move(self.current_player, move)

def rolled_robber(self):
	self.waiting_for_discards = []

	for player in self.players:
		if len(player.cards_list) > 7:
			self.waiting_for_discards.append(player)

	def validate_discards(move, valid_move):
		if '_cards' not in move:
			return False

		try:
			if sum(move['_cards'].values()) != valid_move['_number']:
				return False

			p_cards = self.get_player(move['player_id']).cards
			d_cards = move['_cards']

			for res in d_cards:
				if res not in p_cards or p_cards[res] < d_cards[res]:
					return False

		except (TypeError, AttributeError, KeyError):
			return False

		return True

	while self.waiting_for_discards:
		valid_moves = [{
			'type': 'discard',
			'_number': len(player.cards_list) // 2,
			'player_id': player.id
		} for player in self.waiting_for_discards]
		move = yield from get_move(self, valid_moves, validate_discards)
		self.do_move(self.get_player(move['player_id']), move)

	yield from move_robber(self)

def move_robber(self):
	valid_moves = [{
		'type': 'move_robber',
		'locations': [hx.id_dict() for hx in self.board.land_hexes
		                                  if not hx.being_robbed],
	}]

	move = yield from get_move(self, valid_moves)
	self.action_number += 1
	[hx for hx in self.board.land_hexes if hx.being_robbed][0].being_robbed = False

	hx = self.board.Hex.get(move['location']['id'])
	hx.being_robbed = True
	target_vertices = {v for v in hx.vertices 
	                           if v.built 
	                           and v.built.owner != self.current_player}

	target_vertices = {v for v in target_vertices 
	 			      if max(val for val in v.built.owner.cards.values()) > 0}

	if target_vertices:
		valid_moves = [{
			'type': 'steal_from',
			'locations': [{
				'type': 'vertex',
				'id': list(vertex.id)
			} for vertex in target_vertices]
		}]

		move = yield from get_move(self, valid_moves)
		self.do_move(self.current_player, move)


def start_of_turn(self):
	self.phase = 'start_turn'
	self.can_trade = False

	valid_moves = [{
		'type': 'roll',
	}]

	move = yield from get_move(self, valid_moves)

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
	self.phase = 'main'
	self.can_trade = True

	pl = self.current_player
	played_dev_card = False
	player_dev_cards = list(self.current_player.dev_cards)

	#Actual turn!
	while True:
		valid_moves = [{
			'type': 'end_turn'
		}]

		valid_moves = update_build_moves(self, valid_moves)
		valid_moves = [m for m in valid_moves if m['type'] != 'dev_card']

		# Can only play
		if not played_dev_card:
			print("Current dev cards: {}".format(player_dev_cards))

			for card_name in set(card.name for card in player_dev_cards if card.playable(self)):
				valid_moves.append({
					'type': 'dev_card',
					'dev_card': card_name
				})
				
		move = yield from get_move(self, valid_moves)
			
		if move['type'] == 'dev_card':
			played_dev_card = True

			card = [card for card in player_dev_cards if card.playable(self) and card.name == move['dev_card']][0]
			card.played = True

			if move['dev_card'] == 'Knight':
				yield from move_robber(self)

			continue

		if move['type'] == 'end_turn':
			break
			
		self.do_move(pl, move)