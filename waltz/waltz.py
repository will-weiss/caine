from multiprocessing import Process, Queue, Lock
import signal
import time
from gevent.timeout import Timeout

class SupportingActor(object):
    """
    concurrently processes items in its inbox 
    """
    def __init__(self, timeout = 10, **kwargs):
        self.inbox = Queue()
        self.lock = Lock()
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
    def handle(lock):
        """
        method to call when operation fails
        """
        lock.acquire()
        print "Operation failed."

    @staticmethod
    def listen(inbox, receive, callback, timeout, handle, lock):
        """
        listens for incoming messages
        """
        try:
            SupportingActor._listen(inbox, timeout, receive, lock)
        except Timeout:
            callback()
        except not Timeout:
            handle(lock)

    @staticmethod
    def _listen(inbox, timeout, receive, lock):
        use_timeout = True if type(timeout) == int else False
        if use_timeout: signal.signal(signal.SIGALRM, _raise_timeout) # _raise_timeout is called when alarm goes off
        running = True
        while running:
            if use_timeout: signal.alarm(timeout) # Set/Reset alarm
            lock.acquire()
            lock.release()
            message = inbox.get()
            if use_timeout: signal.alarm(0) # Alarm turned off when processing message
            receive(message)

    def __call__(self):
        """
        begin processing inbox
        """
        self.process = Process(target = SupportingActor.listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self.lock])
        self.process.start()

def _raise_timeout(signum, frame):
    raise Timeout

def _do_nothing(*args, **kwargs):
    pass

def print_square(message):
    print "%s squared is: %s" %(message, message**2)

square_printer = SupportingActor(receive = print_square, timeout = 25)

square_printer()

for i in xrange(1,11):
    square_printer.inbox.put(i)

square_printer.process.is_alive()

class Cast(SupportingActor):
    def __init__(self, supporting_actor, num = 1):
        self.actors = _cast_actors(supporting_actor, num)

    def _cast_actors(self, supporting_actor, num):
        actors = {}
        for i in xrange(num):
            actors[i] = SupportingActor()
            
        pass

    @staticmethod
    def direct(listen, inbox, receive, callback, timeout, handle):
        pass

        


    @staticmethod
    def _direct(timeout, processes):
        use_timeout = True if type(timeout) == int else False
        if use_timeout: signal.signal(signal.SIGALRM, _raise_timeout) # _raise_timeout is called when alarm goes off
        running = True
        while running:
            if use_timeout: signal.alarm(timeout) # Set/Reset alarm
            message = inbox.get()
            if use_timeout: signal.alarm(0) # Alarm turned off when processing message
            receive(message)

    def __call__(self):
        self.processes = []

        self.director = Process(target = Cast.direct, args = [self.listen, self.inbox, self.receive, self.callback, self.timeout, self.handle])
        self.director.start()






















