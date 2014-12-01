import time
from tornado.util import bytes_type

from . import logger
from .base import PConnection, PRequest


class NetStringReq(PRequest):
    """A single request object for NetStringConn.

       Request is finished by either calling `write` or `finish` method.
       When Request is finished, then the writed chunks are send back to client in the
       netstring (http://cr.yp.to/proto/netstrings.txt) format
           <data_length>:<data>,
    """
    def __init__(self, *args, **kwargs):
        super(NetStringReq, self).__init__(*args, **kwargs)
        self._response_data =[]


    def write(self, chunk, callback=None):
        """Writes data to the response stream and finish response."""
        assert isinstance(chunk, bytes_type)
        assert self._response_data is not None, "Writes after finish"

        self._response_data.append(chunk)
        self._response_data.append(',')     # NetString
        data = ''.join(self._response_data)
        self.connection.write(str(len(data)-1) + ':')
        self.connection.write(data, callback=callback)
        self._response_data = None

        self.finish()

    def write_chunk(self, chunk):
        """Writes the given chunk to the response stream.
        This function must be followed by call write or finish method"""
        assert isinstance(chunk, bytes_type)
        self._response_data.append(chunk)


    def finish(self, keep_alive=True):
        """Finishes this request on the open connection."""
        if self._response_data:
            self.write()
        self.connection.finish(keep_alive)
        self._finish_time = time.time()


class NetStringConn(PConnection):
    """
    We read data from socket stream based on NetString protocol
       netstring (http://cr.yp.to/proto/netstrings.txt)
    The readed data is a body of a PRequest object which is send to request_callback function.
    When PRequest calls write or finish method, the request is finish and response is flushed back to socket.
    If keep_alive is true, then the connection is keep open, and PConnection waits for
    another comand (NetString data from socket)
    """
    ReqCls = NetStringReq

    def read(self):
        self.stream.read_until(":", self.on_request)

    def on_request(self, data):
        logger.debug("readed head: " + data)
        try:
            num_bytes = int(data[:-1]) + 1                       #need to read additional ','
            self.stream.read_bytes(num_bytes, self.on_body)
        except:
            logger.exception('Mallformed data, expected number, received: {}'.format(data[:-1]))

    def on_body(self, data):
        logger.debug("Request handled with data: '{}'".format(data))
        self.make_request(data[:-1])     # remove ','


########################################


class NewLinerReq(PRequest):
    """A single request object for NewLinerConn.

       Request is finished by either calling `write` or `finish` method.
       When Request is finished, then the writed chunks are send back to client in the
       data format:
           <data>\n
    """
    def __init__(self, *args, **kwargs):
        super(NewLinerReq, self).__init__(*args, **kwargs)
        self._response_data =[]


    def write(self, data, callback=None):
        """Writes data to the response stream and finish response."""
        assert isinstance(data, bytes_type)
        self.connection.write(data)
        self.connection.write('\n', callback=callback)
        self.finish()


    def finish(self, keep_alive=True):
        """Finishes this request on the open connection."""
        self.connection.finish(keep_alive)
        self._finish_time = time.time()


class NewLinerConn(PConnection):
    ReqCls = NewLinerReq

    def read(self):
        self.stream.read_until("\n", self.on_request)

    def on_request(self, data):
        self.make_request(data[:-1]) # remove '\n'
