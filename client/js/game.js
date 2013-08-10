(function( Catan, $, undefined ) {
	Catan.board = null;
	Catan.current_player = null;

	Catan.resource_types = {
		'wheat': true,
		'clay': true,
		'wood': true,
		'ore': true,
		'wool': true,
	};

	Catan.preload = function() {
		var resources = [
			'res/human_icon.png',
			'res/ai_icon.png',
			'res/gradiant.bmp',
			'res/ports.png',
			'res/Dice.png',
			'res/dicelarge.png',
			'res/DiceAnim.png',
			'res/watermark_want.png',
			'res/watermark_give.png',
			'res/cities.png',
			'res/cities_highlight.png',
			'res/settlements.png',
			'res/settlements_highlight.png',
			'res/roads_highlight.png',
			'res/roads.png',
			'res/robber.png',
			'res/hex-desert.bmp',
			'res/hex-pasture.bmp',
			'res/hex-hills.bmp',
			'res/hex-mountains.bmp',
			'res/hex-forest.bmp',
			'res/hex-fields.bmp',
			'res/playerview-icons.bmp',
			'res/human_icon.png',
			'res/buildbuttons.png',
			'res/actionbuttons.png',
			'res/materialcards.png',
			'res/DevCard.png',
			'res/ai_icon.png',
			'res/divider.bmp',
			'res/actionbuttons.png',
			'res/resource_icons.png',
			'res/divider_large.bmp',
			'res/scroll-button-down.bmp',
			'res/scroll-button-up.bmp',
			'res/scroll-slider-vert.bmp',
			'res/15 - build drop.wav',
			'res/01 - start turn.wav',
			'res/03 - dice roll.wav',
			'res/02 - end turn.wav',
		];

		var done = 0;
		var queue = $.when();

		for( var i in resources ) {
			var res = resources[i];

			var func = function(res) {
				return function() {
					$.ajax({
						url: res,
						success: function() {
							done++;
							console.log("Downloaded "+res+" ("+done+"/"+resources.length+")");
						}
					});
				};
			};

			queue.done(func(res));
		}

		queue.done(function() {
			$('audio').each(function() {
				this.load();
			});
		});
	};

	Catan.play_sound = function(sound) {
		var aud = $('#audio-'+sound)[0];
		if( !aud.muted ) {
			aud.load();
			aud.play();
		}
	}
	
	var SOCKET;

	$(window).load(function() {
		if( !('WebSocket' in window) ) {
			$('.overlay').text('Browser not supported');
			return;
		}

		var sockaddr = document.domain;
		var sockprot = 'ws:';
		var game_token = '';
		if( document.domain == 'localhost' ) {
			sockaddr += ':8080';
		}
		if (document.location.protocol === "https:") {
			sockprot = "wss:";
		}

		if (location.hash) {
			game_token = location.hash.slice(1);
		}

		SOCKET = new WebSocket(sockprot+"//"+sockaddr+document.location.pathname+"socket/"+game_token);

		$('.overlay').text('Connecting');

		SOCKET.onopen = function(){
			$('.overlay').text('Connected');
		};

		SOCKET.onmessage = function(msg) {
			var msg = JSON.parse(msg.data);

			console.log('queue: '+msg.type);
			
			Catan.queue.add(Catan.Handlers[msg.type], [msg]);
		}
	});

	Catan.send = function(msg) {
		SOCKET.send(JSON.stringify(msg));
	}

	$(window).load(Catan.resize);
	$(window).resize(Catan.resize);

	$(document).ready(function() {
		Catan.preload();

		$('.trade_window').hide();
		$('.resource_summary').hide();

		// Prevent noises from stuff that was built on page load.
		$('audio').each(function() {
			this.muted = true;
		});

		// Add click class when mouse pressed on something.
		$('.enabled,.button').live('mousedown', function() {
			$(this).addClass('clicked');
		});

		$(window).mouseup(function() {
			$('.clicked').removeClass('clicked');
		});

	});

	Catan.get_hex = function(hex_id) {
		return $('.hex[hex_id='+hex_id+']');
	};

	Catan.get_path = function(path_id) {
		return $('.path[path_id='+path_id+']');
	};

	Catan.get_path_id = function(path) {
		var path_id = $(path).attr('path_id');

		return path_id;
	};

	Catan.position_message = function() {
		$('.message_box').position({
			my: 'right bottom',
			at: 'right bottom',
			of: $('.game_play_area')
		});
	};

	Catan.show_message = function(msg) {
		$('.message_box').show().text(msg);
		Catan.position_message();
	};

	Catan.clear_message = function() {
		$('.message_box').hide();
	};

	Catan.clone_dict = function(dict) {
		return $.extend({}, dict);
	}

}(window.Catan = window.Catan || {}, jQuery));
