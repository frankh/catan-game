(function( Catan, $, undefined ) {
	Catan.Moves = Catan.Moves || {};

	var Moves = Catan.Moves;
	
	Moves.place = function(move) {
		if( move.build == 'settlement' ) {
			var place_vertices = $();
			Catan.show_message('Place your starting settlement');

			for( var j in move.locations ) {
				var location = move.locations[j];
				var vertex = Catan.get_vertex(location.id);

				vertex.addClass('build');
				vertex.addClass('build_settlement');
				vertex.addClass(Catan.local_player.color);

				place_vertices = place_vertices.add(vertex);
			}

			place_vertices.click(function() {
				place_vertices.unbind();
				place_vertices.removeClass('build');
				place_vertices.removeClass('build_settlement');
				place_vertices.removeClass(Catan.local_player.color);

				Catan.build_on_vert($(this), 'settlement', Catan.local_player.color);
				Catan.clear_message();

				Catan.send({
					type: 'do_move',
					move: {
						type: 'place',
						build: 'settlement',
						location: {
							'type': 'vertex',
							'id': Catan.get_vertex_id($(this)),
						},
					},
				});
			});
		} else if ( move.build == 'road' ) {
			var place_paths = $();
			Catan.show_message('Now place a road adjacent to that settlement');

			for( var j in move.locations ) {
				var path = move.locations[j];
				path = Catan.get_path(path.id);

				path.addClass('build');
				path.addClass(Catan.local_player.color);

				place_paths = place_paths.add(path);
			}

			place_paths.click(function() {
				place_paths.unbind();
				place_paths.removeClass('build');
				place_paths.removeClass(Catan.local_player.color);

				Catan.build_road($(this), Catan.local_player.color);
				Catan.clear_message();

				Catan.send({
					type: 'do_move',
					move: {
						type: 'place',
						build: 'road',
						location: {
							'type': 'path',
							'id': Catan.get_path_id($(this)),
						},
					},
				});
			});
		}
	};

	Moves.discard = function(move) {
		$.each(move, function() {
			if( this.player_id == Catan.local_player.id ) {
				Catan.show_mesasge("You must discard "+move.number+" cards");
			}
		});
	}

	Moves.steal_from = function(move) {
		Catan.show_message("Choose a player to steal from.");

		$.each(move.locations, function() {
			var vertex = Catan.get_vertex(this.id);

			vertex.addClass('steal_from');

			vertex.click(function() {
				$('.steal_from').removeClass('steal_from').unbind('click');

				Catan.send({
					type: 'do_move',
					move: {
						type: 'steal_from',
						location: {
							'type': 'vertex',
							'id': Catan.get_vertex_id(this),
						},
					},
				});

			})
		});
	}

	Moves.roll = function(move) {
		Catan.play_sound('start_turn');
		Catan.show_message(Catan.local_player.name + ', it is now your turn');
		$('.actions .roll')
			.addClass('enabled')
			.click(function() {
				Catan.clear_message();

				Catan.send({
					type: 'do_move',
					move: {
						type: 'roll'
					}
				});
				$(this).removeClass('enabled').unbind();

				$('.rolling_die').addClass('rolling').addClass('show');
				Catan.play_sound('dice_roll');
		 });
	};

	Moves.end_turn = function(move) {
		$('.actions .end_turn')
			.addClass('enabled')
			.click(function() {
				Catan.send({
					type: 'do_move',
					move: {
						type: 'end_turn'
					}
				});
				$(this).removeClass('enabled').unbind();
				Catan.play_sound('end_turn');
				Catan.clear_message();
				$('.enabled').not('#trade_button').removeClass('enabled').unbind();
		 });
	};

	Moves.move_robber = function(move) {
		Catan.show_message('Choose where to place the robber');

		for( var i in move.locations) {
			var hex = move.locations[i];
			var $hex = $('.hex[hex_id='+hex.id+']');

			$hex.click(function(hex) {
				return function() {
					Catan.clear_message();

					Catan.send({
						type: 'do_move',
						move: {
							type: 'move_robber',
							location: hex,
						}
					});
				};
			}(hex));
		}
	};

	Moves.build = function(move) {
		if( move.build == 'dev_card' ) {
			Moves.build_dev_card(move);
			return;
		}

		var start_build = function(move) {
			return function() {
				if( !(move.locations.length) ) {
					Catan.show_message('There is nowhere to place this '+move.build);
					return;
				} 
				
				Catan.show_message('Select where to build your '+move.build);

				var place_locations = $();
				for( var j in move.locations ) {
					var location = move.locations[j];

					if( location.type == 'vertex' ) {
					 	location = Catan.get_vertex(location.id);
						location.addClass('build_'+move.build);
					 } else if( location.type == 'path' ) {
					 	location = Catan.get_path(location.id);
					 }

					location.addClass(Catan.local_player.color);

					place_locations = place_locations.add(location);
				}

				// function wrapper to keep move and location in scope
				var do_build = function(move) {
					return function() {
						place_locations.unbind();
						place_locations.removeClass('build');
						place_locations.removeClass('build_'+move.build);
						place_locations.removeClass(Catan.local_player.color);

						Catan.clear_message();

						var loc_type = 'path';

						if( $(this).is('.vertex') ) {
							loc_type = 'vertex';
							Catan.build_on_vert($(this), move.build, Catan.local_player.color);
						} else {
							Catan.build_road($(this), Catan.local_player.color);
						}

						Catan.send({
							type: 'do_move',
							move: {
								type: 'build',
								build: move.build,
								location: {
									type: loc_type,
									id: loc_type == 'path' ? Catan.get_path_id($(this)) : Catan.get_vertex_id($(this))
								}
							}
						});
					}
				};
				place_locations.unbind('click');
				place_locations.addClass('build');
				place_locations.addClass(Catan.local_player.color);
				place_locations.addClass(move.build);
				place_locations.click(do_build(move));
			};
		};


		$('.build .'+move.build)
			.addClass('enabled')
			.click(start_build(move));
	};

	Moves.build_dev_card = function(move) {
		$('.build .'+move.build)
			.addClass('enabled')
			.click(function() {
				Catan.send({
					type: 'do_move',
					move: {
						type: 'build',
						build: 'dev_card'
					}
				});
				$(this).unbind('click');
				$(this).removeClass('enabled');
			});
	};

	Moves.dev_card = function(move) {
		$('.actions .dev_cards')
			.addClass('enabled')
			.click(function() {
				$('#dev_card_view').show()
			});
	};

	Moves.choose_resource = function(move) {
		$('#resource_selector').show();
		$('#resource_selector .card').addClass('disabled');

		$(move.resources).each(function () {
			$('#resource_selector .card.'+this).removeClass('disabled');
		});
	};
}(window.Catan = window.Catan || {}, jQuery));
