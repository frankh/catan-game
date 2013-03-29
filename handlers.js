handler_board =function(msg) {
	BOARD = msg.board;
	create_board(BOARD);
	resize();
};


handler_forced_action = function(msg) {
};
handler_assign_player = function(msg) {
};

handler_available_moves = function(msg) {
};