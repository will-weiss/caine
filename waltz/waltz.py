from multiprocessing import Process, Queue
import signal
import time
from gevent.timeout import Timeout

class SupportingActor(object):
    def __init__(self, timeout = 10, **kwargs):
        self.inbox = Queue()
        self.timeout = timeout
        for nm, val in kwargs.iteritems(): setattr(self, nm, val) 

    @staticmethod
    def receive(message):
        raise NotImplemented()

    @staticmethod
    def callback():
        print "No more tasks in queue."

    @staticmethod
    def handle():
        print "Operation failed."

    @staticmethod
    def listen(inbox, receive, callback, timeout, handle, _raise_timeout):
        try:
            Actor._listen(inbox, timeout, receive, _raise_timeout)
        except Timeout:
            callback()
        except not Timeout:
            handle()

    @staticmethod
    def _raise_timeout(signum, frame):
        raise Timeout

    @staticmethod
    def _listen(inbox, timeout, receive, _raise_timeout):
        use_timeout = True if type(timeout) == int else False
        if use_timeout:
            signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(timeout)
        running = True
        while running:
            message = inbox.get()
            if use_timeout: signal.alarm(0)
            receive(message)
            if use_timeout: signal.alarm(timeout)
            
    def __call__(self):
        self.process = Process(target = Actor.listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self._raise_timeout])
        self.process.start()