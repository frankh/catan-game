var handler_game =function(msg) {
	handler_board(msg.game);
	handler_players(msg.game);

	SOCKET.send(JSON.stringify({
		'type': 'ready',
	}));
};

var handler_board =function(msg) {
	if( !BOARD ) {
		BOARD = msg.board;
		create_board(BOARD);
		resize();
	} else {
		update_board(msg.board);
	}
};

var handler_players =function(msg) {
	if( !PLAYER ) {
		PLAYERS = msg.players;
		
		for( var i in PLAYERS ) {
			PLAYER = PLAYERS[i];
			var player = PLAYER;
			var player_row = $('.player_row.unused:eq(0)')
			                    .removeClass('unused')
			                    .addClass('player_'+player.color);

		}
	}
};

var handler_moves =function(msg) {
	moves = msg.moves;
	var place_vertices = $();
	for( var i in moves ) {
		var move = moves[i];

		if( move.type == 'place' ) {
			if( move.build == 'settlement' ) {
				show_message('Place your starting settlement');
				$(window).bind('settlement_built', clear_message);

				var build_class = 'build_settlement_'+PLAYER.color;
				var vertex = get_vertex(move.location.id);
				vertex.addClass(build_class);
				place_vertices = place_vertices.add(vertex);

				var do_move = function(move, vertex) {
					return function() {
						place_vertices.unbind();
						place_vertices.removeClass(build_class);

						vertex.removeClass('unbuilt')
						      .addClass('built_settlement_'+PLAYER.color);

						new Audio("res/15 - build drop.wav").play();
						$(window).trigger('settlement_built');

						SOCKET.send(JSON.stringify({
							type: 'do_move',
							move: move,
						}));
					}
				}

				vertex.click(do_move(move, vertex));
			}
		}
	}
};

var handler_forced_action = function(msg) {
};

var handler_assign_player = function(msg) {
	PLAYER = msg.player;
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