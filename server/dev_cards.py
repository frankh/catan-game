import itertools
import random

def flatten(l):
	return list(itertools.chain(*l))

class Deck(object):
	def __init__(self):
		self.cards = flatten([
			[Knight() for _ in range(14)],
			[Plenty() for _ in range(2)],
			[Monopoly() for _ in range(2)],
			[RoadBuilding() for _ in range(2)],
			[VictoryPoint() for _ in range(5)],
		])

		random.shuffle(self.cards)

	def draw(self):
		return self.cards.pop()

class DevCard(object):
	played = False

	@property
	def name(self):
		return self.__class__.__name__

	def playable(self, game):
		return not self.played

	def as_dict(self):
		return self.name

class VictoryPoint(DevCard):
	def playable(self, game):
		return False

class Knight(DevCard):
	pass

class Plenty(DevCard):
	pass

class Monopoly(DevCard):
	pass

class RoadBuilding(DevCard):
	pass