"use strict";

var globals = this;

var PLAYERS;
var TURN_NUMBER = -1;
var NUM_PLAYERS = -1;
var ACTIVE_TRADES = {};
var HANDLERS = function(){};
globals.HANDLERS = HANDLERS;

HANDLERS.queue = {
	wait: {},
	todo: [],

	wait_for: function(evt) {
		this.wait[evt] = true;
	},
	finish: function(evt) {
		delete this.wait[evt];

		while( $.isEmptyObject(this.wait) && this.todo.length ) {
			this.todo.pop()();
		}
	},
	add: function(func, args) {
		var that = this;
		this.todo.push(function() {
			func.apply(that, args);
		});
		// Call finish so that func runs if wait is empty
		this.finish();
	}
};

var num_to_string = {
	1: 'one',
	2: 'two',
	3: 'three',
	4: 'four',
	5: 'five',
}

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
		$('.trade_buttons').addClass(num_to_string[NUM_PLAYERS-1]);

		for( var i = 1; i < NUM_PLAYERS; i++ ) {
			$('.trade_display.template')
			.clone()
			.removeClass('template')
			.addClass('player'+i)
			.appendTo('.trade_window .other_players')
			.find('want,give').addClass('player'+i);

			$('.trade_match_decline.template')
			.clone()
			.removeClass('template')
			.appendTo('.trade_buttons')
			.addClass('player'+i);
		}

		$('.trade_window .other_players').addClass(num_to_string[NUM_PLAYERS-1]);

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
	
	ACTIVE_TRADES[msg.player.id] = trade;

	TRADE.update_other_trades();
};

HANDLERS.trade = function(msg) {
	var trade = msg.trade;
	TURN_NUMBER = msg.turn;

	PLAYERS[trade.player_from.id] = trade.player_from;
	if( trade.player_to ) {
		PLAYERS[trade.player_to.id] = trade.player_to;
	}

	update_players();

	delete ACTIVE_TRADES[trade.player_from.id];
	delete ACTIVE_TRADES[trade.player_to.id];

	TRADE.update_other_trades();

	if( trade.player_from.id == PLAYER.id 
	 || (trade.player_to && trade.player_to.id == PLAYER.id) ) {
		TRADE.reset_trade();
	}
}


var update_players = function() {
	$('.player_row')
		.removeClass('blue')
		.removeClass('red')
		.removeClass('green')
		.removeClass('yellow')
		.addClass('unused');

	$('.resource_player_row').not('.template').remove();

	var ordered_players = [];

	for( var i in PLAYERS ) {
		var player = PLAYERS[i];
		ordered_players[player.id] = player;
	}

	PLAYERS = ordered_players;

	for( var i in PLAYERS ) {
		var player = PLAYERS[i];
		var player_row = $('.player_row.unused:eq(0)')
			.removeClass('unused')
			.addClass(player.color);
		player_row.find('.summary_player.name .name').text(player.name);
		player_row.find('.summary_player.name .icon').addClass(player.icon);
		player_row.find('.summary_player.cards').text(player.num_cards);
		player_row.find('.summary_player.points').text(player.victory_points);
		player_row.find('.summary_player.roads').text(player.longest_road);

		var resource_row = $('.resource_player_row.template')
			.clone()
			.removeClass('template')
			.attr('player_id', player.id)
			.addClass(player.color)
			.appendTo($('.resource_summary'));
		resource_row.find('.name').text(player.name);
		resource_row.find('.icon').addClass(player.icon);

		if( player.player_id == PLAYER.player_id ) {
			PLAYER = player;

			for( var res_type in RESOURCE_TYPES ) {
				$('.hand .card.'+res_type+' .count').text(player.cards[res_type]);
			}
		}
	}
}

HANDLERS.players = function(msg) {
	PLAYERS = msg.players;

	update_players();
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
		var player_class;

		if( this.id == (PLAYER.id + 1)%NUM_PLAYERS ) {
			// next player
			player_class = 'player1';
		} else if( this.id == (PLAYER.id - 1)%NUM_PLAYERS ) {
			// previous player
			player_class = 'player'+(NUM_PLAYERS-1);
		} else {
			//opposite
			player_class = 'player2';
		}

		player_section = $('.trade_display.'+player_class);
		player_section.attr('player_id', this.id);
		player_section.find('.name_bar')
			.text(this.name)
			.removeClass()
			.addClass('name_bar '+this.icon);

		$('.trade_match_decline.'+player_class).attr('player_id', this.id);
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

	HANDLERS.queue.wait_for('dice_roll');

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

			HANDLERS.queue.finish('dice_roll');
		});
	});
};

HANDLERS.resource_generation = function(msg) {
	console.log(msg);
	$.each(msg.hexes, function() {
		HANDLERS.queue.wait_for('resource_generation');
		var $hex = get_hex(this.id);
		$hex.addClass('generating')
		.delay(600).promise().done(function() {
			$hex.removeClass('generating');
			HANDLERS.queue.finish('resource_generation');
		});
	});

	if( msg.hexes.length ) {
		HANDLERS.queue.add(function() {
			HANDLERS.queue.wait_for('resource_summary');
			$('.resource_summary').show().delay(2000).promise().done(function() {
				HANDLERS.queue.finish('resource_summary');
				$('.resource_summary').hide();
			});
		});
	}
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