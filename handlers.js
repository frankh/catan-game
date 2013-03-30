"use strict";

var globals;

(function(global) {
	globals = global;
})(this);

var handler_game =function(msg) {
	handler_board(msg.game);
	handler_players(msg.game);

	SOCKET.send(JSON.stringify({
		'type': 'ready',
	}));
};

var handler_board =function(msg) {
	if( !globals.BOARD ) {
		globals.BOARD = msg.board;
		create_board(globals.BOARD);
		resize();
	} else {
		update_board(msg.board);
	}
};

var handler_players =function(msg) {
	if( !globals.PLAYER ) {
		globals.PLAYERS = msg.players;
		
		for( var i in globals.PLAYERS ) {
			globals.PLAYER = globals.PLAYERS[i];
			var player = globals.PLAYER;
			var player_row = $('.player_row.unused:eq(0)')
			                    .removeClass('unused')
			                    .addClass('player_'+player.color);

		}
	}
};

var handler_moves =function(msg) {
	var moves = msg.moves;
	for( var i in moves ) {
		var move = moves[i];

		if( move.type == 'place' ) {
			if( move.build == 'settlement' ) {
				var place_vertices = $();
				show_message('Place your starting settlement');

				for( var j in move.locations ) {
					var location = move.locations[j];
					var vertex = get_vertex(location.id);

					vertex.addClass('build');
					vertex.addClass('settlement');
					vertex.addClass(globals.PLAYER.color);

					place_vertices = place_vertices.add(vertex);
				}

				place_vertices.click(function() {
					place_vertices.unbind();
					place_vertices.removeClass('build');
					place_vertices.removeClass('settlement');
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
		}
	}
};

var handler_forced_action = function(msg) {
};

var handler_assign_player = function(msg) {
	globals.PLAYER = msg.player;
};

var handler_available_moves = function(msg) {
};

var position_message = function() {
	$('.message_box').position({
		my: 'right bottom',
		at: 'right bottom',
		of: $('.game_play_area')
	});
}

var show_message = function(msg) {
	$('.message_box').show().text(msg);
	position_message();
}

var clear_message = function() {
	$('.message_box').hide();
}