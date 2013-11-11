import sys
import os
import unittest
import random

sys.path.insert(0,os.path.abspath(__file__+"/../.."))

from board_generation_tests import *
from game_tests import *
from utils_tests import *

import time
import logging

logging.disable(logging.WARNING)

def timingDecorator(func):
	import functools
	@functools.wraps(func)
	def wrapper(self, *args, **kwargs):
		ret = func(self, *args, **kwargs)
		self.stream.write(" (%.2fs)\n" % (time.time() - self.startTime))
		return ret

	return wrapper


class _WritelnDecorator(object):
		"""Used to decorate file-like objects with a handy 'writeln' method"""
		def __init__(self,stream):
				self.stream = stream

		def __getattr__(self, attr):
				if attr in ('stream', '__getstate__'):
						raise AttributeError(attr)
				return getattr(self.stream,attr)

		def writeln(self, arg=None):
				if arg:
						self.write(arg)
						self.flush()

class TimeTestResult(unittest.TextTestResult):
	def __init__(self, *args,**kwargs):
		super().__init__(*args, **kwargs)
		self.stream = _WritelnDecorator(self.stream.stream)

	def startTest(self, test):
		self.startTime = time.time()
		return super().startTest(test)

	@timingDecorator
	def addSuccess(self, test):
		return super().addSuccess(test)

	@timingDecorator
	def addError(self, test, err):
		return super().addError(test, err)

	@timingDecorator
	def addFailure(self, test, err):
		return super().addFailure(test, err)

	@timingDecorator
	def addSkip(self, test, reason):
		return super().addSkip(test, reason)

	@timingDecorator
	def addExpectedFailure(self, test, err):
		return super().addExpectedFailure(test, err)

	@timingDecorator
	def addUnexpectedSuccess(self, test):
		return super().addUnexpectedSuccess(test)

class TimeTestRunner(unittest.TextTestRunner):
		resultclass = TimeTestResult

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()

	parser.add_argument(
		'-s',
		'--seed',
		type=int,
		default=random.randint(1, 1000000000)
	)
	opts = parser.parse_args()

	seed = opts.seed
	print('Using random seed', seed)
	random.seed(seed)
	sys.stdout.flush()
	sys.argv = sys.argv[:1]
	unittest.TestProgram(verbosity=2, testRunner=TimeTestRunner, exit=True)
