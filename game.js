
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

	var ratio = $('.game_board').width() / $('.game_board').height();

	$('.game_current_player_notification').text(ratio);
	var hex_width = $('.game_hex').width();
	var hex_height = $('.game_hex').height();

	$('td:nth-child(odd) .game_hex').css('top', hex_height * (0.50) + 'px');

	var width_offset = hex_width * (0.05) + 1;

	$('td:nth-child(odd) .game_hex').css('left', width_offset + 'px');
	$('td:nth-child(3) .game_hex').css('left', -1 * width_offset + 'px');
	$('td:nth-child(4) .game_hex').css('left', -2 * width_offset + 'px');
	$('td:nth-child(5) .game_hex').css('left', -3 * width_offset + 'px');
};

$(window).load(function() {
	for( var i = 0; i < 5; i++ ) {
		$('.game_hex_row.template')
			.clone(true)
			.removeClass('template')
			.appendTo($('.hex_grid'));
	}
});

$(window).load(resize);
$(window).resize(resize);

