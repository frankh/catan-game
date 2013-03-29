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

var RESIZE_TIMER;

var resize = function() {
	_resize();
	//TODO overlay while waiting on resize timer
	
	// clearTimeout(RESIZE_TIMER);
	// RESIZE_TIMER = setTimeout(_resize, 200);
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

	var hex_width = $('.game_hex').width();
	var hex_height = $('.game_hex').height();
	var font_size = hex_height / 5.5;

	var width_offset = hex_width * (0.05) + 1;
	var height_offset = hex_height * (0.50);

	// Position hexes
	$('td:nth-child(odd) .game_hex').css('top', height_offset + 'px');

	$('td:nth-child(odd) .game_hex').css('left', width_offset + 'px');
	$('td:nth-child(3) .game_hex').css('left', -1 * width_offset + 'px');
	$('td:nth-child(4) .game_hex').css('left', -2 * width_offset + 'px');
	$('td:nth-child(5) .game_hex').css('left', -3 * width_offset + 'px');

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

	resize_vertices();
};

$(window).load(function() {
	for( var i = 1; i < 5; i++ ) {
		$('.game_hex_row.template td.template')
			.clone()
			.removeClass('template')
			.appendTo($('.game_hex_row.template'));
	}
	$('.game_hex_row.template td.template').removeClass('template');

	for( var i = 0; i < 5; i++ ) {
		$('.game_hex_row.template')
			.clone()
			.removeClass('template')
			.appendTo($('.hex_grid'));
	}

	$('.game_hex_row.template').remove();

	$('.game_hex_row:nth-child(1) > td:nth-child(1) .game_hex').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(2) .game_hex').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(4) .game_hex').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(5) .game_hex').addClass('sea_tile');
	$('.game_hex_row:nth-child(5) > td:nth-child(1) .game_hex').addClass('sea_tile');
	$('.game_hex_row:nth-child(5) > td:nth-child(5) .game_hex').addClass('sea_tile');

	$('.sea_tile').parents('td').find('.hex_vertex').remove();

	var i = 1;
	var hexes = $('.game_hex').not('.sea_tile');
	hexes.each(function() {
		$(this).attr('hex_id', HEX_CONV_MAP[i]);
		i += 1
	});

	var socket = new WebSocket("ws://localhost:8080/socket/temp/1");

	socket.onopen = function(){
	};

	var valid_tiles = {
		'desert'	: true,
		'fields'	: true,
		'forest'	: true,
		'pasture'	: true,
		'hills'		: true,
		'mountains'	: true,
	}

	socket.onmessage = function(msg) {
		var msg = JSON.parse(msg.data);
		if( msg.type == 'board' ) {
			var board = msg.board;
			create_board(board);
			resize();
		}
	}
});

$(window).load(resize);
$(window).resize(resize);

$(document).ready(function() {

});

function create_board(board) {
	for(var i in board.hexes) {
		var hex = board.hexes[i];
		var $hex = $('.game_hex[hex_id='+hex.id+']');

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

}
// Hex numbers start from top and spiral clockwise
//        __
//     __/1 \__
//  __/3 \__/5 \__
// /2 \__/4 \__/6 \
// \__/8 \__/10\__/
// /7 \__/9 \__/11\
// \__/13\__/15\__/
// /12\__/14\__/16\
// \__/17\__/19\__/
//    \__/18\__/
//       \__/
// Hex numbers start from top and spiral clockwise
//        __
//     __/1 \__
//  __/12\__/2 \__
// /11\__/13\__/3 \
// \__/18\__/14\__/
// /10\__/19\__/4 \
// \__/17\__/15\__/
// /9 \__/16\__/5 \
// \__/8 \__/6 \__/
//    \__/7 \__/
//       \__/
