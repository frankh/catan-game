(function( Catan, $, undefined ) {

	// convert from our js order (number increases by row)
	// to server side order (number increases in a spiral)
	var HEX_CONV_MAP = {
		1 :  1,
		2 : 11,
		3 : 12,
		4 : 13,
		5 :  2,
		6 :  3,
		7 : 10,
		8 : 18,
		9 : 19,
		10: 14,
		11:  4,
		12:  9,
		13: 17,
		14: 16,
		15: 15,
		16:  5,
		17:  8,
		18:  7,
		19:  6
	}

	var resize_timer;

	Catan.resize = function() {
		if( !Catan.board )
			return;

		$('.overlay').show();
		clearTimeout(resize_timer);
		resize_timer = setTimeout(function() {
			_resize();
			$('.overlay').hide();
		}, 10);
	}

	var _resize = function() {
		var min_height = 350;
		var height = $('.game_window').height();

		// Don't shrink after a certain point
		if( height < min_height ) {
			$('.game_window').height(min_height);
			height = min_height;
		} else if ($(window).height() > min_height) {
			$('.game_window').height("100%");
			height = $('.game_window').height();
		}

		// Lock ratio
		$('.game_window').width(height*(4/3));

		var hex_width = $('.hex').width();
		var hex_height = $('.hex').height();
		var font_size = hex_height / 5.5;

		var width_offset = hex_width * (0.05) + 1;
		var height_offset = hex_height * (0.50);

		// Position hexes
		$('td:nth-child(odd) .hex').css('top', height_offset + 'px');
		$('td:nth-child(odd) .hex').css('left', width_offset + 'px');
		$('td:nth-child(3) .hex').css('left', -1 * width_offset + 'px');
		$('td:nth-child(4) .hex').css('left', -2 * width_offset + 'px');
		$('td:nth-child(5) .hex').css('left', -3 * width_offset + 'px');

		// Center the grid
		$('.hex_grid').css('top', 1 * height_offset+'px');

		// Fix hex text sizes
		$('.hex_text').each(function() {
			var two_chars = $(this).text().trim().length == 2;
			
			var font_offset_x = font_size * 0.3;

			if( two_chars ) {
				font_offset_x = font_size * 0.6;
			}

			$(this).css('top',  hex_height * 0.5 - font_size * 0.65 +'px');
			$(this).css('left',  hex_width * 0.5 - font_offset_x +'px');
			$(this).css('font-size',  font_size+'px');
		});

		// Fix other text sizes
		$('.game_interface').css('font-size', height/940 + 'em');
		$('.dice_value').css('font-size', 2*height/940 + 'em');
		$('.game_current_player_notification').css('font-size', 1.5*height/940 + 'em');
		$('.trade_window').css('font-size', 1.2*height/940 + 'em');
		$('.resource_summary').css('font-size', 1*height/940 + 'em');

		Catan.resize_vertices();
		Catan.resize_paths();
		Catan.resize_ports();
		Catan.position_message();
	};

	Catan.create_port = function(port) {
		var $port = $('.port.template').clone();
		$port.removeClass('template')
			 .appendTo('.game_board')
			 .addClass(port.port_type)
			 .attr('port_id', port.id)
			 .attr('path_id', port.path.id)
			 .attr('hex_id', port.hex.id);
	};

	Catan.resize_ports = function() {
		$('.port').not('.template').each(function() {
			var $path = Catan.get_path($(this).attr('path_id'));
			var $hex = Catan.get_hex($(this).attr('hex_id')).find('.hex_in2');

			var hp = $hex.offset();
			var pp = $path.offset();

			hp.top += $hex.height() / 2;
			hp.left += $hex.width() / 2;

			pp.top += $path.height() / 2;
			pp.left += $path.width() / 2;

			var top = (pp.top - hp.top) < -5;
			var bottom = (pp.top - hp.top) > 5;
			var left = (pp.left - hp.left) < -5;
			var right = (pp.left - hp.left) > 5;
			var hmid = !left && !right;
			var vmid = !top && !bottom;

			var my, at;
			
			at = 'center center'

			if( top && left  ) {
				my = 'right+14% bottom+25%';
				$(this).addClass('top_left');
			} else if( top && hmid  ) {
				my = 'center bottom';
				$(this).addClass('top_mid');
			} else if( top && right ) {
				my = 'left-14% bottom+25%';
				$(this).addClass('top_right');
			} else if( bottom && left ) {
				my = 'right+14% top-25%';
				$(this).addClass('bottom_left');
			} else if( bottom && hmid ) {
				my = 'center top';
				$(this).addClass('bottom_mid');
			} else if( bottom && right ) {
				my = 'left-14% top-25%';
				$(this).addClass('bottom_right');
			}

			$(this).position({
				my: my,
				at: at,
				of: $path,
			});
		});
	};

	Catan.create_path = function(path) {
		"use strict";

		var path_id = path.id;
		var path = $('.path.template').clone();
		path.removeClass('template');
		path.appendTo($('.vertexes .paths'));
		path.attr('path_id', path_id);
	};

	Catan.resize_paths = function() {
		"use strict";

		$('.path').not('.template').each(function() {
			var path = $(this);
			var path_id = path.attr('path_id');

			var vert_ids = path_id.split('__');
			var vert1 = Catan.get_vertex(vert_ids[0]);
			var vert2 = Catan.get_vertex(vert_ids[1]);

			var new_size = vert1.width() * 1.7;
			path.width(new_size);
			path.height(new_size);

			var v1pos = vert1.offset();
			v1pos.left += vert1.width() / 2;
			v1pos.top += vert1.height() / 2;

			var v2pos = vert2.offset();
			v2pos.left += vert2.width() / 2;
			v2pos.top += vert2.height() / 2;

			path.css({
				top: (v1pos.top + v2pos.top) / 2 - (path.height() / 2),
				left: (v1pos.left + v2pos.left) / 2 - (path.width() / 2),
				position: 'absolute'
			});

			var ppos = path.offset();
			ppos.left += path.width() / 2;
			ppos.top += path.height() / 2;

			var top = function(pos) {
				if( pos === false )
					return false;

				if( pos.top - ppos.top < -5 )
					return pos;

				return false;
			};
			var left = function(pos) {
				if( pos === false )
					return false;

				if( pos.left - ppos.left < -5 )
					return pos;

				return false;
			};
			var bottom = function(pos) {
				if( pos === false )
					return false;

				if( pos.top - ppos.top > 5 )
					return pos;

				return false;
			};
			var right = function(pos) {
				if( pos === false )
					return false;

				if( pos.left - ppos.left > 5 )
					return pos;

				return false;
			};

			if( top(left(v1pos)) && bottom(right(v2pos)) 
			 || top(left(v2pos)) && bottom(right(v1pos)) ) {
				path.addClass('trailing');
			} else if( bottom(left(v1pos)) && top(right(v2pos)) 
			        || bottom(left(v2pos)) && top(right(v1pos)) )  {
				path.addClass('leading');
			} else {
				path.addClass('flat');
			}
		});
	};

	Catan.create_board = function(board) {
		for( var i = 1; i < 5; i++ ) {
			$('.hex_row.template td.template')
				.clone()
				.removeClass('template')
				.appendTo($('.hex_row.template'));
		}
		$('.hex_row.template td.template').removeClass('template');

		for( var i = 0; i < 5; i++ ) {
			$('.hex_row.template')
				.clone()
				.removeClass('template')
				.appendTo($('.hex_grid'));
		}

		for( var i = 0; i < 4; i++ ) {
			$('.player_row.template')
			    .clone()
			    .removeClass('template')
			    .appendTo('.summary')
		}

		$('.player_row.template').remove();
		$('.hex_row.template').remove();

		$('.hex_row:nth-child(1) > td:nth-child(1) .hex').addClass('sea_tile');
		$('.hex_row:nth-child(1) > td:nth-child(2) .hex').addClass('sea_tile');
		$('.hex_row:nth-child(1) > td:nth-child(4) .hex').addClass('sea_tile');
		$('.hex_row:nth-child(1) > td:nth-child(5) .hex').addClass('sea_tile');
		$('.hex_row:nth-child(5) > td:nth-child(1) .hex').addClass('sea_tile');
		$('.hex_row:nth-child(5) > td:nth-child(5) .hex').addClass('sea_tile');

		$('.sea_tile').parents('td').find('.vertex').remove();

		var i = 1;
		var hexes = $('.hex').not('.sea_tile');
		hexes.each(function() {
			$(this).attr('hex_id', HEX_CONV_MAP[i]);
			i += 1
		});
		for(var i in board.hexes) {
			var hex = board.hexes[i];
			var $hex = $('.hex[hex_id='+hex.id+']');

			$hex.addClass('hex_'+hex.tile);
			var hex_text = $hex.find('.hex_text').text(hex.value);

			if( hex.value == 6 || hex.value == 8 ) {
				hex_text.addClass('high_yield');
			}
		}

		for( var i in board.vertices ) {
			var vert = board.vertices[i];
			Catan.create_vertex(vert);
		}

		for( var i in board.paths ) {
			var path = board.paths[i];
			Catan.create_path(path);
		}

		for( var i in board.ports ) {
			var port = board.ports[i];
			Catan.create_port(port);
		}

		Catan.update_board(board);
		$('audio').each(function() {
			this.muted = false;
		});
	};

	Catan.update_board = function(board) {
		$('.being_robbed').removeClass('being_robbed');
		for( var i in board.hexes ) {
			var hex = board.hexes[i];
			var $hex = $('.hex[hex_id='+hex.id+']');

			if( hex.being_robbed ) {
				$hex.addClass('being_robbed');
			}
		}

		for( var i in board.vertices ) {
			var vert = board.vertices[i];
			var $vert = Catan.get_vertex(vert.id);

			if( vert.blocked || vert.built ) {
				$vert.removeClass('unbuilt');
			} else {
				$vert.addClass('unbuilt');
			}

			if( vert.built ) {
				Catan.build_on_vert($vert, vert.built.building, vert.built.owner.color);
			} 
		}

		for( var i in board.paths ) {
			var path = board.paths[i];
			var $path = Catan.get_path(path.id);

			if( path.built ) {
				Catan.build_road($path, path.built.owner.color);
			} else {
				// Potential bug for not cleaning up color class here.
				$path.removeClass('built');
			}
		}
	};
}(window.Catan = window.Catan || {}, jQuery));