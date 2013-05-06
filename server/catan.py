import json
import log
from pprint import pformat

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.websocket

import dice_gen
import settings

from game import (
	Player,
	Game
)

log = log.getLogger('catan')

class DefaultGame(Game):

	def __init__(self):
		super().__init__()
		self.dice_gen = dice_gen.DeckDiceGen()
		self.max_players = 2
		
games = set()
game_tokens = {}

class Socket(tornado.websocket.WebSocketHandler):
	def open(self):
		token = self.get_cookie('game-token', None)

		global game_tokens
		if token not in game_tokens:
			self.write_message(json.dumps({
				'type': 'error',
				'error': {
					'type': 'Invalid Token',
					'msg': 'Invalid Token'
				}
			}))
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
		self.player.connection = None

class Create(tornado.web.RequestHandler):
	def post(self):
		secret = self.get_argument('secret')

		if( secret != settings.secret ):
			raise tornado.web.HTTPError(403)

		players = json.loads(self.get_argument('players'))
		game_name = self.get_argument('name')

		game = Game(name=game_name, max_players=len(players))

		global games
		games.add(game)

		for player in players:
			pl_obj = Player(player['token'], player['name'], game)
			game_tokens[player['token']] = game
			game.add_player(pl_obj)



socket_app = tornado.web.Application([
	(r"/socket", Socket),
	(r"/create", Create),
])

if __name__ == '__main__':
	socket_app.listen(settings.port)
	log.debug('Listening on port {0}'.format(settings.port))
	iol = tornado.ioloop.IOLoop.instance()
	tornado.ioloop.PeriodicCallback(lambda: None,500,iol).start()
	iol.start()