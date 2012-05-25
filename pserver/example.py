from tornado.iostream import  IOStream
import socket

from pserver.protocols import NewLinerConn
from pserver import PServer


def echo_server(port, pcon=NewLinerConn):
    """makes Echo server"""
    from tornado.ioloop import IOLoop
    print("Makeing echo server")
    def echo_handler(request):
        print("echo server: "+request.body)
        request.write(request.body)

    server = PServer(echo_handler, pcon)
    server.listen(port)
    server.start()
    IOLoop.instance().start()

def make_client_sock(port):
    sock = socket.create_connection(("127.0.0.1", port), .2)
    return sock

def make_client_stream(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    stream = IOStream(s)
    stream.connect(("127.0.0.1", port))
    return stream
