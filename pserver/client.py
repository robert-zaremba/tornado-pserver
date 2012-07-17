"""Basic clients implementation for PServer and its connections"""

from . import logger


class NetStringClient(object):
    """Basic NetString client
    If you want to use it simply inherit from this class and overwrite receive method
    """
    def __init__(self, stream):
        self.stream = stream

    def send(self, data):
        logger.debug('client write: {}'.format(data))
        self.stream.write("{}:{},".format(len(data),data), self._read_head)

    def _read_head(self):
        self.stream.read_until(':', self._read_body)    # head is <number>":"   we need to read

    def _read_body(self, head):
        num_bytes = int(head[:-1])+1    # we need to read one more character - the last comma
        logger.debug('heder lenght: {}'.format(num_bytes))
        self.stream.read_bytes(num_bytes, self._on_body)

    def _on_body(self, data):
        logger.debug('received body: {}'.format(data))
        return self.receive(data[:-1])

    def receive(self, data):
        pass

