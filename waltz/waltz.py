import multiprocessing
from multiprocessing import Process, Queue, Lock, Pipe, Value, Manager
import signal
import time
from functools import partial
from gevent.timeout import Timeout

def _raise_timeout(signum, frame):
    raise Timeout

class SupportingActor(object):
    """
    Data structure with operations for processing objects in its inbox.

    Parameters
    __________
    timeout : int or None, default None
        Number of seconds between message receptions before callback is executed
    kwargs : object
        Additional keyword arguments are set as attributes

    """
    def __init__(self, timeout = None, **kwargs):
        self.inbox = Manager().Queue()
        self.timeout = timeout
        for nm, val in kwargs.iteritems(): setattr(self, nm, val)

    @property
    def instance_kwargs(self):
        instance_kwargs = {}
        for nm, val in self.__dict__.iteritems():
            if not hasattr(val,'__call__'):
                instance_kwargs[nm] = val
        return instance_kwargs

    @staticmethod
    def receive(message, **instance_kwargs):
        """
        method to call using messages from inbox, requires implementation
        """
        raise NotImplemented()

    @staticmethod
    def callback(**instance_kwargs):
        """
        method to call when inbox is empty
        """
        print "No more messages in inbox."

    @staticmethod
    def handle(exc, message, **instance_kwargs):
        """
        method to call when non-timeout exception raised by listen
        """
        print "Error for message:"
        print message
        raise exc

    @staticmethod
    def _callback(signum, frame, running_flag, callback, **instance_kwargs):
        """
        shuts off the running_flag value and executes callback
        """
        running_flag.value = 0
        return callback(**instance_kwargs)

    @staticmethod
    def _listen(inbox, receive, callback, timeout, handle, instance_kwargs):
        """
        listens for incoming messages, executes callback after Timeout exception, passes all other exceptions and the message that caused them to handle
        """
        running_flag = Value('i', 1)                            # 1 if the process should be running, 0 otherwise
        use_timeout = True if type(timeout) == int else False   # We use a timeout if timeout is an integer, otherwise not
        if use_timeout:
            # _callback is called when alarm goes off
            signal.signal(signal.SIGALRM, partial(SupportingActor._callback, running_flag = running_flag, callback = callback, **instance_kwargs)) 
        while running_flag.value == 1:
            try:
                if use_timeout: signal.alarm(timeout)   # Set/Reset alarm
                message = inbox.get()
                if use_timeout: signal.alarm(0)         # Alarm turned off when processing message
            except:
                continue                                # If we fail to get a message we recheck whether the actor process should still be running
            try:
                receive(message, **instance_kwargs)
            except Exception as exc:
                handle(exc, message, **instance_kwargs)

    def __call__(self):
        """
        begin processing inbox
        """
        self.process = Process(target = SupportingActor._listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self.instance_kwargs])
        self.process.start()

class SupportingCast(SupportingActor):
    """
    Data structure with operations for processing objects in its inbox using multiple waltz.SupportingActor processes.

    Parameters
    __________
    num : int, default 1
        Number of seconds between message receptions before callback is executed
    kwargs : object
        Additional keyword arguments are set as attributes

    """
    def __init__(self, num = 1, **kwargs):
        self.num = num
        SupportingActor.__init__(self, **kwargs)

    @staticmethod
    def _listen(inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, actor_kwargs):
        """
        listens for incoming messages, executes callback after Timeout exception, passes all other exceptions and the message that caused them to handle
        """
        while running_flag.value == 1:
            try:                                        # Try to get a message
                assert handling_error_flag.value == 0   # Check that the director isn't currently handling an error
                assert error_queue.empty()              # Check that the error queue is empty
                message = inbox.get_nowait()            # Attempt to get a message at once
                message_received_flag.value = 1         # Toggle flag indicating that a message was received
            except:
                continue                                # If any of the above fails we check whether we should still be running
            try:
                receive(message, **actor_kwargs)
            except Exception as exc:
                error_queue.put((exc, message, actor_kwargs))
                handling_error_flag.value = 1
                while handling_error_flag.value == 1:
                    time.sleep(1)

    @staticmethod
    def _direct(inbox, receive, callback, timeout, handle, num, instance_kwargs):
        """
        directs the process for using multiple actors to process a common inbox
        """
        running_flag = Value('i', 1)            # This flag is toggled to zero to shut off individual actors
        message_received_flag = Value('i', 0)   # This flag gets toggled to 1 when individual actors receive messages, which causes the director to reset the timeout alarm
        handling_error_flag = Value('i', 0)     # This flag gets toggled to 1 when the director is handling an error
        error_queue = Manager().Queue()         # This queue holds information about errors

        actors = {i : Process(target = SupportingCast._listen, args = [inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, dict(instance_kwargs.items() + [('actor_id', i)])]) for i in xrange(num)}
        for actor in actors.values(): actor.start()
        use_timeout = True if type(timeout) == int else False # We use a timeout if timeout is an integer, otherwise not
        if use_timeout: 
            signal.signal(signal.SIGALRM, partial(SupportingCast._callback, running_flag = running_flag, callback = callback, **instance_kwargs)) # _callback is called when alarm goes off
            signal.alarm(timeout)
        while running_flag.value == 1:
            try:
                if not error_queue.empty():                                   # If there is an exception in the error pipe,
                    (exc, message, actor_kwargs) = error_queue.get()          # we catch it,
                    handle(exc, message, **actor_kwargs)                      # and raise it
                    handling_error_flag.value = 0
                if use_timeout:
                    if message_received_flag.value == 1: 
                        signal.alarm(timeout)               # Set/Reset alarm if some process received a message
                        message_received_flag.value = 0     # Then toggle the flag back to zero
            except:
                continue

    def __call__(self):
        """
        begin processing a shared inbox using multiple actors
        """
        self.director = Process(target = SupportingCast._direct, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self.num, self.instance_kwargs])
        self.director.start()
