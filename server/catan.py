import json
import log
from pprint import pformat

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.websocket
from tornado.escape import url_unescape

import dice_gen
import settings

from game import (
	Player,
	Game
)

log = log.getLogger('catan')

class DefaultGame(Game):

	def __init__(self, max_players=1):
		from inspect import getmembers, isfunction
		import board_validators
		validators_list = [name for (name, value) in getmembers(board_validators) if isfunction(value)]
		super().__init__(max_players=max_players, validators=validators_list)
		self.dice_gen = dice_gen.DeckDiceGen()
	
global games, game_tokens
games = set()
game_tokens = {}

class Socket(tornado.websocket.WebSocketHandler):
	player = None

	def open(self, token):
		global game_tokens
		token = url_unescape(token)
		if token not in game_tokens:

			if "default" in game_tokens:
				token = "default"
			else:
				self.write_message(json.dumps({
					'type': 'error',
					'error': {
						'type': 'Invalid Token',
						'msg': 'Invalid Token'
					}
				}))
				print(game_tokens)
				self.close()
				return

		game = game_tokens[token]
		self.game = game
		self.player = game.get_player_from_token(token)
		self.player.connection = self

		self.write_message(json.dumps({
			'type': 'assign_player',
			'player': self.player.as_dict(),
		}));

		self.write_message(json.dumps({
			'type': 'game',
			'game': game.as_dict(),
		}));

		game.recv_move(self.player, {'type': 'reconnect'})
		self.write_message(json.dumps({
			'type': 'can_trade',
			'can_trade': game.can_trade,
		}));

		log.debug(self.player.name+" joined "+game.name)

	def on_message(self, message):
		try:
			log.debug(str('temp')+'>'+pformat(json.loads(message)['type']))
		except:
			log.debug(str('temp')+'>'+message)

		message = json.loads(message)

		if( message['type'] == 'ready' ):
			self.game.set_ready(self.player)

		elif( message['type'] == 'do_move' ):
			move = message['move']
			self.game.recv_move(self.player, move)
		elif( message['type'] == 'trade' ):
			self.game.recv_trade(self.player, message['trade'])
			# { 'type': 'trade', 'trade': {'give': {}, 'want': {}, 'turn': 1, 'player': None} }
		
	def write_message(self, message):
		try:
			log.debug(str('temp')+'<'+pformat(json.loads(message)['type']))
		except:
			log.debug(str('temp')+'<'+message)

		super().write_message(message);


	def on_close(self):
		if self.player:
			self.player.connection = None

class Create(tornado.web.RequestHandler):
	def post(self):
		secret = self.get_argument('secret')

		if( secret != settings.secret ):
			raise tornado.web.HTTPError(403)

		players = json.loads(self.get_argument('players'))
		game_name = self.get_argument('name')

		game = Game(name=game_name, max_players=len(players))

		global games, game_tokens
		games.add(game)

		for player in players:
			pl_obj = Player(player['token'], player['name'], game)
			game_tokens[player['token']] = game
			print(player['token'])
			game.add_player(pl_obj)



socket_app = tornado.web.Application([
	(r"/socket/(?P<token>\w+)/?", Socket),
	(r"/create", Create),
])

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-p', 
		'--port', 
		metavar='port', 
		type=int,
		default=8080,
		help='listen on the specified port'
	)

	parser.add_argument(
		'--default_game',
		type=int,
		metavar='num_players',
		dest='default_num_players',
		nargs='?',
		default='no_default'
	)

	opts = parser.parse_args()
	if opts.default_num_players is None:
		opts.default_num_players = 1

	if opts.default_num_players == "no_default":
		opts.default_num_players = None

	if opts.default_num_players is not None:
		num_players = opts.default_num_players
		game = DefaultGame(num_players)
		games.add(game)
		for i in range(num_players):
			token = "default{}".format(i+1)
			game_tokens[token] = game
			default_player = Player(token, token, game)
			game.add_player(default_player)

	socket_app.listen(opts.port)
	log.debug('Listening on port {0}'.format(opts.port))
	iol = tornado.ioloop.IOLoop.instance()
	tornado.ioloop.PeriodicCallback(lambda: None,500,iol).start()
	iol.start()