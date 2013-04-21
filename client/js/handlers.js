"use strict";

var globals = this;

var TURN_NUMBER = -1;
var NUM_PLAYERS = -1;
var HANDLERS = function(){};
globals.HANDLERS = HANDLERS;

HANDLERS.game = function(msg) {
	NUM_PLAYERS = msg.game.max_players;

	HANDLERS.board(msg.game);
	HANDLERS.players(msg.game);
	TURN_NUMBER = msg.game.turn;

	if( msg.game.current_player ) {
		HANDLERS.current_player({
			player: msg.game.current_player
		});
	}

	if( !msg.game.started ) {
		SOCKET.send(JSON.stringify({
			'type': 'ready',
		}));
	}
};

HANDLERS.can_trade = function(msg) {
	var can_trade = msg.can_trade;

	if( !can_trade ) {
		$('.trade_window').hide();
		$('#trade_button').removeClass('enabled');
		TRADE.reset_trade();
	} else {
		$('#trade_button').addClass('enabled');
	}
}

HANDLERS.board = function(msg) {
	if( !globals.BOARD ) {
		for( var i = 1; i < NUM_PLAYERS; i++ ) {
			$('.trade_display.template')
				.clone()
				.removeClass('template')
				.addClass('player'+i)
				.appendTo('.trade_window .other_players')
				.find('wants,needs').addClass('player'+i)
		}

		switch(NUM_PLAYERS-1) {
			case 1: $('.trade_window .other_players').addClass('one'); break;
			case 2: $('.trade_window .other_players').addClass('two'); break;
			case 3: $('.trade_window .other_players').addClass('three'); break;
			default: break;
		}

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

HANDLERS.trade_offer = function(msg) {
	var trade = msg.trade;

	if( msg.player.id == PLAYER.id ) {
		return;
	}

	//TODO

}

HANDLERS.players = function(msg) {
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

HANDLERS.current_player = function(msg) {
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

	$.each(PLAYERS, function() {
		var player_section;

		if( this.id == (PLAYER.id + 1)%NUM_PLAYERS ) {
			// next player
			player_section = $('.trade_display.player1');
		} else if( this.id == (PLAYER.id - 1)%NUM_PLAYERS ) {
			// previous player
			player_section = $('.trade_display.player'+(NUM_PLAYERS-1));
		} else {
			//opposite
			player_section = $('.trade_display.player2');
		}

		player_section.attr('player_id', this.id);
		player_section.find('.name_bar')
			.text(this.name)
			.removeClass()
			.addClass('name_bar '+this.icon);
	});
};

HANDLERS.moves = function(msg) {
	var moves = msg.moves;

	$('.enabled').not('#trade_button').removeClass('enabled').unbind();

	for( var i in moves ) {
		var move = moves[i];

		MOVES[move.type](move);

	}
};

HANDLERS.roll = function(msg) {
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

HANDLERS.resource_generation = function(msg) {
	console.log(msg);
};

HANDLERS.assign_player = function(msg) {
	globals.PLAYER = msg.player;
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