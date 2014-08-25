import multiprocessing
import signal
import time
import functools
import types
import inspect
import utils

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
        attr_dicts = [parent_class.__dict__ for parent_class in inspect.getmro(self.__class__)] + [self.__dict__]
        for attr_dict in attr_dicts:
            for nm, val in attr_dict.iteritems():
                if (nm == 'instance_attributes') or (nm.startswith('_')):
                    continue
                if (hasattr(val,'__call__') and (not isinstance(val, types.FunctionType))) or (isinstance(val, staticmethod)):
                    val = utils.globalmethod(val)
                instance_attributes[nm] = val
        return instance_attributes

    @property
    def process(self):
        """
        multiprocessing.Process receiving messages put in inbox 
        """
        if self._process is None:
            self._running_flag = multiprocessing.Value('i', 0)
            self._process = multiprocessing.Process(target = SupportingActor._listen, args = [self._running_flag, self.instance_attributes])
        return self._process
    
    @staticmethod
    def receive(message, instance_attributes):
        """
        method called on messages put in inbox, requires implementation
        """
        raise NotImplemented()

    @staticmethod
    def callback(instance_attributes):
        """
        method called when inbox reception done
        """
        print "Inbox processing done."

    @staticmethod
    def handle(exc, message, instance_attributes):
        """
        method called upon exception
        """
        print "Error for message:"
        print message
        raise exc

    @staticmethod
    def _timeout(signum, frame, running_flag):
        """
        shuts off the running_flag value, ending inbox reception
        """
        running_flag.value = 0

    @staticmethod
    def _listen(running_flag, instance_attributes):
        """
        listens for incoming messages, executes callback when inbox reception complete, executes handle when exception raised
        """
        running_flag.value = 1 # This flag indicates whether the listening process is ongoing.
        
        # Use a timeout if timeout is an integer, otherwise do not.
        # If a timeout is being used, set an alarm to run _timeout after timeout seconds.
        use_timeout = True if type(instance_attributes['timeout']) == int else False
        if use_timeout: 
            signal.signal(signal.SIGALRM, functools.partial(SupportingActor._timeout, running_flag = running_flag))
            signal.alarm(instance_attributes['timeout'])
                 
        while running_flag.value == 1:                                                                      # While inbox reception is ongoing:
            
            try:                                                                                            # Try
                message = instance_attributes['inbox'].get_nowait()                                         # to get a message immediately.
                if hasattr(message, '_caine_cut_'):                                                         # If message has attribute _caine_cut_,
                    if message._caine_cut_ == True:                                                         # and _caine_cut_ is equal to True,
                        running_flag.value = 0                                                              # flag inbox reception as not ongoing
                        break                                                                               # and break the listening process
                if use_timeout: signal.alarm(0)                                                             # Alarm turned off while running receive on message
            
            except:                                                                                         # If any of the above fails
                continue                                                                                    # start the while loop again to ensure that the listening process should continue.
            
            try:                                                                                            # With a non-Cut message try
                instance_attributes['receive'](message, instance_attributes)                                # executing the receive function on the message
                if use_timeout : signal.alarm(instance_attributes['timeout'])                               # if successful, reset the alarm if appropriate. 
            except Exception as exc: instance_attributes['handle'](exc, message, instance_attributes)       # If an exception is raised, pass it, the message, and the instance atributes to handle.
        
        if running_flag.value != -1:                                                                        # If running_flag does not have a value of -1 indicating the process was not cut immediately,
            instance_attributes['callback'](instance_attributes)                                            # execute callback.

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
    Data structure with operations for receiving objects put in its inbox using multiple caine.SupportingActor processes

    Parameters
    __________
    timeout : int or None, default None
        If not None, the number of seconds between message receptions before callback is executed
    num : int, default 1
        Number of actor processes
    kwargs : object
        Additional keyword arguments are set as attributes
    """
    def __init__(self, num = 1, **kwargs):
        self.num = num
        super(SupportingCast, self).__init__(**kwargs)

    @property
    def process(self):
        """
        multiprocessing.Process directing multiple actors receiving from a common inbox 
        """
        if self._process is None:
            self._running_flag = multiprocessing.Value('i', 0)
            self._process = multiprocessing.Process(target = SupportingCast._direct, args = [self._running_flag, self.instance_attributes])
        return self._process

    @staticmethod
    def handle(exc, message, actors, actor_attributes):
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
                if hasattr(message, '_caine_cut_'):                 # If message has attribute _caine_cut_,
                    if message._caine_cut_ == True:                 # and _caine_cut_ is equal to True,
                        break                                       # break the listening process.
                message_received_flag.value = 1                     # If we get a non-Cut message without waiting, toggle flag indicating that a message was received.
            
            except:                                                 # If any of the above fails
                continue                                            # start the while loop again to ensure that the listening process should continue.
            
            try: receive(message, actor_attributes)                 # With a non-Cut message try executing the receive function on the message.
            except Exception as exc:                                # If an exception is raised:
                error_queue.put((exc, message, actor_attributes))   # put it, the message, and the actor atributes in the error queue
                handling_error_flag.value = 1                       # and toggle the flag indicating that an error as being handled.
                while handling_error_flag.value == 1:               # While the flag is toggled to 1,
                    time.sleep(1)                                   # wait to proceed with the listening process.

    @staticmethod
    def _direct(running_flag, instance_attributes):
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
            args = [instance_attributes['inbox'], instance_attributes['receive'], error_queue, running_flag, message_received_flag, handling_error_flag, dict(instance_attributes.items() + [('actor_id', i)])]
        ) for i in xrange(instance_attributes['num'])]
        for actor in actors: actor.start()
         
        # Use a timeout if timeout is an integer, otherwise do not.
        # If a timeout is being used, set an alarm to run _timeout after timeout seconds.
        use_timeout = True if type(instance_attributes['timeout']) == int else False                                                                               
        if use_timeout:
            signal.signal(signal.SIGALRM, functools.partial(SupportingCast._timeout, running_flag = running_flag))
            signal.alarm(instance_attributes['timeout'])
        
        while running_flag.value == 1:                                                          # While inbox reception is ongoing:
            
            try:                                                                                # Try the following:
                if not any([actor.is_alive() for actor in actors]):                             # If no actor is alive,
                    running_flag.value = 0                                                      # flag the listening process as complete,
                    break                                                                       # and break the listening process.
                
                if not error_queue.empty():                                                     # If there is an exception in the error queue,
                    if use_timeout: signal.alarm(0)                                             # turn the alarm off if appropriate,
                    (exc, message, actor_attributes) = error_queue.get()                        # catch the exception, the message, and the actor atributes,
                    instance_attributes['handle'](exc, message, actors, actor_attributes)       # and pass them to handle.
                    handling_error_flag.value = 0                                               # When handle is complete turn off the flag,
                    if use_timeout: signal.alarm(time_out)                                      # and reset the alarm if appropriate.
                
                if use_timeout:                                                                 # If a timeout is being used,
                    if message_received_flag.value == 1:                                        # and a message was received
                        signal.alarm(instance_attributes['timeout'])                            # reset the alarm,
                        message_received_flag.value = 0                                         # and toggle the flag back to zero.

            except:                                                                             # If any of the above failed,
                continue                                                                        # jump to the top of the while loop to check if inbox reception is ongoing.
        
        if running_flag.value != -1:                                                            # If running_flag does not have a value of -1 indicating the process was not cut immediately,
            instance_attributes['callback'](instance_attributes)                                # execute callback.

class Collector(SupportingActor):
    """
    Data structure with operations for collecting objects put in its inbox.

    Parameters
    __________
    timeout : int or None, default None
        If not None, the number of seconds between message receptions before callback is executed
    kwargs : object
        Additional keyword arguments are set as attributes
    """
    def __init__(self, **kwargs):
        super(Collector, self).__init__(**kwargs)
        self._pipe_in, self._pipe_out = multiprocessing.Pipe()
  
    @property
    def instance_attributes(self):
        """
        dict with atributes of instance
        """
        # Collector.receive needs both ends of the pipe, so we include these in the instance attributes
        return dict(SupportingActor.instance_attributes.__get__(self).items() + {'_pipe_in': self._pipe_in, '_pipe_out': self._pipe_out}.items())

    @property
    def collected(self):
        """
        all collected messages if inbox processing is complete, otherwise None
        """
        if not self.process.is_alive():         # If the process is not alive,
            if self._pipe_out.poll():           # and there's data in the output end of the pipe,
                return self._pipe_out.recv()    # return the data in the pipe,
        return None                             # otherwise return None.

    @staticmethod
    def collect(new_message, prior_collected, instance_attributes):
        """
        returns collected messages when passed a new message and prior messages, requires implementation
        """
        raise NotImplemented()

    @staticmethod
    def receive(message, instance_attributes):
        if instance_attributes['_pipe_out'].poll():                                                         # If the output end of the pipe has data,
            prior_collected = instance_attributes['_pipe_out'].recv()                                       # get that data from the pipe
        else:                                                                                               # otherwise,
            prior_collected = None                                                                          # there are no previously collected messages.
        newly_collected = instance_attributes['collect'](message, prior_collected, instance_attributes)     # Get the newly collected messages by passing the new message, the previously collected messages and the instance attributes to collect.              
        instance_attributes['_pipe_in'].send(newly_collected)                                               # Send the newly collected messages to the pipe.

class Cut:
    """
    when put in inbox of SupportingActor or SupportingCast instance shuts down inbox reception
    """
    _caine_cut_ = True
