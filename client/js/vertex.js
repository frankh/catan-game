create_vertex = function(vert) {
	var vert_id = vert.id;
	var vertex = $('.vertex.template').clone();
	vertex.removeClass('template');
	vertex.appendTo($('.vertexes'));
	vertex.find('.vertex_text').text(vert.probability);
	vertex.attr('vertex_id', vert_id);
	vertex.addClass('unbuilt');
};

get_vertex = function(vert_id) {
	return $('.vertex[vertex_id='+vert_id+']');
}

get_vertex_id = function(vert) {
	var vert_id = $(vert).attr('vertex_id');

	return vert_id;
}

resize_vertices = function() {
	$('.vertexes .vertex').not('.template').each(function() {
		var vertex = $(this);

		var vert_id = vertex.attr('vertex_id');
		var vert = {
			id: vert_id.split('_')
		}

		var hexes = [];

		for( var j in vert.id ) {
			var hex_id = vert.id[j];

			if( hex_id > 100 ) {
				var from_id = parseInt(hex_id.toString().slice(1,3), 10);
				var to_id = parseInt(hex_id.toString().slice(3,5), 10);
				hexes.push({
					sea: true,
					from: $('.hex[hex_id='+from_id+']'),
					to: $('.hex[hex_id='+to_id+']')
				});
			} else {
				hexes.push($('.hex[hex_id='+hex_id+']'));
			}
		}

		// Make sure the first hex isn't sea.
		while( hexes[0].sea ) {
			var hex = hexes[0];
			hexes = hexes.slice(1);
			hexes.push(hex);
		}

		var $hex = hexes[0];
		var pos_hex = $hex.find('.hex_in2');
		var new_size = pos_hex.width()*0.10;

		vertex.width(new_size);
		vertex.height(new_size);
		vertex.find('.vertex_text').css('font-size', new_size/24 + 'em');
		// Vertical centering
		vertex.find('.vertex_text').css('padding-top', new_size/10+'px');

		vertex.position({
			my: 'center',
			at: 'center',
			of: pos_hex
		});

		var pos = function(elem) {
			return {
				left: elem.offset().left + elem.width() / 2,
				top: elem.offset().top + elem.height() / 2
			}
		}

		var get_other = function(other) {
			if( other.sea ) {
				if( other.from.attr('hex_id') == $hex.attr('hex_id') ) {
					other = other.to;
				} else {
					other = other.from;
				}
			}

			return other;
		}

		var left_of = function(other) {
			other = get_other(other);
			return (pos(other).left - pos($hex).left) > 10;
		}
		var above = function(other) {
			other = get_other(other);			
			return (pos(other).top - pos($hex).top) > 10;
		}
		var right_of = function(other) {
			other = get_other(other);
			return (pos(other).left - pos($hex).left) < -10;
		}
		var below = function(other) {
			other = get_other(other);			
			return (pos(other).top - pos($hex).top) < -10;
		}

		// console.log(vert_id);
		// console.log(hexes);


		var left1 = left_of(hexes[1]);
		var left2 = left_of(hexes[2]);
		var right1 = right_of(hexes[1]);
		var right2 = right_of(hexes[2]);
		var above1 = above(hexes[1]);
		var above2 = above(hexes[2]);
		var below1 = below(hexes[1]);
		var below2 = below(hexes[2]);

		var middle_right = function() {
			vertex.position({
				my: 'center',
				at: 'right-20%',
				of: pos_hex
			});
		};

		var middle_left = function() {
			vertex.position({
				my: 'center',
				at: 'left+20%',
				of: pos_hex
			});
		};

		var bottom_right = function() {
			vertex.position({
				my: 'center',
				at: 'center+15% bottom-1.8%',
				of: pos_hex
			});
		};

		var top_right = function() {
			vertex.position({
				my: 'center',
				at: 'center+15% top+1.8%',
				of: pos_hex
			});
		};

		var bottom_left = function() {
			vertex.position({
				my: 'center',
				at: 'center-15% bottom-1.8%',
				of: pos_hex
			});
		};

		var top_left = function() {
			vertex.position({
				my: 'center',
				at: 'center-15% top+1.8%',
				of: pos_hex
			});
		};

		// Got bored...special case sea tiles.
		var sea_vert_map = {
			'1_10101_10102' : top_right,
			'2_10102_10203' : top_right,
			'3_10203_10303' : top_right,
			'3_10303_10304' : middle_right,
			'3_4_10304'     : bottom_right,
			'4_10304_10405' : middle_right,
			'4_5_10405'     : bottom_right,
			'5_10405_10505' : middle_right,
			'5_10505_10506' : bottom_right,
			'5_6_10506'     : bottom_left,
			'6_10506_10607' : bottom_right,
			'6_7_10607'     : bottom_left,
			'7_10607_10707' : bottom_right,
			'7_10707_10708' : bottom_left,
			'8_10708_10809' : bottom_left,
			'9_10809_10909' : bottom_left,
			'9_10909_10910' : middle_left,
			'9_10_10910'    : top_left,
			'10_10910_11011': middle_left,
			'10_11_11011'   : top_left,
			'11_11011_11111': middle_left,
			'11_11111_11112': top_left,
			'11_12_11112'   : top_right,
			'12_10112_11112': top_left,
			'1_10101_10112' : top_left
		}
		// console.log([left1,left2,right1,right2,above1,above2,below1,below2].join());

		if        ( vert_id in sea_vert_map ) {
			// Easier to just special case these.
			sea_vert_map[vert_id]();
		} else if ( left1 && left2 ) {
			middle_right();
		} else if ( right1 && right2 ) {
			middle_left()
		} else if ( left1 || left2 ) {
			if( above1 ) {
				bottom_right()
			} else {
				top_right();
			}
		} else if ( right1 || right2 ) {
			if( above1 ) {
				bottom_left();
			} else {
				top_left();
			}
		} else {
			vertex.remove();
		}
	});
};