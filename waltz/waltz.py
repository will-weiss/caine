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
    def listen(inbox, receive, callback, timeout, handle):
        """
        listens for incoming messages
        """
        try:
            SupportingActor._listen(inbox, timeout, receive)
        except Timeout:
            callback()
        except not Timeout:
            handle()

    @staticmethod
    def _listen(inbox, timeout, receive):
        use_timeout = True if type(timeout) == int else False
        if use_timeout: signal.signal(signal.SIGALRM, _raise_timeout) # _raise_timeout is called when alarm goes off
        running = True
        while running:
            if use_timeout: signal.alarm(timeout) # Set/Reset alarm
            message = inbox.get()
            if use_timeout: signal.alarm(0) # Alarm turned off when processing message
            receive(message)
    
    def __call__(self):
        """
        begin processing inbox
        """
        self.process = Process(target = SupportingActor.listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle])
        self.process.start()

def _raise_timeout(signum, frame):
    raise Timeout