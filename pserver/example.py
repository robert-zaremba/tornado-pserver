import socket
from tornado.iostream import  IOStream
from tornado.ioloop import IOLoop

from pserver.protocols import NewLinerConn
from pserver import PServer


def echo_server(port=12345, pcon=NewLinerConn):
    """makes Echo server"""
    print("Making echo server")
    def echo_handler(request):
        print("echo server: "+request.body)
        request.write(request.body)

    server = PServer(echo_handler, pcon)
    server.listen(port)
    server.start()
    IOLoop.instance().start()


class EchoClienAsync(object):
    def __init__(self, host = "127.0.0.1", port=12345):
        self.host = host
        self.port = port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = IOStream(s)

    def connect(self):
        self.stream.connect((self.host, self.port))
        return self.stream

    def send(self, data, callback=None):
        self.stream.write(data+"\n", callback)

    def recv(self, callback):
        self.stream.read_until("\n", lambda data: callback(data[:-1]))

class EchoClientSync(object):
    def __init__(self, host = "127.0.0.1", port=12345):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), .2)

    def send(self, data):
        self.sock.send(data+"\n")

    def recv(self):
        result = []
        while True:
            chunk = self.sock.recv(1024)
            result.append(chunk)
            if chunk[-1]=='\n':
                break
        return ''.join(result)[:-1]

def test_client_async():
    ioloop = IOLoop.instance()
    conn = EchoClienAsync()
    conn.connect()
    text = "Hello World"
    conn.send(text)
    def handle_data(data):
        assert data == text
        print "Result OK"
        ioloop.stop()

    conn.recv(handle_data)

    ioloop.start()

def test_client_sync():
    conn = EchoClientSync()
    conn.connect()
    text = "Hello World"
    conn.send(text)
    assert conn.recv() == text
