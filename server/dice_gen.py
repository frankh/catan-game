import random
import itertools

class RandomDiceGen(object):
	def roll(self):
		return random.randint(1,6), random.randint(1,6)

class DeckDiceGen(object):
	def __init__(self, cutoff=5):
		self.deck = list(itertools.product([1,2,3,4,5,6], [1,2,3,4,5,6]))
		self.cutoff = cutoff
		self.discards = []
		random.shuffle(self.deck)

	def roll(self):
		if len(self.deck) <= self.cutoff:
			self.deck += self.discards
			self.discards = []
			random.shuffle(self.deck)

		card = self.deck.pop()
		self.discards.append(card)

		return card

class DoubleDeckDiceGen(DeckDiceGen):
	def __init__(self, cutoff=36):
		super().__init__(cutoff)
		self.deck = self.deck + self.deck
		random.shuffle(self.deck)