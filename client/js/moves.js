var MOVES = function() {}

MOVES.place = function(move) {
	if( move.build == 'settlement' ) {
		var place_vertices = $();
		show_message('Place your starting settlement');

		for( var j in move.locations ) {
			var location = move.locations[j];
			var vertex = get_vertex(location.id);

			vertex.addClass('build');
			vertex.addClass('build_settlement');
			vertex.addClass(globals.PLAYER.color);

			place_vertices = place_vertices.add(vertex);
		}

		place_vertices.click(function() {
			place_vertices.unbind();
			place_vertices.removeClass('build');
			place_vertices.removeClass('build_settlement');
			place_vertices.removeClass(globals.PLAYER.color);

			build_on_vert($(this), 'settlement', globals.PLAYER.color);
			clear_message();

			globals.SOCKET.send(JSON.stringify({
				type: 'do_move',
				move: {
					type: 'place',
					build: 'settlement',
					location: {
						'type': 'vertex',
						'id': get_vertex_id($(this)),
					},
				},
			}));
		});
	} else if ( move.build == 'road' ) {
		var place_paths = $();
		show_message('Now place a road adjacent to that settlement');

		for( var j in move.locations ) {
			var path = move.locations[j];
			path = get_path(path.id);

			path.addClass('build');
			path.addClass(globals.PLAYER.color);

			place_paths = place_paths.add(path);
		}

		place_paths.click(function() {
			place_paths.unbind();
			place_paths.removeClass('build');
			place_paths.removeClass(globals.PLAYER.color);

			build_road($(this), globals.PLAYER.color);
			clear_message();

			globals.SOCKET.send(JSON.stringify({
				type: 'do_move',
				move: {
					type: 'place',
					build: 'road',
					location: {
						'type': 'path',
						'id': get_path_id($(this)),
					},
				},
			}));
		});
	}
};

MOVES.roll = function(move) {
	play_sound('start_turn');
	show_message(PLAYER.name + ', it is now your turn');
	$('.actions .roll')
		.addClass('enabled')
		.click(function() {
			clear_message();

			globals.SOCKET.send(JSON.stringify({
				type: 'do_move',
				move: {
					type: 'roll'
				}
			}));
			$(this).removeClass('enabled').unbind();

			$('.rolling_die').addClass('rolling').addClass('show');
			play_sound('dice_roll');
	 });
};

MOVES.end_turn = function(move) {
	$('.actions .end_turn')
		.addClass('enabled')
		.click(function() {
			globals.SOCKET.send(JSON.stringify({
				type: 'do_move',
				move: {
					type: 'end_turn'
				}
			}));
			$(this).removeClass('enabled').unbind();
			play_sound('end_turn');
			clear_message();
			$('.enabled').not('#trade_button').removeClass('enabled').unbind();
	 });
};

MOVES.move_robber = function(move) {
	show_message('Choose where to place the robber');

	for( var i in move.locations) {
		var hex = move.locations[i];
		var $hex = $('.hex[hex_id='+hex.id+']');

		$hex.click(function(hex) {
			return function() {
				clear_message();

				globals.SOCKET.send(JSON.stringify({
					type: 'do_move',
					move: {
						type: 'move_robber',
						location: hex,
					}
				}));
			};
		}(hex));
	}
};

MOVES.build = function(move) {
	var start_build = function(move) {
		return function() {
			if( !(move.locations.length) ) {
				show_message('There is nowhere to place this '+move.build);
				return;
			} 
			
			show_message('Select where to build your '+move.build);

			var place_locations = $();
			for( var j in move.locations ) {
				var location = move.locations[j];

				if( location.type == 'vertex' ) {
				 	location = get_vertex(location.id);
					location.addClass('build_'+move.build);
				 } else if( location.type == 'path' ) {
				 	location = get_path(location.id);
				 }

				location.addClass(globals.PLAYER.color);

				place_locations = place_locations.add(location);
			}

			// function wrapper to keep move and location in scope
			var do_build = function(move) {
				return function() {
					place_locations.unbind();
					place_locations.removeClass('build');
					place_locations.removeClass('build_'+move.build);
					place_locations.removeClass(globals.PLAYER.color);

					clear_message();

					var loc_type = 'path';

					if( $(this).is('.vertex') ) {
						loc_type = 'vertex';
						build_on_vert($(this), move.build, globals.PLAYER.color);
					} else {
						build_road($(this), globals.PLAYER.color);
					}

					globals.SOCKET.send(JSON.stringify({
						type: 'do_move',
						move: {
							type: 'build',
							build: move.build,
							location: {
								type: loc_type,
								id: loc_type == 'path' ? get_path_id($(this)) : get_vertex_id($(this))
							}
						}
					}));
				}
			};
			place_locations.unbind('click');
			place_locations.addClass('build');
			place_locations.addClass(globals.PLAYER.color);
			place_locations.addClass(move.build);
			place_locations.click(do_build(move));
		};
	};


	$('.build .'+move.build)
		.addClass('enabled')
		.click(start_build(move));
};