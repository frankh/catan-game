import itertools
import random
import json
import logging

log = logging.getLogger('catan')
log.setLevel(logging.DEBUG)

def flatten(l):
	return list(itertools.chain(*l))

def generate_board():

	tiles = [
		['desert']		* 1,
		['fields']		* 4,
		['forest']		* 4,
		['pasture']		* 4,
		['hills']		* 3,
		['mountains']	* 3,
	]

	values = [
		[2]	* 1,
		[3]	* 2,
		[4]	* 2,
		[5]	* 2,
		[6]	* 2,
		[8]	* 2,
		[9]	* 2,
		[10]* 2,
		[11]* 2,
		[12]* 1,
	]

	tiles = flatten(tiles)
	random.shuffle(tiles)

	values = flatten(values)
	random.shuffle(values)

	return {
		'tiles': tiles, 
		'values': values,
	}

class Game(object):
	def __init__(self):
		self.board = generate_board()

class DefaultGame(Game):
	def __init__(self):
		super().__init__()


import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.websocket
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
			'board': game.board	
		}));
		log.debug(username+" joined "+game_id)

	def on_message(self, message):
		log.debug(str(self.player.id)+'>'+message)
		message = json.loads(message)

	def on_close(self):
		if hasattr(self, 'game'):
			if self.game.started:
				self.player.connected = False
				self.player.connection = None
			else:
				self.game.players.remove(self.player)

socket_app = tornado.web.Application([
	(r"/socket/(?P<username>\w+)/(?P<game_id>\w+)(?:/(?P<password>\w+))?", ClientSocket),
])

if __name__ == '__main__':
	try:
		tornado.options.enable_pretty_logging()
		socket_app.listen(8080)
		log.debug('Listening on port 8080')
		iol = tornado.ioloop.IOLoop.instance()
		tornado.ioloop.PeriodicCallback(lambda: None,500,iol).start()
		iol.start()
	except BaseException as e:
		for game in games.values():
			game.killed = True
		raise e
