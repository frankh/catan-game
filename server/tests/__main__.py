import sys
import os
import unittest
import random

sys.path.insert(0,os.path.abspath(__file__+"/../.."))

from board_generation_tests import *
from game_tests import *
from utils_tests import *

if __name__ == '__main__':
	if len(sys.argv) > 1:
		seed = int(sys.argv[1])
		sys.argv = sys.argv[:1]
	else:
		seed = random.randint(1, 1000000000)

	print('Using random seed', seed)
	random.seed(seed)
	unittest.main(verbosity=2)
