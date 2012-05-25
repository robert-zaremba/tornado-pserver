# Copyright 2012 Robert Zaremba
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A non-blocking, single-threaded TCP-protocol avare server, with data
stream definied by:
       netstring (http://cr.yp.to/proto/netstrings.txt)

The code is based on HTTP server implementation
"""

import socket
import time
import ssl # Python 2.6+
from tornado.iostream import  SSLIOStream
from tornado.netutil import TCPServer
from tornado import stack_context

from pserver import logger


class PServer(TCPServer):
    r"""A non-blocking, single-threaded TCP-protocol avare server.
    with data stream definied by:
       netstring (http://cr.yp.to/proto/netstrings.txt)

    A server is defined by a request callback that takes an Request
    instance as an argument and writes data back with calling
    `Request.write`. After data is written,  `Request.finish` can be
    called with keep_alive option to overwrite default. `Request.finish`
    finishes the request (but does not necessarily close the connection
    in the case of keep-alive requests). A simple example server that
    echoes back the URI you requested::

        import pserver
        import ioloop

        def handle_request(request):
           request.write("OK")
           request.finish(keep_alive) = False)   # this is optional

        server = pserver.PServer(handle_request)
        server.listen(8888)
        ioloop.IOLoop.instance().start()

    `PServer` is a very basic connection handler.
    It accept request which is single line bytes stream, and call on it
    `request_handler`. It also implementes keep-alive connections, which
    is True be default. You can provide the ``keep_alive`` argument to the
    `PServer` constructor, which will ensure the connection is not closed
    on every request. This can be overwrited by request_handler on request object

    `PServer` are the same as initialization methods defined on
    `tornado.netutil.TCPServer`:
        http://www.tornadoweb.org/documentation/netutil.html#tornado.netutil.TCPServer
    """
    def __init__(self, request_callback, protocol_conn, keep_alive=True, io_loop=None,
                 ssl_options=None):
        """Initialize PServer with protocol specified by <protocol_connection>, and
        <request_callback> as na callable to handle requests objects (which is build by protocol_conn)
        """
        self.request_callback = request_callback
        self.protocol_conn = protocol_conn
        self.keep_alive = keep_alive
        TCPServer.__init__(self, io_loop=io_loop, ssl_options=ssl_options)
        logger.debug("PServer initialized")

    def sockets_names(self):
        return [s.getsockname() for s in self._sockets.values()]

    def handle_stream(self, stream, address):
        logger.info("handling new stream - a client connection")
        self.protocol_conn(stream, address, self.request_callback,
                           self.keep_alive)


class PConnection(object):
    """Handles a connection of client and calls `requests_callback`
    supplied by pserver.

    This is a base class which needs to be extended in derived class.
    Some who want to implemet own protocol needs to:
      * develop proper Request class which will handle writes and reads.
      The Request object will be deliver to handler - `request_callback`
      * set this Request class as an ReqCls field of derived class
      * implement approprite `read` method, which will prepare the connection
      object and put `on_request` as a callback to first `stream.read_*` function,
      to handle firs portion of data. Other callbacks for `stream.read_*` can
      be anything you want.
      * implement approprite `write` method.
      * implement `on_request` which takes needs to be called from the first
      `stream.read_*` function

    """
    ReqCls  = NotImplementedError

    def __init__(self, stream, address, request_callback, keep_alive=True):
        self.stream = stream
        if self.stream.socket.family not in (socket.AF_INET, socket.AF_INET6):
            # Unix (or other) socket; fake the remote address
            address = ('0.0.0.0', 0)
        self.address = address
        self.request_callback = request_callback
        self.keep_alive = keep_alive
        self._request = None
        self._request_finished = False
        self._write_callback = None
        # Save stack context here, outside of any request.  This keeps
        # contexts from one request from leaking into the next.
        self._on_request = self.on_request   # make safe copy
        self.on_request = stack_context.wrap(self._on_request)
        self.read()

    def read(self):    # TODO
        """define here the start functionality of you protocol.
        The  first callback to `stream.read*` function should be `on_requst`,
        which is context wrapped `_on_read` function which you must to implement as an method.
          When whole data is ready, and buffered `self.make_request(data)` should be called"""
        raise NotImplementedError("read function must be implemented in derived class")

    def make_request(self, data):
        self._request = self.ReqCls(data, connection=self, remote_ip=self.address[0])
        try:
            self.request_callback(self._request)
        except:
            logger.exception(b"exception was thrown from request_callback({})".format(data))

    def write(self, chunk, callback=None):
        """Writes a chunk of output to the stream."""
        assert self._request, "Request closed"
        logger.debug("writing chunk: '{}'".format(chunk))
        if not self.stream.closed():
            self._write_callback = callback and stack_context.wrap(callback)    # TODO
            self.stream.write(chunk, self._on_write_complete)

    def finish(self, keep_alive=True):
        """Finishes the request."""
        assert self._request, "can't finish closed request"
        self._request_finished = True
        if not self.stream.writing():
            self._finish_request()
        # elsewhere _on_write_complete will call _finish_request
        # the IOLoop should be single threaded, so this is safe

    def _on_write_complete(self):
        if self._write_callback is not None:
            callback = self._write_callback
            self._write_callback = None
            callback()
        # _on_write_complete is enqueued on the IOLoop whenever the
        # IOStream's write buffer becomes empty, but it's possible for
        # another callback that runs on the IOLoop before it to
        # simultaneously write more data and finish the request.  If
        # there is still data in the IOStream, a future
        # _on_write_complete will be responsible for calling
        # _finish_request.
        if self._request_finished and not self.stream.writing():
            self._finish_request()

    def _finish_request(self):
        # possibly check if something should disconnect based on protocol function
        self._request = None
        self._request_finished = False
        if self.keep_alive:
            logger.debug("finishing request")
            self.read()
        else:
            self.stream.close()



class PRequest(object):
    """A single request.

    .. attribute:: body: byte string

       Request body, if present, as a byte string.

    .. attribute:: remote_ip: string

       Client's IP address

    .. attribute:: protocol

       The protocol used, either "" or "ssl".

    .. attribute:: connection

       An request is attached to a single connection, which can
       be accessed through the "connection" attribute.
       Since connections are kept open by default (keep_alive), multiple requests can be handled
       sequentially on a single connection.

       Request is finished by either calling `write` or `finish` method.
       When Request is finished, then the writed chunks are send back to client in the
       netstring (http://cr.yp.to/proto/netstrings.txt) format
           <data_length>:<data>,
    """

    def __init__(self, body=None, remote_ip=None, protocol=None, connection=None):
        self.body = body or ""
        self.remote_ip = remote_ip
        if protocol:
            self.protocol = protocol
        elif isinstance(connection.stream,
                        SSLIOStream):
            self.protocol = "ssl"
        else:
            self.protocol = ""
        self.connection = connection
        self._start_time = time.time()
        self._finish_time = None


    def write(self, chunk, callback=None):
        """Writes data to the response stream and finish response."""
        raise NotImplementedError("read function must be implemented in derived class")


    def finish(self, keep_alive=True):
        """Finishes this request on the open connection."""
        raise NotImplementedError("read function must be implemented in derived class")

    def request_time(self):
        """Returns the amount of time it took for this request to execute."""
        if self._finish_time is None:
            return time.time() - self._start_time
        else:
            return self._finish_time - self._start_time

    def get_ssl_certificate(self):
        """Returns the client's SSL certificate, if any.

        To use client certificates, the PServer must have been constructed
        with cert_reqs set in ssl_options, e.g.::

            server = PServer(app,
                ssl_options=dict(
                    certfile="foo.crt",
                    keyfile="foo.key",
                    cert_reqs=ssl.CERT_REQUIRED,
                    ca_certs="cacert.crt"))

        The return value is a dictionary, see SSLSocket.getpeercert() in
        the standard library for more details.
        http://docs.python.org/library/ssl.html#sslsocket-objects
        """
        try:
            return self.connection.stream.socket.getpeercert()
        except ssl.SSLError:
            return None

    def __repr__(self):
        return " {} from {},  body:{}".foramt(self.__class__.__name__, self.protocol, self.remote_ip, self.body)
