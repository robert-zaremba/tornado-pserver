# coding: utf-8
from multiprocessing import Process
from threading import Thread, Event as TEvent
import time
import random
import socket
from tornado import iostream

from tornado.testing import AsyncTestCase, main, get_unused_port
import pytest
from testutils import SpyMethod

from pserver import PServer, NetStringConn
from pserver.client import NetStringClient
from . import logger


class TestPServer1(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        self.response_callback = SpyMethod()
        self.server = PServer(self.response_callback, NetStringConn, io_loop = self.io_loop)
        self.server.handle_stream = SpyMethod()
        self.port = get_unused_port()
        self.server.listen(self.port)

    def check_and_stop(self):
        assert self.io_loop.running()
        assert self.server._started
        self.server.stop()
        self.io_loop.add_callback(self.stop)

    def test_start_stop_server(self):
        self.server.start()
        assert self.port in [s[1] for s in self.server.sockets_names()]
        self.io_loop.add_timeout(time.time()+.2, self.check_and_stop)
        self.wait(timeout=1)


    def check_handle_request(self):
        assert self.server.handle_stream.num_calls == 1

        # assert_that_method(self.server.handle_stream).was_called()
        # self.io_loop.add_callback(assert_that_method(self.server.handle_stream).was_called)

    def test_connection_sync(self):
        self.server.start()

        def connect():
            # following raises exception, if connection was'nt made
            sock = socket.create_connection(("127.0.0.1", self.port), .2)
            assert sock
            #assert_that_method(self.server.handle_stream).was_never_called()
            assert self.server.handle_stream.num_calls == 0
            sock.send(b'request\n')
            self.io_loop.add_callback(self.check_handle_request)
            self.io_loop.add_callback(self.stop)

        self.io_loop.add_callback(connect)
        self.wait(timeout=1)


class TestPServer2(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        self.response_callback = echo_handler
        self.server = PServer(self.response_callback, NetStringConn, io_loop = self.io_loop)
        #self.server = proxy_spy(self.server)
        self.port = get_unused_port()
        self.server.listen(self.port)

        conn_info = socket.getaddrinfo('127.0.0.1', self.port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        af, socktype, proto, conname, saddress = conn_info[0]
        # print(conn_info)
        # print(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = saddress
        self.sock = socket.socket(af, socktype, 6)                 # In the examples from net, the protocol version is 0
        self.stream = iostream.IOStream(self.sock, self.io_loop)   # client must have the same event loop, otherwise it will create new one
        self.server.start()


    def test_connection_stream(self):
        """test próby połączenia trzech klientów: jeden z tego samego wątku, drugi z nowego.
        Pierwszy jest z tego samego wątku. Przy połączeniu uwstawia walidator <connected>.
        Drugi z nowego wątku zamyka przy połączeniu zatrzymuje główną pętlę i server.
        Trzeci jest z nowego procesu. Musi mieć nowego event loopa, który musi osobno wystartować (główny event loop startuje wraz z funkcją self.wati).
           Przy połączeniu event loop procesu zostaje zamknięty i proces się kończy.
           Gdyby się nie połączył, test się nie skończy"""
        connected_t = TEvent()

        def connect(io_loop, f_stop=None):
            if not f_stop:
                f_stop = io_loop.stop
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            stream2 = iostream.IOStream(sock2, io_loop)
            stream2.connect(self.server_address, f_stop)
            if io_loop != self.io_loop:                       # we get other event loop
                logger.debug("Mam nowy  event loop. Startuje go")
                io_loop.start()


        self.stream.connect(self.server_address, connected_t.set)
        p=Process(target = connect, args=(self.get_new_ioloop(), ))  # proces musi operować na innym event loopie!
        p.start()
        t=Thread(target = connect, args=(self.io_loop, self.stop))   # wątek może mieć ten sam eventloop
        t.start()

        self.wait(timeout=1)
        assert connected_t.is_set()
        assert t.is_alive() is False
        p.join(0.1)
        if p.is_alive():
            p.terminate()
            self.fail("Process doesn't terminate normally - client doesn't connect to server")

    def test_req_resp(self):

        def client_work():
            num_writes = 1
            client.stop_cond = lambda obj: len(obj.resp)==num_writes
            #client.next_random()
            for i in range(num_writes):
                #self.io_loop.add_callback(lambda: client.write(str(random.random())))
                client.next_random()

        client = EchoClient(self.stream, self)
        self.stream.connect(self.server_address, client_work)

        self.wait(timeout=1)
        assert client.req == client.resp


    def raw_req_resp_session(self, length, callback):
        """make req resp session with NetString server.
        when session is finished, call callback
        """
        out = []
        def send(i):
            """Send some data in NetString format"""
            data = 'w'+str(i+1)                       # some test data
            data = "{}:{},".format(len(data), data) # constructing NetString
            logger.debug("send "+data)
            self.stream.write(data, on_write)

        def on_read(data):
            out.append(data)
            logger.debug("out: {}".format(data))
            i = len(out)
            if i == length:
                callback()
            else:
                send(i)

        def on_write():
            self.stream.read_bytes(5, on_read)

        send(0)

    def test_req_resp2(self):
        self.stream.connect(self.server_address,
                            lambda: self.raw_req_resp_session(1, self.stop))

        self.wait(timeout=1)


    def test_req_resp3(self):
        self.stream.connect(self.server_address,
                            lambda: self.raw_req_resp_session(4, self.stop))

        self.wait(timeout=1)

    def test_req_resp_noseq(self):
        """test if reads /writes where reads do not follow approprite writes don't succeed"""

        def work():
            self.stream.write("2:d1,")
            with pytest.raises(IOError):
                self.stream.write("2:d1,")
            self.io_loop.add_callback(self.stop)

        self.io_loop.add_callback(work)

        self.wait(timeout=1)


    def socket_raw_req_resp(self, d_in, d_out):
        time.sleep(.1)
        sock = socket.create_connection(self.server_address, .2)
        for d in d_out:
            logger.info("sending: "+ d)
            sock.send(d)
            r = sock.recv(8)
            r += sock.recv(8)        # net string are sended in two phases
            logger.info("received: "+ r)
            d_in.append(r)
        self.stop()


    def test_req_resp_socket(self):
        d_out = ["2:d1,", "2:d2,"]
        d_in  = []
        t = Thread(target=self.socket_raw_req_resp,  args=(d_in, d_out))
        self.io_loop.add_callback(t.start)

        self.wait(timeout=1.2)
        assert d_in == d_out

def echo_handler(request):
    request.write(request.body)

class EchoClient(NetStringClient):
    def __init__(self, stream, test):
        self.stream = stream
        self.test = test
        self.req=[]
        self.resp=[]
        self.stop_cond = self.__true

    def __true(self): return True

    def next_random(self):
        self.send(str(random.random()))

    def send(self, data):
        self.req.append(data)
        NetStringClient.send(self, data)

    def receive(self, data):
        self.resp.append(data)
        logger.debug('client read: {}'.format(self.resp))
        if self.stop_cond(self):
            self.test.stop()
        else:
            self.next_random()


if __name__ == '__main__':
    from unittest import TestLoader
    loader = TestLoader()
    suite = loader.loadTestsFromTestCase(TestPServer1)
    reduce(lambda x,test : suite.addTest(loader.loadTestsFromTestCase(test)), [TestPServer2], None)
    all = suite # TestPServer2
    main()

