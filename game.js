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
	position_message();
};

var SOCKET;

$(window).load(function() {
	if( !('WebSocket' in window) ) {
		$('.overlay').text('Browser not supported');
		return;
	}

	SOCKET = new WebSocket("ws://localhost:8080/socket/temp/1");

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
		}

		handlers[msg.type](msg);
	}
});

$(window).load(resize);
$(window).resize(resize);

$(document).ready(function() {
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

function update_board(board) {
	for( var i in board.vertices ) {
		var vert = board.vertices[i];
		var $vert = get_vertex(vert.id);

		if( vert.blocked || vert.built ) {
			$vert.removeClass('unbuilt');
		}

		if( vert.built ) {
			$vert.addClass('built_'+vert.built.building+'_'+vert.built.owner.color);
		}
	}
}