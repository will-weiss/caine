import multiprocessing
from multiprocessing import Process, Queue, Lock, Pipe, Value
import signal
import time
from gevent.timeout import Timeout

class SupportingActor(object):
    """
    Data structure with operations for processing objects in its inbox.

    Parameters
    __________
    timeout : int or None, default None
        Number of seconds between message receptions before callback is executed
    kwargs : object

    """
    def __init__(self, timeout = None, **kwargs):
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
    def handle(exc):
        """
        method to call when non-timeout exception raised by listen
        """
        raise exc

    @staticmethod
    def listen(inbox, receive, callback, timeout, handle):
        """
        listens for incoming messages, executes callback after Timeout, 
        """
        try:
            SupportingActor._listen(inbox, timeout, receive)
        except Timeout:
            callback()
        except Exception as exc:
            handle(exc)

    @staticmethod
    def _listen(inbox, timeout, receive):
        use_timeout = True if type(timeout) == int else False           # We use a timeout if timeout is an integer, otherwise not
        if use_timeout: signal.signal(signal.SIGALRM, _raise_timeout)   # _raise_timeout is called when alarm goes off
        running = True
        while running:
            if use_timeout: signal.alarm(timeout)   # Set/Reset alarm
            message = inbox.get()
            if use_timeout: signal.alarm(0)         # Alarm turned off when processing message
            receive(message)

    def __call__(self):
        """
        begin processing inbox
        """
        self.process = Process(target = SupportingActor.listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle])
        self.process.start()

class SupportingCast(SupportingActor):
    def __init__(self, num = 1, **kwargs):
        SupportingActor.__init__(self, **kwargs)
        self.num = num
        self._error_lock = Lock()                           # While the error lock is held, message reception in SupportingCast._listen is blocked
        self._error_pipe_in, self._error_pipe_out = Pipe()  # Errors from individual actors are sent through the error pipe so they are caught by the director process.
        self._message_received_flag = Value('i', 0)         # This flag gets toggled to 1 when individual actors receive messages, which causes the director to reset the timeout alarm

    def _cast_actor(self):
        return Process(target = SupportingCast.listen, args = [self.inbox, self.receive, self._message_received_flag, self._error_lock, self._error_pipe_in])

    def _cast_actors(self):
        return {i : self._cast_actor() for i in xrange(self.num)}

    @staticmethod
    def listen(inbox, receive, message_received_flag, error_lock, error_pipe_in):
        """
        listens for incoming messages
        """
        try:
            SupportingCast._listen(inbox, receive, message_received_flag, error_lock)
        except Exception as exc:
            error_lock.acquire()
            error_pipe_in.send(exc)

    @staticmethod
    def _listen(inbox, receive, message_received_flag, error_lock):
        running = True
        while running:
            error_lock.acquire() # Blocks message reception while there is an error
            error_lock.release()
            message = inbox.get()
            message_received_flag.value = 1
            receive(message)

    @staticmethod
    def direct(callback, timeout, handle, error_pipe_out, message_received_flag):
        try:
            SupportingCast._direct(timeout, error_pipe_out, message_received_flag)
        except Timeout:
            callback()
        except Exception as exc:
            handle(exc)

    @staticmethod
    def _direct(timeout, error_pipe_out, message_received_flag):
        use_timeout = True if type(timeout) == int else False           # We use a timeout if timeout is an integer, otherwise not
        if use_timeout: signal.signal(signal.SIGALRM, _raise_timeout)   # _raise_timeout is called when alarm goes off
        running = True
        while running:
            if error_pipe_out.poll():                   # If there is an exception in the error pipe,
                exc = error_pipe_out.recv()             # we catch it,
                raise exc                               # and raise it
            if use_timeout:
                if message_received_flag.value == 1: 
                    signal.alarm(timeout)               # Set/Reset alarm if some process received a message
                    message_received_flag.value = 0     # Then toggle the flag back to zero

    def __call__(self):
        self.actors = self._cast_actors()
        for actor in self.actors.values(): actor.start()
        self.director = Process(target = SupportingCast.direct, args = [self.callback, self.timeout, self.handle, self._error_pipe_out, self._message_received_flag])
        self.director.start()

def _raise_timeout(signum, frame):
    raise Timeout
