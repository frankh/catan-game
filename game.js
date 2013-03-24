
var resize = function() {
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

	// Position vertices
	$('.hex_vertex').each(function() {
		var $this = $(this);
		var hex = $this.parent().find('.hex_in2');
		var hex_position = parseInt(hex.attr('hex_position'));
		var number = parseInt($this.attr('number'));

		var new_size = hex.width()*0.10;

		$this.width(new_size);
		$this.height(new_size);
		$this.find('.vertex_text').css('font-size', new_size/24 + 'em');
		// Vertical centering
		$this.find('.vertex_text').css('padding-top', new_size/10+'px');

		// Always add 1 and 4
		if( number == 1 ) {
			$this.position({
				my: 'center',
				at: 'left+20%',
				of: hex
			});
		} else if( number == 4 ) {
			$this.position({
				my: 'center',
				at: 'right-20%',
				of: hex
			});
		} 
		// Only add 2 if on top or left
		else if( number == 2 && [1,2,3,7,12].indexOf(hex_position) >= 0 ) {
			$this.position({
				my: 'center',
				at: 'center-15% top+1.8%',
				of: hex
			});
		} 
		// Only add 3 if on top or right
		else if( number == 3 && [1,5,6,11,16].indexOf(hex_position) >= 0 ) {
			$this.position({
				my: 'center',
				at: 'center+15% top+1.8%',
				of: hex
			});
		}
		// Only add 5 if on bottom right
		else if( number == 5 && [16,19,18].indexOf(hex_position) >= 0 ) {
			$this.position({
				my: 'center',
				at: 'center+15% bottom-1.8%',
				of: hex
			});
		}
		// Only add 6 if on bottom left
		else if( number == 6 && [12,17,18].indexOf(hex_position) >= 0 ) {
			$this.position({
				my: 'center',
				at: 'center-15% bottom-1.8%',
				of: hex
			});
		} else {
			$this.remove();
		}
	});
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

	$('.template').remove();

	$('.game_hex_row:nth-child(1) > td:nth-child(1) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(2) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(4) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(5) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(5) > td:nth-child(1) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(5) > td:nth-child(5) .hex_in2').addClass('sea_tile');

	$('.sea_tile').parents('td').find('.hex_vertex').remove();

	var i = 1;
	var hexes = $('.game_hex .hex_in2').not('.sea_tile');
	hexes.each(function() {
		$(this).attr('hex_position', i);
		i += 1
	});

	// Initialise vertexes.
	resize();

	i = 1;
	$('.hex_vertex').each(function() {
		$(this).attr('vertex_position', i);
		$(this).find('.vertex_text').text(i);
		i += 1;
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

			hexes.each(function() {
				var tile = board.tiles.pop();

				if( !(tile in valid_tiles) ) {
					alert('Invalid tile!');
				}

				if( tile != 'desert' ) {
					var value = board.values.pop();

					$(this).find('.hex_text').text(value);
					if( value == 6 || value == 8 ) {
						$(this).find('.hex_text').addClass('high_yield');
					}
				}

				$(this).addClass('hex_'+tile);
			});

			resize();
		}
	}
});

$(window).load(resize);
$(window).resize(resize);

$(document).ready(function() {

})