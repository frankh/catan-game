(function( Catan, $, undefined ) {
	"use strict";

	Catan.build_on_vert = function($vert, building, color) {
		$vert.removeClass('build');
		if( !$vert.hasClass('built_'+building) ) {
			Catan.play_sound('build');
			$vert.removeClass('unbuilt');
			$vert.removeClass('built_settlement');
			$vert.addClass('built_'+building);
			$vert.addClass(color);
			$vert.addClass('built');
			$vert.clone().appendTo($vert.parent());
			$vert.remove();
		}
	}

	Catan.build_road = function($path, color) {
		$path.removeClass('build');
		if( !$path.hasClass('built') ) {
			Catan.play_sound('build');
			$path.addClass('built');
			$path.addClass(color);
		}
	}
}(window.Catan = window.Catan || {}, jQuery));

