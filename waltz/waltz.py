from multiprocessing import Process, Queue
import signal
import time
from gevent.timeout import Timeout

class SupportingActor(object):
    """
    concurrently processes items in its inbox 
    """
    def __init__(self, timeout = 10, **kwargs):
        self.inbox = Queue()
        self.timeout = timeout
        for nm, val in kwargs.iteritems(): setattr(self, nm, val) 

    @staticmethod
    def receive(message):
        """
        method to call using messages from inbox
        """
        raise NotImplemented()

    @staticmethod
    def callback():
        """
        method to call when inbox is empty
        """
        print "No more messages in inbox."

    @staticmethod
    def handle():
        """
        method to call when operation fails
        """
        print "Operation failed."

    @staticmethod
    def listen(inbox, receive, callback, timeout, handle, _raise_timeout):
        """
        listens for incoming messages
        """
        try:
            SupportingActor._listen(inbox, timeout, receive, _raise_timeout)
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
        if use_timeout: # Set alarm to raise a timeout after timeout seconds
            signal.signal(signal.SIGALRM, _raise_timeout)
            signal.alarm(timeout)
        running = True
        while running:
            message = inbox.get()
            if use_timeout: signal.alarm(0) # Alarm turned off when processing message
            receive(message)
            if use_timeout: signal.alarm(timeout) # Alarm reset
            
    def __call__(self):
        """
        begin processing inbox
        """
        self.process = Process(target = SupportingActor.listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self._raise_timeout])
        self.process.start()