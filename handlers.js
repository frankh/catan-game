var handler_game =function(msg) {
	handler_board(msg.game);
	handler_players(msg.game);

	SOCKET.send(JSON.stringify({
		'type': 'ready',
	}));
};

var handler_board =function(msg) {
	BOARD = msg.board;
	create_board(BOARD);
	resize();
};

var handler_players =function(msg) {
	PLAYERS = msg.players;
	
	for( var i in PLAYERS ) {
		PLAYER = PLAYERS[i];
		var player = PLAYER;
		var player_row = $('.player_row.unused:eq(0)')
		                    .removeClass('unused')
		                    .addClass('player_'+player.color);

	}
};

var handler_moves =function(msg) {
	moves = msg.moves;
	
	for( var i in moves ) {
		var move = moves[i];

		if( move.type == 'place' ) {
			show_message('Place your starting settlement');
			$(window).bind('settlement_built', clear_message);

			var build_class = 'build_settlement_'+PLAYER.color;

			var unbuilt_vertexes = $('.hex_vertex.unbuilt');
			unbuilt_vertexes.addClass(build_class);
			unbuilt_vertexes.click(function() {
				unbuilt_vertexes.unbind();
				unbuilt_vertexes.removeClass(build_class);

				$(this).removeClass('unbuilt')
				       .addClass('built_settlement_'+PLAYER.color);

			})


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