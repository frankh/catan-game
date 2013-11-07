(function( Catan, $, undefined ) {
	"use strict";

	Catan.Trade = Catan.Trade || {};

	var Trade = Catan.Trade;
	Trade.current_trade = {};

	var num_to_string = {
		1: 'one',
		2: 'two',
		3: 'three',
		4: 'four',
		5: 'five',
	};
	
	Trade.reset_trade = function() {
		Trade.current_trade.give = {
			'wheat': 0,
			'clay': 0,
			'wood': 0,
			'ore': 0,
			'wool': 0,
		};
		Trade.current_trade.want = {
			'wheat': 0,
			'clay': 0,
			'wood': 0,
			'ore': 0,
			'wool': 0,
		};

		Trade.update_give_icons();
		Trade.update_want_icons();
	};

	Trade.sum_dict = function(d) {
		var total = 0;
		for( var key in d ) {
			total += d[key];
		}
		return total;
	}

	Trade.current_trade.give_total = function() {
		return Trade.sum_dict(Trade.current_trade.give);
	};

	Trade.current_trade.want_total = function() {
		return Trade.sum_dict(Trade.current_trade.want);
	};

	function get_exchange_rate_for_res(res) {
		var rate = 4;

		if( $.inArray('general', Catan.local_player.ports) >= 0 ) {
			rate = 3;
		}

		if( $.inArray(res, Catan.local_player.ports) >= 0 ) {
			rate = 2;
		}

		return rate;
	}

	Trade.update_port_trade = function() {
		if( Catan.local_player === undefined ) {
			return;
		}

		var give_res;

		for( var res in Catan.resource_types ) {
			$('.port_trade_button').removeClass(res);
		}
		$('.port_trade_button').removeClass('enabled');

		if( $.inArray('general', Catan.local_player.ports) >= 0 ) {
			$('.port_trade_button').addClass('general');
		} else {
			$('.port_trade_button').removeClass('general');
		}

		for( var res in Trade.current_trade.give ) {
			if( Trade.current_trade.give[res] > 0 ) {
				if( give_res !== undefined ) {
					return;
				}

				give_res = res;
			}
		}

		if( give_res === undefined ) {
			return;
		}

		var rate = get_exchange_rate_for_res(give_res);

		if( rate == 2 ) {
			$('.port_trade_button').removeClass('general');
			$('.port_trade_button').addClass(give_res);
		}

		if( Catan.local_player.cards[give_res] >= rate && Trade.current_trade.want_total() == 1) {
			$('.port_trade_button').addClass('enabled');
		}
	}

	Trade.update_give_icons = function() {
		var res_num = 0;

		$('.give_section .sel_res')
			.removeClass()
			.addClass('sel_res');

		for( var res in Trade.current_trade.give ) {
			var count = Trade.current_trade.give[res];

			for( var i = 0; i < count; i++ ) {
				$('.give_section .sel_res:eq('+res_num+')').addClass(res);
				res_num++;
			}
		}

		$('.give_section .avail').each(function() {
			var restype = $(this).attr('restype');

			$(this).find('span').text(Catan.local_player.cards[restype] - Trade.current_trade.give[restype]);
		});

		Trade.update_port_trade();
	}

	Trade.update_want_icons = function() {
		var res_num = 0;

		$('.want_section .sel_res')
			.removeClass()
			.addClass('sel_res');

		for( var res in Trade.current_trade.want ) {
			var count = Trade.current_trade.want[res];

			for( var i = 0; i < count; i++ ) {
				$('.want_section .sel_res:eq('+res_num+')').addClass(res);
				res_num++;
			}
		}

		Trade.update_port_trade();
	}

	Trade.update_other_trades = function() {
		$('.trade_display').find('.resource').remove();

		for( var player_id in Catan.active_trades ) {
			var trade = Catan.active_trades[player_id];
			var $trade = $('.trade_display[player_id='+player_id+']');

			$.each(['give', 'want'], function() {
				var res_num = 0;
				var can_match = true;
				var is_matched = true;

				var opp = {
					give: 'want',
					want: 'give'
				}

				for( var res in trade[this] ) {
					for( var i = 0; i < trade[this][res]; i++ ) {
						res_num++;
						var $res = $('<div class="resource '+res+' '+num_to_string[res_num]+'"></div>');
						$trade.find('.'+this).append($res);
					}

					if( this == 'want' && Catan.local_player.cards[res] < trade[this][res] ) {
						can_match = false;
					}

					if( trade[this][res] != Trade.current_trade[opp[this]][res] ) {
						is_matched = false;
					}
				}


				if( res_num == 0 ) {
					can_match = false;
					is_matched = false;
				}


				if( is_matched ) {
					$('.trade_buttons .match')
					.text('Confirm')
					.removeClass('disabled')
					.addClass('confirm');
				} else if( can_match ) {
					$('.trade_buttons .match')
					.text('Match')
					.removeClass('disabled')
					.removeClass('confirm');
				} else {
					$('.trade_buttons .match')
					.text('Match')
					.removeClass('confirm')
					.addClass('disabled');
				}
			});
		}
	};

	Trade.send_trade = function (player_id, port) {
		if( player_id === undefined ) {
			player_id = null;
		}

		if( port === undefined ) {
			port = false;
		}

		Catan.send({
			'type': 'trade',
			'trade': {
				'give': Trade.current_trade.give,
				'want': Trade.current_trade.want,
				'player_id': player_id,
				'port': port,
				'turn': Catan.action_number,
			}
		});

		Trade.update_other_trades();
	}

	Trade.reset_trade();

	$(document).ready(function() {
		$('#trade_button').click(function() {
			if( !$(this).hasClass('enabled') ) {
				return;
			}

			$('.trade_window').show();
			Trade.reset_trade();
		})

		$('.hide_trade').click(function() {
			$('.trade_window').hide();
		})

		$('.give_section .sel_res').live('click', function() {
			var $this = $(this);
			for( var res in Catan.resource_types ) {
				if( $this.hasClass(res) ) {
					$this.removeClass(res);
					Trade.current_trade.give[res] -= 1;
				}
			}

			Trade.update_give_icons();
			Trade.send_trade();
		});

		$('.want_section .sel_res').live('click', function() {
			var $this = $(this);
			for( var res in Catan.resource_types ) {
				if( $this.hasClass(res) ) {
					$this.removeClass(res);
					Trade.current_trade.want[res] -= 1;
				}
			}

			Trade.update_want_icons();
			Trade.send_trade();
		});

		var pending_port_trade = null;
		$('.port_trade_button.enabled').live('click', function() {
			var give_res;
			var want_res;

			for( var res in Trade.current_trade.give ) {
				if( Trade.current_trade.give[res] > 0 ) {
					give_res = res;
				}
			}

			for( var res in Trade.current_trade.want ) {
				if( Trade.current_trade.want[res] > 0 ) {
					want_res = res;
				}
			}

			var rate = get_exchange_rate_for_res(give_res);

			if( pending_port_trade 
			 && Trade.current_trade.give == pending_port_trade.give
			 && Trade.current_trade.want == pending_port_trade.want ) {
				Trade.send_trade(null, true);
			} else {
				Trade.reset_trade();

				Trade.current_trade.give[give_res] = rate;
				Trade.current_trade.want[want_res] = 1;

				Trade.update_give_icons();
				Trade.update_want_icons();

				pending_port_trade = Catan.clone_dict(Trade.current_trade);
			}
		});

		$('.give_section .avail_resources .avail').live('click', function() {
			var restype = $(this).attr('restype');

			if( Catan.local_player.cards[restype] - Trade.current_trade.give[restype] <= 0 
			 || Trade.current_trade.give_total() >= 5
			 || Trade.current_trade.want[restype]) {
				return;
			}

			Trade.current_trade.give[restype] += 1;
			Trade.update_give_icons();
			Trade.send_trade();

		});

		$('.want_section .avail_resources .avail').live('click', function() {
			var restype = $(this).attr('restype');

			if( Trade.current_trade.want_total() >= 5
			 || Trade.current_trade.give[restype]) {
				return;
			}

			Trade.current_trade.want[restype] += 1;
			Trade.update_want_icons();
			Trade.send_trade();
		});

		$('.trade_buttons .match:not(.disabled)').live('click', function() {
			// Match the target player's trade
			var $trade_buttons = $(this).closest('.trade_match_decline');
			var player_id = parseInt($trade_buttons.attr('player_id'));
			Trade.current_trade.want = $.extend({}, Catan.active_trades[player_id].give);
			Trade.current_trade.give = $.extend({}, Catan.active_trades[player_id].want);

			Trade.update_want_icons();
			Trade.update_give_icons();
			Trade.send_trade();
		});

		$('.trade_buttons .match.confirm:not(.disabled)').live('click', function() {
			// Confirm target player's trade.
			var $trade_buttons = $(this).closest('.trade_match_decline');
			var player_id = parseInt($trade_buttons.attr('player_id'));

			Trade.send_trade(player_id);
		});
	});
}(window.Catan = window.Catan || {}, jQuery));
