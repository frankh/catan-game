
var resize = function() {
	var min_height = 300;
	var height = $('.game_window').height();

	if( height < min_height ) {
		$('.game_window').height(min_height);
		height = min_height;
	} else if ($(window).height() > min_height) {
		$('.game_window').height("100%");
	}

	$('.game_window').width(height*(4/3));

	var hex_width = $('.game_hex').width();
	var hex_height = $('.game_hex').height();
	var font_size = hex_height / 5.5;

	var width_offset = hex_width * (0.05) + 1;
	var height_offset = hex_height * (0.50);

	$('td:nth-child(odd) .game_hex').css('top', height_offset + 'px');

	$('td:nth-child(odd) .game_hex').css('left', width_offset + 'px');
	$('td:nth-child(3) .game_hex').css('left', -1 * width_offset + 'px');
	$('td:nth-child(4) .game_hex').css('left', -2 * width_offset + 'px');
	$('td:nth-child(5) .game_hex').css('left', -3 * width_offset + 'px');

	//$('.hex_grid').css('left', 5.7 * width_offset+'px');
	$('.hex_grid').css('top', 1 * height_offset+'px');

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

	$('.game_interface').css('font-size', height/940 + 'em');
	$('.dice_value').css('font-size', 2*height/940 + 'em');
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

	$('.game_hex_row:nth-child(1) > td:nth-child(1) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(2) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(4) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(1) > td:nth-child(5) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(5) > td:nth-child(1) .hex_in2').addClass('sea_tile');
	$('.game_hex_row:nth-child(5) > td:nth-child(5) .hex_in2').addClass('sea_tile');

	var i = 1;
	$('.game_hex .hex_in2').not('.sea_tile').each(function() {
		$(this).find('.hex_text').text(i);
		i += 1;
	});
});

$(window).load(resize);
$(window).resize(resize);