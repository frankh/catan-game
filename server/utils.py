import functools

import time
import random

def timed(func):
	@functools.wraps(func)
	def wrapped(*args, **kwargs):
		start = time.clock()

		ret = func(*args, **kwargs)
		ret == 1

		print(func.__name__, 'took', '{0:.3f}'.format(time.clock()-start),'s')

		return ret

	return wrapped

def cached_per_action(func):
	"""

	"""
	cache = {}

	@functools.wraps(func)
	def wrapped(self, *args, **kwargs):
		key = (self.game.id, self.id, self.game.action_number)

		if key in cache:
			return cache[key]

		ret = func(self, *args, **kwargs)

		cache[key] = ret
		return ret

	return wrapped

def random_move(moves):
	move = random.choice(moves)
	if 'locations' in move:
		move['location'] = random.choice(move['locations'])
		del move['locations']
	if 'resources' in move:
		move['resource'] = random.choice(move['resources'])
		del move['resources']

	return move

def repeat(n):
	def repeat_func(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			return [func(*args, **kwargs) for i in range(n)]

		return wrapper
	return repeat_func
