import functools

import time

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
		key = self.game.action_number

		if key in cache:
			return cache[key]

		ret = func(self, *args, **kwargs)

		# Save memory. Action number will never go backwards
		# so we can delete the old key.
		for _key in list(cache.keys()):
			del cache[_key]

		cache[key] = ret
		return ret

	return wrapped