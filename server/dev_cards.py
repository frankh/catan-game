import itertools
import random

def flatten(l):
	return list(itertools.chain(*l))

class Deck(object):
	def __init__(self):
		self.cards = flatten([
			[Knight()]       * 14,
			[Plenty()]       * 2,
			[Monopoly()]     * 2,
			[RoadBuilding()] * 2,
			[VictoryPoint()] * 5,
		])

		random.shuffle(self.cards)

	def draw(self):
		return self.cards.pop()

class DevCard(object):
	def as_dict(self):
		return self.__class__.__name__

class VictoryPoint(DevCard):
	pass

class Knight(DevCard):
	pass

class Plenty(DevCard):
	pass

class Monopoly(DevCard):
	pass

class RoadBuilding(DevCard):
	pass