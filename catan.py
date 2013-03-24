import itertools
import random

def flatten(l):
	return list(itertools.chain(*l))

def generate_board():

	tiles = [
		['desert']*1,
		['fields']*4,
		['forest']*4,
		['hills']*3,
		['mountains']*3,
		['pasture']*4,
	]

	tiles = flatten(tiles)
	random.shuffle(tiles)

	return tiles