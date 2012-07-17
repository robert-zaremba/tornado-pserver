tornado-pserver
===============

Asynchronous, super fast, protocol aware server based on `tornado.netutil.TCPServer`. It's very easy to extend and supply own protocol

## Example
For low level echo server example check [example file](https://github.com/robert-zaremba/tornado-pserver/blob/master/pserver/example.py)

Other example of server to make communication between two services by NetString protocol.

* Client asks server for some data from database.
* Server receives request about some data from Redis database, and respond by sending the result with additional info (empty `dict`).

### Server

```python
import logging
import time
import redis
from redis import StrictRedis
from json import dumps

from pserver import PServer, NetStringConn


class Handler(object):
    def __init__(self):
        self.redis = StrictRedis()
        self.num_h   = 0   # num of handled request
        self.tstamp  = time.time()

    def handler(self, request):
        if time.time()-self.tstamp > 600:
            logging.info("handled {} request, in 10 minutes".format(self.num_h, self.num_r))
            self.num_r = self.num_h = 0
            self.tstamp = time.time()
        self.num_h += 1

        try:
            data = redis.get(request.body)
            logging.debug('receiving resposne')
            request.write( dumps((request.body, {})).format(result) )
        except:
            logging.exception("Error during writing to connection")
            logging.debug("Closeing connection")
            if request:
                request.connection.stream.close()

def make_server():
    handler = Handler()
    server  = PServer(handler.handler, NetStringConn)
    server.listen(config.adconnector_port)
    logging.info("Server created")
    return server

if __name__ == '__main__':
    server = make_server()
    logging.info("Server activated and listening")
    IOLoop.instance().start()
```

## Usage

To use _pserver_ for your protocol, you should extend `base.PConnection` class and `base.PRequest` class.


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

