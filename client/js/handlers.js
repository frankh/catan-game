"use strict";

var globals = this;

var handler_game =function(msg) {
	handler_board(msg.game);
	handler_players(msg.game);

	if( msg.game.current_player ) {
		handler_current_player({
			player: msg.game.current_player
		});
	}

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

globals.RESOURCE_TYPES = {
	'wheat': true,
	'clay': true,
	'wood': true,
	'ore': true,
	'wool': true,
}

var handler_players =function(msg) {
	$('.player_row')
		.removeClass('blue')
		.removeClass('red')
		.removeClass('green')
		.removeClass('yellow')
		.addClass('unused');

	globals.PLAYERS = msg.players;
	
	for( var i in globals.PLAYERS ) {
		var player = globals.PLAYERS[i];
		var player_row = $('.player_row.unused:eq(0)')
		                    .removeClass('unused')
		                    .addClass(player.color);
		player_row.find('.summary_player.name .name').text(player.name);
		player_row.find('.summary_player.name .icon').addClass(player.icon);
		player_row.find('.summary_player.name .icon').addClass(player.icon);
		player_row.find('.summary_player.cards').text(player.num_cards);
		player_row.find('.summary_player.points').text(player.victory_points);
		player_row.find('.summary_player.roads').text(player.longest_road);

		if( player.player_id == globals.PLAYER.player_id ) {
			globals.PLAYER = player;

			for( var res_type in globals.RESOURCE_TYPES ) {
				$('.hand .card.'+res_type+' .count').text(player.cards[res_type]);
			}
		}
	}
};

var handler_current_player = function(msg) {
	var player = msg.player;

	var $bar = $('.game_current_player_notification');

	$bar.removeClass('blue')
	    .removeClass('red')
	    .removeClass('green')
	    .removeClass('yellow')
        .addClass(msg.player.color);

	$bar.find('.name').text(player.name);
	$bar.find('.icon').removeClass('ai')
	                  .removeClass('human')
	                  .addClass(player.icon);
};

var handler_moves =function(msg) {
	var moves = msg.moves;

	$('.enabled').removeClass('enabled').unbind();

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
		}

		if( move.type == 'roll' ) {
			globals.SOUNDS.push(new Audio("../res/01 - start turn.wav").play());
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
					globals.SOUNDS.push(new Audio("../res/03 - dice roll.wav").play());
			 });
		}

		if( move.type == 'end_turn' ) {
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
					globals.SOUNDS.push(new Audio("../res/02 - end turn.wav").play());
					clear_message();
					$('.enabled').removeClass('enabled').unbind();
			 });
		}

		if( move.type == 'build' ) {
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
		}
	}
};

var handler_roll = function(msg) {
	var values = msg.values;

	$('.corner_dice').css('visibility', 'hidden');
	$('.roll_dice').addClass('show');

	$('.rolling_die')
	   .addClass('rolling')
	   .delay(1000)
	   .promise()
	   .done(function() {
		$('.rolling_die').removeClass('rolling')
		$('.rolling_die:eq(0)').addClass('value_'+values[0]);
		$('.rolling_die:eq(1)').addClass('value_'+values[1]);

		$('.rolling_die')
		   .delay(1000)
		   .promise()
		   .done(function() {
		   	$(this).add($('.corner_dice .die'))
		           .removeClass('value_1')
		           .removeClass('value_2')
		           .removeClass('value_3')
		           .removeClass('value_4')
		           .removeClass('value_5')
		           .removeClass('value_6');
		    $(this).parent().removeClass('show')

			$('.corner_dice .die:eq(0)').addClass('value_'+values[0]);
			$('.corner_dice .die:eq(1)').addClass('value_'+values[1]);

			$('.corner_dice .dice_value').text(msg.result);
			$('.corner_dice').css('visibility', 'visible');
		});
	});
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