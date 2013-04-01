// convert from our js order (number increases by row)
// to server side order (number increases in a spiral)

HEX_CONV_MAP = {
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

var BOARD;
var PLAYER;
var RESIZE_TIMER;

var resize = function() {
	if( !BOARD )
		return;

	$('.overlay').show();
	clearTimeout(RESIZE_TIMER);
	RESIZE_TIMER = setTimeout(function() {
		_resize();
		$('.overlay').hide();
	}, 200);
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

	resize_vertices();
	resize_paths();
	position_message();
};

var SOCKET;

$(window).load(function() {
	if( !('WebSocket' in window) ) {
		$('.overlay').text('Browser not supported');
		return;
	}

	var sockaddr = document.domain;
	if( document.domain == 'localhost' ) {
		sockaddr += ':8080';
	}

	SOCKET = new WebSocket("ws://"+sockaddr+"/socket/temp/1");

	$('.overlay').text('Connecting');

	SOCKET.onopen = function(){
		$('.overlay').text('Connected');
	};

	var valid_tiles = {
		'desert'	: true,
		'fields'	: true,
		'forest'	: true,
		'pasture'	: true,
		'hills'		: true,
		'mountains'	: true,
	}

	SOCKET.onmessage = function(msg) {
		var msg = JSON.parse(msg.data);

		handlers = {
			game           : handler_game,
			moves          : handler_moves,
			board          : handler_board,
			forced_action  : handler_forced_action,
			assign_player  : handler_assign_player,
			available_moves: handler_available_moves,
			current_player : handler_current_player,
			roll           : handler_roll,
		}

		handlers[msg.type](msg);
	}
});

$(window).load(resize);
$(window).resize(resize);

$(document).ready(function() {
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

	// Add click class when mouse pressed on something.
	$('.enabled').live('mousedown', function() {
		$(this).addClass('clicked');
	});

	$(window).mouseup(function() {
		$('.clicked').removeClass('clicked');
	});

});

var get_path = function(path_id) {
	return $('.path[path_id='+path_id+']');
}

var get_path_id = function(path) {
	var path_id = $(path).attr('path_id');

	return path_id;
}

function create_path(path) {
	var path_id = path.id;
	var path = $('.path.template').clone();
	path.removeClass('template');
	path.appendTo($('.vertexes .paths'));
	path.attr('path_id', path_id);
}

function resize_paths() {
	"use strict";

	$('.path').not('.template').each(function() {
		var path = $(this);
		var path_id = path.attr('path_id');

		var vert_ids = path_id.split('__');
		var vert1 = get_vertex(vert_ids[0]);
		var vert2 = get_vertex(vert_ids[1]);

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
}

function create_board(board) {
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
		create_vertex(vert);
	}

	for( var i in board.paths ) {
		var path = board.paths[i];

		create_path(path);
	}

	update_board(board);
}

function update_board(board) {
	for( var i in board.vertices ) {
		var vert = board.vertices[i];
		var $vert = get_vertex(vert.id);

		if( vert.blocked || vert.built ) {
			$vert.removeClass('unbuilt');
		} else {
			$vert.addClass('unbuilt');
		}

		if( vert.built ) {
			build_on_vert($vert, vert.built.building, vert.built.owner.color);
		} 
	}

	for( var i in board.paths ) {
		var path = board.paths[i];
		var $path = get_path(path.id);

		if( path.built ) {
			build_road($path, path.built.owner.color);
		} else {
			// Potential bug for not cleaning up color class here.
			$path.removeClass('built');
		}
	}
}