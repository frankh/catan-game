import sys
import os
import unittest

sys.path.insert(0,os.path.abspath(__file__+"/../.."))

from board_generation_tests import *
from game_tests import *

if __name__ == '__main__':
        unittest.main()
