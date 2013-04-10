import logging

def getLogger(name):
	log = logging.root
	logging.basicConfig(format='%(asctime)s %(message)s')
	log.setLevel(logging.DEBUG)

	return log