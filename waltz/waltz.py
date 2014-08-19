from multiprocessing import Process as mProcess
from multiprocessing import Value as mValue
from multiprocessing import Manager as mManager
import signal
from time import sleep as tsleep
from functools import partial
from gevent.timeout import Timeout

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
        self.inbox = mManager().Queue()
        self.timeout = timeout
        for nm, val in kwargs.iteritems(): setattr(self, nm, val)
        self._process = None

    @property
    def instance_kwargs(self):
        instance_kwargs = {}
        for nm, val in self.__dict__.iteritems():
            if (not hasattr(val,'__call__')) & (nm[0] != '_'):
                instance_kwargs[nm] = val
        return instance_kwargs

    @property
    def process(self):
        if self._process is None:
            self._process = mProcess(target = SupportingActor._listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self.instance_kwargs])
        return self._process
    
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
        running_flag = mValue('i', 1)                            # 1 if the process should be running, 0 otherwise
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
        self._process = None
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
        self._director = None

    @property
    def director(self):
        if self._director is None:
            self._director = mProcess(target = SupportingCast._direct, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self.num, self.instance_kwargs])
        return self._director

    @staticmethod
    def _listen(inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, actor_kwargs):
        """
        listens for incoming messages, passes exceptions and the message that caused them to handle
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
                    tsleep(1)

    @staticmethod
    def handle(exc, message, actors, **actor_kwargs):
        """
        method to call when non-timeout exception raised by listen
        """
        print "Error for message:"
        print message
        for actor in actors: actor.terminate()
        raise exc

    @staticmethod
    def _direct(inbox, receive, callback, timeout, handle, num, instance_kwargs):
        """
        directs the process for using multiple actors to process a common inbox
        """
        running_flag = mValue('i', 1)            # This flag is toggled to zero to shut off individual actors
        message_received_flag = mValue('i', 0)   # This flag gets toggled to 1 when individual actors receive messages, which causes the director to reset the timeout alarm
        handling_error_flag = mValue('i', 0)     # This flag gets toggled to 1 when the director is handling an error
        error_queue = mManager().Queue()         # This queue holds information about errors
        actors = [mProcess(target = SupportingCast._listen, args = [inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, dict(instance_kwargs.items() + [('actor_id', i)])]) for i in xrange(num)]
        for actor in actors: actor.start()
        use_timeout = True if type(timeout) == int else False # We use a timeout if timeout is an integer, otherwise not
        if use_timeout: 
            signal.signal(signal.SIGALRM, partial(SupportingCast._callback, running_flag = running_flag, callback = callback, **instance_kwargs)) # _callback is called when alarm goes off
            signal.alarm(timeout)
        while running_flag.value == 1:
            if not any([actor.is_alive() for actor in actors]):
                running_flag.value = 0
            if not error_queue.empty():                             # If there is an exception in the error queue,
                if use_timeout: signal.alarm(0)                     # turn the alarm off,
                (exc, message, actor_kwargs) = error_queue.get()    # we catch the exception, the message, and the actor keyword arguments,
                handle(exc, message, actors, **actor_kwargs)        # and pass them to handle
                handling_error_flag.value = 0                       # When handle is complete the flag is turned off
            if use_timeout:
                if message_received_flag.value == 1: 
                    signal.alarm(timeout)               # Set/Reset alarm if some process received a message
                    message_received_flag.value = 0     # Then toggle the flag back to zero

    def __call__(self):
        """
        begin processing a shared inbox using multiple actors
        """
        self._director = None
        self.director.start()

