"use strict";

var globals = this;

globals.SOUNDS = [];

var build_on_vert = function($vert, building, color) {
	$vert.removeClass('build');
	if( !$vert.hasClass('built_'+building) ) {
		globals.SOUNDS.push(new Audio("../res/15 - build drop.wav").play());
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
		globals.SOUNDS.push(new Audio("../res/15 - build drop.wav").play());
		$path.addClass('built');
		$path.addClass(color);
	}
}


