(function( Catan, $, undefined ) {
	"use strict";
	Catan.Handlers = Catan.Handlers || {};

	Catan.players = [];
	Catan.action_number = -1;
	Catan.num_players = -1;
	Catan.active_trades = {};

	var Handlers = Catan.Handlers;
	var Trade = Catan.Trade;

	var num_to_string = {
		1: 'one',
		2: 'two',
		3: 'three',
		4: 'four',
		5: 'five',
	};

	Catan.queue =  {
		wait: {},
		todo: [],

		wait_for: function(evt) {
			this.wait[evt] = true;
			console.log('wait for '+evt);
		},
		finish: function(evt) {
			delete this.wait[evt];
			if(evt) {
				console.log(evt + ' finished');
			}

			while( $.isEmptyObject(this.wait) && this.todo.length ) {
				this.todo.shift()();
			}
		},
		add_front: function(func, args) {
			var that = this;
			this.todo.unshift(function() {
				try {
					console.log('running '+args[0].type);
				} catch (e) {
					console.log('running ?');
				}
				func.apply(that, args);
			});
			// Call finish so that func runs if wait is empty
			this.finish();
		},

		add: function(func, args) {
			var that = this;
			this.todo.push(function() {
				try {
					console.log('running '+args[0].type);
				} catch (e) {
					console.log('running ?');
				}
				func.apply(that, args);
			});
			// Call finish so that func runs if wait is empty
			this.finish();
		}
	};

	Handlers.game = function(msg) {
		Catan.num_players = msg.game.max_players;

		Handlers.board(msg.game);
		Handlers.players(msg.game);
		Catan.action_number = msg.game.action_number;

		if( msg.game.current_player ) {
			Handlers.current_player({
				player: msg.game.current_player
			});
		}

		if( !msg.game.started ) {
			Catan.send({
				'type': 'ready',
			});
		}
	};

	Handlers.board = function(msg) {
		if( !Catan.board ) {
			$('.trade_buttons').addClass(num_to_string[Catan.num_players-1]);

			for( var i = 1; i < Catan.num_players; i++ ) {
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

			$('.trade_window .other_players').addClass(num_to_string[Catan.num_players-1]);

			Catan.board = msg.board;
			Catan.create_board(Catan.board);
			Catan.resize();
		} else {
			Catan.update_board(msg.board);
		}
	};

	Handlers.can_trade = function(msg) {
		var can_trade = msg.can_trade;

		if( !can_trade ) {
			$('.trade_window').hide();
			$('#trade_button').removeClass('enabled');
			Catan.Trade.reset_trade();
		} else {
			$('#trade_button').addClass('enabled');
		}
	};

	Handlers.trade_offer = function(msg) {
		var trade = msg.trade;

		if( msg.player.id == Catan.local_player.id ) {
			// Ignore local players offers.
			return;
		}
		
		Catan.active_trades[msg.player.id] = trade;

		Trade.update_other_trades();
	};

	Handlers.trade = function(msg) {
		var trade = msg.trade;
		Catan.action_number = msg.action_number;

		Catan.players[trade.player_from.id] = trade.player_from;
		if( trade.player_to ) {
			Catan.players[trade.player_to.id] = trade.player_to;
		}

		update_players();

		delete Catan.active_trades[trade.player_from.id];

		if( trade.player_to !== null ) {
			delete Catan.active_trades[trade.player_to.id];
		}

		Trade.update_other_trades();

		if( trade.player_from.id == Catan.local_player.id 
		 || (trade.player_to && trade.player_to.id == Catan.local_player.id) ) {
			Trade.reset_trade();
		}
	};

	var update_players = function() {
		$('.player_row')
			.removeClass('blue')
			.removeClass('red')
			.removeClass('green')
			.removeClass('yellow')
			.addClass('unused');

		$('.resource_player_row').not('.template').remove();

		var ordered_players = [];

		for( var i in Catan.players ) {
			var player = Catan.players[i];
			ordered_players[player.id] = player;
		}

		Catan.players = ordered_players;

		for( var i in Catan.players ) {
			var player = Catan.players[i];
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

			if( player.player_id == Catan.local_player.player_id ) {
				Catan.local_player = player;

				for( var res_type in Catan.resource_types ) {
					$('.hand .card.'+res_type+' .count').text(player.cards[res_type]);
				}
			}
		}
	};


	Handlers.players = function(msg) {
		Catan.players = msg.players;
		update_players();
	};

	Handlers.current_player = function(msg) {
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

		$.each(Catan.players, function() {
			var player_section;
			var player_class;

			if( this.id == (Catan.local_player.id + 1)%Catan.num_players ) {
				// next player
				player_class = 'player1';
			} else if( this.id == (Catan.local_player.id - 1)%Catan.num_players ) {
				// previous player
				player_class = 'player'+(Catan.num_players-1);
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

	Handlers.moves = function(msg) {
		var moves = msg.moves;

		$('.enabled').not('#trade_button').removeClass('enabled').unbind();

		for( var i in moves ) {
			var move = moves[i];

			Catan.queue.add(function(move) {
				return function() {
					Catan.Moves[move.type](move)
				};
			}(move));
		}
	};

	Handlers.roll = function(msg) {
		var values = msg.values;

		Catan.queue.wait_for('dice_roll');

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

				Catan.queue.finish('dice_roll');
			});
		});
	};

	Handlers.resource_generation = function(msg) {
		$.each(msg.hexes, function() {
			Catan.queue.wait_for('resource_generation');
			var $hex = Catan.get_hex(this.id);
			$hex.addClass('generating')
			.delay(600).promise().done(function() {
				$hex.removeClass('generating');
				Catan.queue.finish('resource_generation');
			});
		});

		if( msg.hexes.length ) {
			Catan.queue.add_front(function() {
				Catan.queue.wait_for('resource_summary');
				$('.resource_summary').show().delay(2000).promise().done(function() {
					Catan.queue.finish('resource_summary');
					$('.resource_summary').hide();
				});
			});
		}
	};

	Handlers.assign_player = function(msg) {
		Catan.local_player = msg.player;
	};

}(window.Catan = window.Catan || {}, jQuery));