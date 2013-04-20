"use strict";

var globals = this;

globals.SOUNDS = [];

var build_on_vert = function($vert, building, color) {
	$vert.removeClass('build');
	if( !$vert.hasClass('built_'+building) ) {
		play_sound('build');
		$vert.removeClass('unbuilt');
		$vert.removeClass('build_settlement');
		$vert.addClass('built_'+building);
		$vert.addClass(color);
		$vert.addClass('built');
		$vert.clone().appendTo($vert.parent());
		$vert.remove();
	}
}

var build_road = function($path, color) {
	$path.removeClass('build');
	if( !$path.hasClass('built') ) {
		play_sound('build');
		$path.addClass('built');
		$path.addClass(color);
	}
}


