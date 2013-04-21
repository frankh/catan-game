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

var preload = function() {
	resources = [
		'../res/human_icon.png',
		'../res/ai_icon.png',
		'../res/gradiant.bmp',
		'../res/ports.png',
		'../res/Dice.png',
		'../res/dicelarge.png',
		'../res/DiceAnim.png',
		'../res/watermark_want.png',
		'../res/watermark_give.png',
		'../res/cities.png',
		'../res/cities_highlight.png',
		'../res/settlements.png',
		'../res/settlements_highlight.png',
		'../res/roads_highlight.png',
		'../res/roads.png',
		'../res/robber.png',
		'../res/hex-desert.bmp',
		'../res/hex-pasture.bmp',
		'../res/hex-hills.bmp',
		'../res/hex-mountains.bmp',
		'../res/hex-forest.bmp',
		'../res/hex-fields.bmp',
		'../res/playerview-icons.bmp',
		'../res/human_icon.png',
		'../res/buildbuttons.png',
		'../res/actionbuttons.png',
		'../res/materialcards.png',
		'../res/DevCard.png',
		'../res/ai_icon.png',
		'../res/divider.bmp',
		'../res/actionbuttons.png',
		'../res/resource_icons.png',
		'../res/divider_large.bmp',
		'../res/scroll-button-down.bmp',
		'../res/scroll-button-up.bmp',
		'../res/scroll-slider-vert.bmp',
		'../res/15 - build drop.wav',
		'../res/01 - start turn.wav',
		'../res/03 - dice roll.wav',
		'../res/02 - end turn.wav',
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

var play_sound = function(sound) {
	var aud = $('#audio-'+sound)[0];
	if( !aud.muted ) {
		aud.load();
		aud.play();
	}
}

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
	resize_ports();
	position_message();
};

var SOCKET;

$(window).load(function() {
	if( !('WebSocket' in window) ) {
		$('.overlay').text('Browser not supported');
		return;
	}

	var sockaddr = document.domain;
	var sockprot = 'ws:';
	if( document.domain == 'localhost' ) {
		sockaddr += ':8080';
	}
	if (document.location.protocol === "https:") {
    	sockprot = "wss:";
	}

	SOCKET = new WebSocket(sockprot+"//"+sockaddr+"/socket/temp/1");

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
		
		HANDLERS[msg.type](msg);
	}
});

$(window).load(resize);
$(window).resize(resize);

$(document).ready(function() {
	preload();

	$('.trade_window').hide();

	$('audio').each(function() {
		this.muted = true;
	});

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

var get_hex = function(hex_id) {
	return $('.hex[hex_id='+hex_id+']');
}

var get_path = function(path_id) {
	return $('.path[path_id='+path_id+']');
}

var get_path_id = function(path) {
	var path_id = $(path).attr('path_id');

	return path_id;
}

function create_port(port) {
	var $port = $('.port.template').clone();
	$port.removeClass('template')
		 .appendTo('.game_board')
		 .addClass(port.port_type)
		 .attr('port_id', port.id)
		 .attr('path_id', port.path.id)
		 .attr('hex_id', port.hex.id);

}

function resize_ports() {
	$('.port').not('.template').each(function() {
		var $path = get_path($(this).attr('path_id'));
		var $hex = get_hex($(this).attr('hex_id')).find('.hex_in2');

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

		if     ( top && left  ) {
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

	for( var i in board.ports ) {
		var port = board.ports[i];

		create_port(port);
	}

	update_board(board);
	$('audio').each(function() {
		this.muted = false;
	});
}

function update_board(board) {
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