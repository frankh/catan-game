import itertools
import random
import json
import logging
from collections import defaultdict, Iterable
import itertools
from functools import lru_cache
from pprint import pprint, pformat

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.websocket

import dice_gen

from game import \
	Player, \
	Game


class Logger(object):
	def setLevel(self, level):
		pass

	def debug(self, msg):
		pass
		#print('DEBUG:', msg)

log = Logger()
log.setLevel(logging.DEBUG)


class DefaultGame(Game):

	def __init__(self):
		super().__init__()
		self.dice_gen = dice_gen.DeckDiceGen()
		self.max_players = 1
games = {
	'1': DefaultGame()
}

class ClientSocket(tornado.websocket.WebSocketHandler):

	def open(self, username, game_id, password):
		username = username.decode('utf-8')
		game_id = game_id.decode('utf-8')
		
		if password:
			password = password.decode('utf-8')

		global games
		if game_id not in games:
			self.write_message(json.dumps(
				{
					'type': 'error',
					'error': {
						'type': 'NO_GAME',
						'msg': 'Game doesn\'t exist',
					 }
				 })
			)
			self.close()
			return
			
		game = games[game_id]
		self.game = game
		self.player = Player(self, username, game)
		game.add_player(self.player)

		if game.password and game.password != password:
			self.write_message(json.dumps(
				{
					'type': 'error',
					'error': {
						'type': 'BAD_PASSWORD',
						'msg': 'Wrong password',
					 }
				 })
			)
			self.close()
			return

		self.write_message(json.dumps({
			'type': 'assign_player',
			'player': self.player.as_dict(),
		}));

		self.write_message(json.dumps({
			'type': 'game',
			'game': game.as_dict(),
		}));
		log.debug(username+" joined "+game_id)

	def on_message(self, message):
		print('message')
		try:
			log.debug(str('temp')+'>'+pformat(json.loads(message)))
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
			log.debug(str('temp')+'<'+pformat(json.loads(message)))
		except:
			pass
			#log.debug(str('temp')+'<'+message)

		super().write_message(message);


	def on_close(self):
		if hasattr(self, 'game'):
			self.game.players.remove(self.player)

socket_app = tornado.web.Application([
	(r"/socket/(?P<username>\w+)/(?P<game_id>\w+)(?:/(?P<password>\w+))?", 
	 ClientSocket),
])

if __name__ == '__main__':
	socket_app.listen(8080)
	log.debug('Listening on port 8080')
	iol = tornado.ioloop.IOLoop.instance()
	tornado.ioloop.PeriodicCallback(lambda: None,500,iol).start()
	iol.start()