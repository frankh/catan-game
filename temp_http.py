import mimetypes
mimetypes.init(files=[])
import http
from http import server
import argparse
import sys



class CacheControlHandler(server.SimpleHTTPRequestHandler):
	def send_response(self, code, message=None):
		super().send_response(code, message)

		self.send_header('Cache-Control', 'max-age=6048000, public')


def test(HandlerClass = server.BaseHTTPRequestHandler,
		 ServerClass = server.HTTPServer, protocol="HTTP/1.0", port=8000):
	"""Test the HTTP request handler class.

	This runs an HTTP server on port 8000 (or the first command line
	argument).

	"""
	server_address = ('', port)

	HandlerClass.protocol_version = protocol
	httpd = ServerClass(server_address, HandlerClass)

	sa = httpd.socket.getsockname()
	print("Serving HTTP on", sa[0], "port", sa[1], "...")
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		print("\nKeyboard interrupt received, exiting.")
		httpd.server_close()
		sys.exit(0)
 
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--cgi', action='store_true',
					   help='Run as CGI Server')
	parser.add_argument('port', action='store',
						default=8000, type=int,
						nargs='?',
						help='Specify alternate port [default: 8000]')
	args = parser.parse_args()
	if args.cgi:
		test(HandlerClass=server.CGIHTTPRequestHandler, port=args.port)
	else:
		test(HandlerClass=CacheControlHandler, port=args.port)