tornado-pserver
===============

Asynchronous, super fast, protocol aware server based on `tornado.netutil.TCPServer`. It's very easy to extend and supply own protocol

## Example
For low level echo server based on build in _NewLiner_ protocol check [example file](https://github.com/robert-zaremba/tornado-pserver/blob/master/pserver/example.py).
To start server, write:
'''python
echo_server(12345)
'''

Below I present an implementation of communication between two services using NetString protocol.

* Client asks server for some data from database.
* Server receives request about some data from Redis database, and respond by sending the pair of (request, result).

#### Server

```python
import logging
import time
from json import dumps
from redis import StrictRedis
from tornado.ioloop import IOLoop

from pserver import PServer, NetStringConn


class Handler(object):
    def __init__(self):
        self.redis  = StrictRedis()
        self.num_r  = 0   # num of handled request
        self.tstamp = time.time()

    def handler(self, request):
        if time.time()-self.tstamp > 600:
            logging.info("handled {} request, in 10 minutes".format(self.num_h, self.num_r))
            self.num_r = 0
            self.tstamp = time.time()
        self.num_r += 1
        try:
            data = self.redis.get(request.body)
            logging.debug('handled request %s', data)
            logging.debug('receiving resposne')
            request.write( dumps((request.body, {})).format(data) )
        except:
            logging.exception("Error during writing to connection")
            logging.debug("Closing connection")
            if request:
                request.connection.stream.close()

def make_server(port):
    handler = Handler()
    server  = PServer(handler.handler, NetStringConn)
    server.listen(port)
    logging.info("Server created")
    return server

if __name__ == '__main__':
    server = make_server(12345)
    logging.info("Server activated and listening")
    IOLoop.instance().start()
```

## Usage

To use _pserver_ for your protocol, you should extend `base.PConnection` class and `base.PRequest` class.
Check [protocols.py](https://github.com/robert-zaremba/tornado-pserver/blob/master/pserver/protocols.py) for template implementation of [_Netstrings_](http://cr.yp.to/proto/netstrings.txt) protocol and _NewLiner_ protocol.


## Installation

```
python setup.py install
```

### Requirements

* Python2 >= 2.7 or Python3 >= 3.1 or PyPy >= 1.8
* tornado >= 2.1.1

Additional requirements to run tests:

* py.test (preferred) or nose
* [pyfunctional](https://github.com/robert-zaremba/pyfunctional)

