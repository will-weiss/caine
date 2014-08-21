import multiprocessing
import signal
import time
import functools

class SupportingActor(object):
    """
    Data structure with operations for receiving objects put in its inbox.

    Parameters
    __________
    timeout : int or None, default None
        If not None, the number of seconds between message receptions before callback is executed
    kwargs : object
        Additional keyword arguments are set as attributes
    """

    def __init__(self, timeout = None, **kwargs):
        self.inbox = multiprocessing.Manager().Queue()
        self.timeout = timeout
        for nm, val in kwargs.iteritems(): setattr(self, nm, val)
        self._process = None

    @property
    def instance_kwargs(self):
        """
        dict with keyword arguments of instance
        """
        instance_kwargs = {}
        for nm, val in self.__dict__.iteritems():
            if (not hasattr(val,'__call__')) & (nm[0] != '_'):
                instance_kwargs[nm] = val
        return instance_kwargs

    @property
    def process(self):
        """
        multiprocessing.Process receiving messages put in inbox 
        """
        if self._process is None:
            self._process = multiprocessing.Process(target = SupportingActor._listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self.instance_kwargs])
        return self._process
    
    @staticmethod
    def receive(message, **instance_kwargs):
        """
        method called on messages put in inbox, requires implementation
        """
        raise NotImplemented()

    @staticmethod
    def callback(**instance_kwargs):
        """
        method called when inbox reception done
        """
        print "No more messages in inbox."

    @staticmethod
    def handle(exc, message, **instance_kwargs):
        """
        method called upon exception
        """
        print "Error for message:"
        print message
        raise exc

    @staticmethod
    def _raise_timeout(signum, frame, running_flag):
        """
        shuts off the running_flag value, ending inbox reception
        """
        running_flag.value = 0

    @staticmethod
    def _listen(inbox, receive, callback, timeout, handle, instance_kwargs):
        """
        listens for incoming messages, executes callback when inbox reception complete, executes handle when exception raised
        """
        running_flag = multiprocessing.Value('i', 1) # This flag indicates whether the listening process is ongoing.
        
        # Use a timeout if timeout is an integer, otherwise do not.
        # If a timeout is being used, set an alarm to run _raise_timeout after timeout seconds.
        use_timeout = True if type(timeout) == int else False
        if use_timeout: 
            signal.signal(signal.SIGALRM, functools.partial(SupportingActor._raise_timeout, running_flag = running_flag))
            signal.alarm(timeout)
                 
        while running_flag.value == 1:                                          # While inbox reception is ongoing:

            try:                                                                # Try
                message = inbox.get_nowait()                                    # to get a message immediately.
                if hasattr(message, '__waltz_cut__'):                           # If message has attribute __waltz_cut__,
                    if message.__waltz_cut__ == True:                           # and __waltz_cut__ is equal to True,
                        if message == Cut:                                      # and the message is Cut,
                            running_flag.value = 0                              # flag inbox reception as not ongoing
                            break                                               # and break the listening process
                if use_timeout: signal.alarm(0)                                 # Alarm turned off while running receive on message
            
            except:                                                             # If any of the above fails
                continue                                                        # start the while loop again to ensure that the listening process should continue.
            
            try:                                                                # With a non-Cut message try
                receive(message, **instance_kwargs)                             # executing the receive function on the message
                if use_timeout : signal.alarm(timeout)                          # if successful, reset the alarm if appropriate. 
            except Exception as exc: handle(exc, message, **instance_kwargs)    # If an exception is raised, pass it, the message, and the instance keyword arguments to handle.
        
        callback(**instance_kwargs)                                             # Execute callback when inbox reception complete.

    def cut(self):
        use_num = 1 if not hasattr(self,'num') else self.num
        for _ in xrange(use_num): self.inbox.put(Cut)            

    def __call__(self):
        """
        begin receiving messages put in inbox
        """
        self._process = None
        self.process.start()

