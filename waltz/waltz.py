import multiprocessing
import signal
import time
import functools
import types

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
    def instance_attributes(self):
        """
        dict with atributes of instance
        """
        instance_attributes = {}
        attr_dicts = []
        for parent_class in self.__class__.__bases__:
            if parent_class == object:
                continue
            attr_dicts.append(parent_class.__dict__)
        attr_dicts.append(self.__class__.__dict__)
        attr_dicts.append(self.__dict__) 
        for attr_dict in attr_dicts:
            for nm, val in attr_dict.iteritems():
                if (nm == 'instance_attributes') | (nm[0] == '_') | (hasattr(val,'__call__') & (not isinstance(val, types.FunctionType))): 
                    continue
                instance_attributes[nm] = val
        return instance_attributes

    @property
    def process(self):
        """
        multiprocessing.Process receiving messages put in inbox 
        """
        if self._process is None:
            self._running_flag = multiprocessing.Value('i', 0)
            self._process = multiprocessing.Process(target = SupportingActor._listen, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self._running_flag, self.instance_attributes])
        return self._process
    
    @staticmethod
    def receive(message, **instance_attributes):
        """
        method called on messages put in inbox, requires implementation
        """
        raise NotImplemented()

    @staticmethod
    def callback(**instance_attributes):
        """
        method called when inbox reception done
        """
        print "No more messages in inbox."

    @staticmethod
    def handle(exc, message, **instance_attributes):
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
    def _listen(inbox, receive, callback, timeout, handle, running_flag, instance_attributes):
        """
        listens for incoming messages, executes callback when inbox reception complete, executes handle when exception raised
        """
        running_flag.value = 1 # This flag indicates whether the listening process is ongoing.
        
        # Use a timeout if timeout is an integer, otherwise do not.
        # If a timeout is being used, set an alarm to run _raise_timeout after timeout seconds.
        use_timeout = True if type(timeout) == int else False
        if use_timeout: 
            signal.signal(signal.SIGALRM, functools.partial(SupportingActor._raise_timeout, running_flag = running_flag))
            signal.alarm(timeout)
                 
        while running_flag.value == 1:                                              # While inbox reception is ongoing:
            
            try:                                                                    # Try
                message = inbox.get_nowait()                                        # to get a message immediately.
                if hasattr(message, '__waltz_cut__'):                               # If message has attribute __waltz_cut__,
                    if message.__waltz_cut__ == True:                               # and __waltz_cut__ is equal to True,
                        if message == Cut:                                          # and the message is Cut,
                            running_flag.value = 0                                  # flag inbox reception as not ongoing
                            break                                                   # and break the listening process
                if use_timeout: signal.alarm(0)                                     # Alarm turned off while running receive on message
            
            except:                                                                 # If any of the above fails
                continue                                                            # start the while loop again to ensure that the listening process should continue.
            
            try:                                                                    # With a non-Cut message try
                receive(message, **instance_attributes)                             # executing the receive function on the message
                if use_timeout : signal.alarm(timeout)                              # if successful, reset the alarm if appropriate. 
            except Exception as exc: handle(exc, message, **instance_attributes)    # If an exception is raised, pass it, the message, and the instance atributes to handle.
        
        if running_flag.value != -1:                                                # If running_flag does not have a value of -1 indicating the process was not cut immediately,
            callback(**instance_attributes)                                         # execute callback.

    def cut(self, immediate = False):
        """
        ends inbox processing

        Parameters
        __________
        immediate : boolean, default False
            If True, inbox processing is ended in place, otherwise inbox processing continues for all values already in the queue.
        """
        if immediate:
            self._running_flag.value = -1
        else:
            use_num = 1 if not hasattr(self,'num') else self.num
            for _ in xrange(use_num): self.inbox.put(Cut)            

    def __call__(self):
        """
        begin receiving messages put in inbox
        """
        if self._process is not None:
            print "Ending existing process..."
            self.cut(immediate = True)
            while self._process.is_alive():
                time.sleep(1)
            print "Existing process ended."
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

    @property
    def process(self):
        """
        multiprocessing.Process directing multiple actors receiving from a common inbox 
        """
        if self._process is None:
            self._running_flag = multiprocessing.Value('i', 0)
            self._process = multiprocessing.Process(target = SupportingCast._direct, args = [self.inbox, self.receive, self.callback, self.timeout, self.handle, self.num, self._running_flag, self.instance_attributes])
        return self._process

    @staticmethod
    def handle(exc, message, actors, **actor_attributes):
        """
        method called upon exception
        """
        print "Error for message:"
        print message
        for actor in actors: actor.terminate()
        raise exc

    @staticmethod
    def _listen(inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, actor_attributes):
        """
        listens for incoming messages, passes exceptions and the message that caused them to handle
        """
        while running_flag.value == 1:                              # While inbox reception is ongoing:
            
            try:                                                    # Try to get a message immediately.
                assert handling_error_flag.value == 0               # First check that the process isn't currently handling an error,
                assert error_queue.empty()                          # then check that the error queue is empty,
                message = inbox.get_nowait()                        # now attempt to get a message at once.
                if hasattr(message, '__waltz_cut__'):               # If message has attribute __waltz_cut__,
                    if message.__waltz_cut__ == True:               # and __waltz_cut__ is equal to True,
                        if message == Cut:                          # and the message is Cut,
                            break                                   # break the listening process.
                message_received_flag.value = 1                     # If we get a non-Cut message without waiting, toggle flag indicating that a message was received.
            
            except:                                                 # If any of the above fails
                continue                                            # start the while loop again to ensure that the listening process should continue.
            
            try: receive(message, **actor_attributes)               # With a non-Cut message try executing the receive function on the message.
            except Exception as exc:                                # If an exception is raised:
                error_queue.put((exc, message, actor_attributes))   # put it, the message, and the actor atributes in the error queue
                handling_error_flag.value = 1                       # and toggle the flag indicating that an error as being handled.
                while handling_error_flag.value == 1:               # While the flag is toggled to 1,
                    time.sleep(1)                                   # wait to proceed with the listening process.

    @staticmethod
    def _direct(inbox, receive, callback, timeout, handle, num, running_flag, instance_attributes):
        """
        cast and direct multiple actors receiving messages from a common inbox
        """
        running_flag.value = 1                                  # This flag indicates whether the listening process is ongoing.
        message_received_flag = multiprocessing.Value('i', 0)   # This flag gets toggled to 1 when individual actors receive messages, which causes the process to reset the timeout alarm.
        handling_error_flag = multiprocessing.Value('i', 0)     # This flag gets toggled to 1 when the process is handling an error and toggled back to zero when error handling is done.
        error_queue = multiprocessing.Manager().Queue()         # This queue holds information about errors.
        
        # Create a list of actors, processes who each listen for messages from a common inbox, then start each actor.
        actors = [multiprocessing.Process(
            target = SupportingCast._listen,
            args = [inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, dict(instance_attributes.items() + [('actor_id', i)])]
        ) for i in xrange(num)]
        for actor in actors: actor.start()
         
        # Use a timeout if timeout is an integer, otherwise do not.
        # If a timeout is being used, set an alarm to run _raise_timeout after timeout seconds.
        use_timeout = True if type(timeout) == int else False                                                                               
        if use_timeout:
            signal.signal(signal.SIGALRM, functools.partial(SupportingCast._raise_timeout, running_flag = running_flag))
            signal.alarm(timeout)
        
        while running_flag.value == 1:                                      # While inbox reception is ongoing:
            
            try:                                                            # Try the following:
                if not any([actor.is_alive() for actor in actors]):         # If no actor is alive,
                    running_flag.value = 0                                  # flag the listening process as complete,
                    break                                                   # and break the listening process.
                
                if not error_queue.empty():                                 # If there is an exception in the error queue,
                    if use_timeout: signal.alarm(0)                         # turn the alarm off if appropriate,
                    (exc, message, actor_attributes) = error_queue.get()    # catch the exception, the message, and the actor atributes,
                    handle(exc, message, actors, **actor_attributes)        # and pass them to handle.
                    handling_error_flag.value = 0                           # When handle is complete turn off the flag,
                    if use_timeout: signal.alarm(time_out)                  # and reset the alarm if appropriate.
                
                if use_timeout:                                             # If a timeout is being used,
                    if message_received_flag.value == 1:                    # and a message was received
                        signal.alarm(timeout)                               # reset the alarm,
                        message_received_flag.value = 0                     # and toggle the flag back to zero.

            except:                                                         # If any of the above failed,
                continue                                                    # jump to the top of the while loop to check if inbox reception is ongoing.
        
        if running_flag.value != -1:                                        # If running_flag does not have a value of -1 indicating the process was not cut immediately,
            callback(**instance_attributes)                                 # execute callback.

class Collector(SupportingActor):
  def __init__(self, **kwargs):
    SupportingActor.__init__(self, **kwargs)
    self.collected_outbox = multiprocessing.Manager().Queue()

  @staticmethod
  def collect(new_message, collected_messages, **collector_attributes):
    raise NotImplemented()

  @staticmethod
  def receive(message, **collector_attributes):
    collect_func = collector_attributes['collect']
    try:
      c = collector_attributes['collected_outbox'].get_nowait()
    except:
      c = None
    collected_messages = collect_func(message, c, **collector_attributes)
    collector_attributes['collected_outbox'].put(collected_messages)

class Cut:
    """
    when put in inbox of SupportingActor or SupportingCast instance shuts down inbox reception
    """
    __waltz_cut__ = True