class SupportingCast(SupportingActor):
    """
    Data structure with operations for receiving objects put in its inbox using multiple waltz.SupportingActor processes

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
        """
        multiprocessing.Process directing multiple actors receiving from a common inbox 
        """
        if self._director is None:
            self._director = multiprocessing.Process(target = SupportingCast._direct, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self.num, self.instance_kwargs])
        return self._director

    @staticmethod
    def handle(exc, message, actors, **actor_kwargs):
        """
        method called upon exception
        """
        print "Error for message:"
        print message
        for actor in actors: actor.terminate()
        raise exc

    @staticmethod
    def _listen(inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, actor_kwargs):
        """
        listens for incoming messages, passes exceptions and the message that caused them to handle
        """
        while running_flag.value == 1:                          # While inbox reception is ongoing:
            
            try:                                                # Try to get a message immediately.
                assert handling_error_flag.value == 0           # First check that the director isn't currently handling an error,
                assert error_queue.empty()                      # then check that the error queue is empty,
                message = inbox.get_nowait()                    # now attempt to get a message at once.
                if hasattr(message, '__waltz_cut__'):           # If message has attribute __waltz_cut__,
                    if message.__waltz_cut__ == True:           # and __waltz_cut__ is equal to True,
                        if message == Cut:                      # and the message is Cut,
                            break                               # break the listening process.
                message_received_flag.value = 1                 # If we get a non-Cut message without waiting, toggle flag indicating that a message was received.
            
            except:                                             # If any of the above fails
                continue                                        # start the while loop again to ensure that the listening process should continue.
            
            try: receive(message, **actor_kwargs)               # With a non-Cut message try executing the receive function on the message.
            except Exception as exc:                            # If an exception is raised:
                error_queue.put((exc, message, actor_kwargs))   # put it, the message, and the actor keyword arguments in the error queue
                handling_error_flag.value = 1                   # and toggle the flag indicating that an error as being handled.
                while handling_error_flag.value == 1:           # While the flag is toggled to 1,
                    time.sleep(1)                               # wait to proceed with the listening process.

    @staticmethod
    def _direct(inbox, receive, callback, timeout, handle, num, instance_kwargs):
        """
        cast and direct multiple actors receiving messages from a common inbox
        """
        running_flag = multiprocessing.Value('i', 1)            # This flag indicates whether the listening process is ongoing.
        message_received_flag = multiprocessing.Value('i', 0)   # This flag gets toggled to 1 when individual actors receive messages, which causes the director to reset the timeout alarm.
        handling_error_flag = multiprocessing.Value('i', 0)     # This flag gets toggled to 1 when the director is handling an error and toggled back to zero when error handling is done.
        error_queue = multiprocessing.Manager().Queue()         # This queue holds information about errors.
        
        # Create a list of actors, processes who each listen for messages from a common inbox, then start each actor.
        actors = [multiprocessing.Process(
            target = SupportingCast._listen,
            args = [inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, dict(instance_kwargs.items() + [('actor_id', i)])]
        ) for i in xrange(num)]
        for actor in actors: actor.start()
         
        # Use a timeout if timeout is an integer, otherwise do not.
        # If a timeout is being used, set an alarm to run _raise_timeout after timeout seconds.
        use_timeout = True if type(timeout) == int else False                                                                               
        if use_timeout:
            signal.signal(signal.SIGALRM, functools.partial(SupportingCast._raise_timeout, running_flag = running_flag))
            signal.alarm(timeout)
        
        while running_flag.value == 1:                                  # While inbox reception is ongoing:
            
            try:                                                        # Try the following:
                if not any([actor.is_alive() for actor in actors]):     # If no actor is alive,
                    running_flag.value = 0                              # flag the listening process as complete,
                    break                                               # and break the listening process.
                
                if not error_queue.empty():                             # If there is an exception in the error queue,
                    if use_timeout: signal.alarm(0)                     # turn the alarm off if appropriate,
                    (exc, message, actor_kwargs) = error_queue.get()    # catch the exception, the message, and the actor keyword arguments,
                    handle(exc, message, actors, **actor_kwargs)        # and pass them to handle.
                    handling_error_flag.value = 0                       # When handle is complete turn off the flag,
                    if use_timeout: signal.alarm(time_out)              # and reset the alarm if appropriate.
                
                if use_timeout:                                         # If a timeout is being used,
                    if message_received_flag.value == 1:                # and a message was received
                        signal.alarm(timeout)                           # reset the alarm,
                        message_received_flag.value = 0                 # and toggle the flag back to zero.

            except:                                                     # If any of the above failed,
                continue                                                # jump to the top of the while loop to check if inbox reception is ongoing.
            
        callback(**instance_kwargs)                                     # Execute callback when inbox reception complete.

    def __call__(self):
        """
        begin receiving messages put in common inbox
        """
        self._director = None
        self.director.start()

class Cut:
    """
    when put in inbox of SupportingActor or SupportingCast instance shuts down inbox reception
    """
    __waltz_cut__ = True
