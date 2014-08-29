import multiprocessing
import signal
import time
import functools
import types
import inspect

def _receive(message, instance_attributes):
    """
    method called on messages put in inbox, requires implementation
    """
    raise NotImplemented()

def _callback(instance_attributes):
    """
    method called when inbox reception done
    """
    print "Inbox processing done."

def _handle(exc, message, instance_attributes):
    """
    method called upon exception
    """
    print "Error for message:"
    print message
    raise exc

def _timeout(signum, frame, running_flag):
    """
    shuts off the running_flag value, ending inbox reception
    """
    running_flag.value = 0

def _listen_active(running_flag, instance_attributes, pipe_collect = None):
    """
    listens for incoming messages, executes callback when inbox reception complete, executes handle when exception raised
    """
    running_flag.value = 1                                  # 1 : listening process is ongoing, 0 : listening process ended naturally, -1 : listening process was cut immediately
    if pipe_collect is not None: prior_collected = None     # We keep track of previously collected messages if pipe_collect is not None.
    
    # Use a timeout if timeout is an integer, otherwise do not.
    # If a timeout is being used, set an alarm to run _timeout after timeout seconds.
    use_timeout = True if type(instance_attributes['timeout']) == int else False
    if use_timeout: 
        signal.signal(signal.SIGALRM, functools.partial(_timeout, running_flag = running_flag))
        signal.alarm(instance_attributes['timeout'])
             
    while running_flag.value == 1:                                                                                  # While inbox reception is ongoing:
        
        try:                                                                                                        # Try
            message = instance_attributes['inbox'].get_nowait()                                                     # to get a message immediately.
            if hasattr(message, '_caine_cut_'):                                                                     # If message has attribute _caine_cut_,
                if message._caine_cut_ == True:                                                                     # and _caine_cut_ is equal to True,
                    running_flag.value = 0                                                                          # flag inbox reception as not ongoing
                    break                                                                                           # and break the listening process
            if use_timeout: signal.alarm(0)                                                                         # Alarm turned off while running receive on message
        
        except:                                                                                                     # If any of the above fails
            continue                                                                                                # start the while loop again to ensure that the listening process should continue.
        
        try:                                                                                                        # With a non-Cut message,
            if pipe_collect is not None:                                                                            # if there is a pipe to collect messages,
                prior_collected = instance_attributes['collect'](message, prior_collected, instance_attributes)     # try executing the collect function on the message, the previously collected messages and the instance attributes
            else:                                                                                                   # otherwise,
                instance_attributes['receive'](message, instance_attributes)                                        # execute the receive function on the message and the instance attributes.
            if use_timeout : signal.alarm(instance_attributes['timeout'])                                           # if successful, reset the alarm if appropriate. 
        except Exception as exc: instance_attributes['handle'](exc, message, instance_attributes)                   # If an exception is raised, pass it, the message, and the instance atributes to handle.
    
    if running_flag.value != -1:                                                                                    # If running_flag does not have a value of -1 indicating the process was not cut immediately,
        if pipe_collect is not None: pipe_collect.send(prior_collected)                                             # send the previously collected messages through the pipe if appropriate,
        instance_attributes['callback'](instance_attributes)                                                        # and execute callback.

def _handle_direct(exc, message, actor_id, actors, instance_attributes):
    """
    method called upon exception
    """
    print "Actor with id <%s> raised an exception." %(actor_id)
    print "Message on which exception was raised: %s" %(message)
    print "Exception type: %s" %(type(exc))
    print "Exception message: %s" %(exc.message)
    print "Exception args: %s" %(", ".join([str(arg) for arg in exc.args]))
    print "Terminating actor with id <%s>..." %(actor_id)
    actors[actor_id].terminate()
    print "Actor with id <%s> terminated." %(actor_id)

def _listen_passive(inbox, receive, error_queue, running_flag, message_received_flag, handling_error_flag, cut_flag, actor_attributes):
    """
    listens for incoming messages, passes exceptions and the message that caused them to handle
    """
    while running_flag.value == 1:                                          # While inbox reception is ongoing:
        
        try:                                                                # Try to get a message immediately.
            assert handling_error_flag.value == 0                           # First check that the process isn't currently handling an error,
            assert error_queue.empty()                                      # then check that the error queue is empty,
            message = inbox.get_nowait()                                    # now attempt to get a message at once.
            if hasattr(message, '_caine_cut_'):                             # If message has attribute _caine_cut_,
                if message._caine_cut_ == True:                             # and _caine_cut_ is equal to True,
                    if cut_flag.value == 0: cut_flag.value = 1              # if cut_flag has a value of zero, then the other actors have not been cut yet, so we toggle the flag to 1,
                    break                                                   # either way, break the listening process.
            message_received_flag.value = 1                                 # If we get a non-Cut message without waiting, toggle flag indicating that a message was received.
        
        except:                                                             # If any of the above fails
            continue                                                        # start the while loop again to ensure that the listening process should continue.
        
        try: receive(message, actor_attributes)                             # With a non-Cut message try executing the receive function on the message.
        except Exception as exc:                                            # If an exception is raised:
            error_queue.put((exc, message, actor_attributes['actor_id']))   # put it, the message, and the actor_id in the error queue,
            handling_error_flag.value = 1                                   # and toggle the flag indicating that an error as being handled.
            while handling_error_flag.value == 1:                           # While the flag is toggled to 1,
                time.sleep(1)                                               # wait to proceed with the listening process.

def _direct(running_flag, instance_attributes):
    """
    cast and direct multiple actors receiving messages from a common inbox
    """
    running_flag.value = 1                                  # 1 : listening process is ongoing, 0 : listening process ended naturally, -1 : listening process was cut immediately
    message_received_flag = multiprocessing.Value('i', 0)   # 1 : some actor recently received a message, 0 : actor has not received a message since last checked
    handling_error_flag = multiprocessing.Value('i', 0)     # 1 : _direct process is currently handling an error, 0 :  _direct process is not currently handling an error
    cut_flag = multiprocessing.Value('i', 0)                # 1 : an actor received cut, 0 : no actor has yet received cut, -1 : no longer check for whether an actor received cut
    error_queue = multiprocessing.Manager().Queue()         # This queue holds information about errors.
    
    # Create a dictionary of actors, processes who each listen for messages from a common inbox, then start each actor.
    actors = {i : multiprocessing.Process(
        target = _listen_passive,
        args = [instance_attributes['inbox'], instance_attributes['receive'], error_queue, running_flag, message_received_flag, handling_error_flag, cut_flag, dict(instance_attributes.items() + {'actor_id': i}.items())]
    ) for i in xrange(instance_attributes['num'])}
    for actor in actors.values(): actor.start()
     
    # Use a timeout if timeout is an integer, otherwise do not.
    # If a timeout is being used, set an alarm to run _timeout after timeout seconds.
    use_timeout = True if type(instance_attributes['timeout']) == int else False                                                                               
    if use_timeout:
        signal.signal(signal.SIGALRM, functools.partial(_timeout, running_flag = running_flag))
        signal.alarm(instance_attributes['timeout'])
    
    while running_flag.value == 1:                                                                  # While inbox reception is ongoing:
        
        try:                                                                                        # Try the following:
            if not any([actor.is_alive() for actor in actors.values()]):                            # If no actor is alive,
                running_flag.value = 0                                                              # flag the listening process as complete,
                break                                                                               # and break the listening process.
            
            while not error_queue.empty():                                                          # If there is an exception in the error queue,
                if use_timeout: signal.alarm(0)                                                     # turn the alarm off if appropriate,
                (exc, message, actor_id) = error_queue.get()                                        # catch the exception, the message, and the actor_od,
                instance_attributes['handle'](exc, message, actor_id, actors, instance_attributes)  # and pass them to handle.
                if use_timeout: signal.alarm(time_out)                                              # Reset the alarm if appropriate.
            handling_error_flag.value = 0                                                           # When the error queue is empty, turn off the flag.    
            
            if cut_flag.value == 1:                                                                 # If one of the actors received Cut,
                for _ in xrange(instance_attributes['num'] - 1):                                    # put num - 1
                    instance_attributes['inbox'].put(Cut)                                           # copies of Cut in the inbox to cut the other actors.
                cut_flag.value = -1                                                                 # Set the cut_flag to -1 such that this only happens once per run of _direct.

            if use_timeout:                                                                         # If a timeout is being used,
                if message_received_flag.value == 1:                                                # and a message was received
                    signal.alarm(instance_attributes['timeout'])                                    # reset the alarm,
                    message_received_flag.value = 0                                                 # and toggle the flag back to zero.

        except:                                                                                     # If any of the above failed,
            continue                                                                                # jump to the top of the while loop to check if inbox reception is ongoing.
    
    if running_flag.value != -1:                                                                    # If running_flag does not have a value of -1 indicating the process was not cut immediately,
        instance_attributes['callback'](instance_attributes)                                        # execute callback.

def _collect(new_message, prior_collected, instance_attributes):
    """
    returns collected messages when passed a new message and prior messages, requires implementation
    """
    raise NotImplemented()

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
        self._process = None
        self.receive = _receive
        self.callback = _callback
        self.handle = _handle
        self._running_flag = multiprocessing.Value('i', 0)
        self._process_func = _listen_active
        for nm, val in kwargs.iteritems(): setattr(self, nm, val)

    @property
    def _process_args(self):
        return [self._running_flag, self.instance_attributes]

    @property
    def instance_attributes(self):
        """
        dict with atributes of instance
        """
        instance_attributes = {}
        attr_dicts =  [self.__dict__] + [parent_class.__dict__ for parent_class in inspect.getmro(self.__class__)]
        for attr_dict in attr_dicts:
            for nm, val in attr_dict.iteritems():
                if (nm == 'instance_attributes') or (nm.startswith('_')) or nm in instance_attributes:
                    continue
                instance_attributes[nm] = val
        return instance_attributes

    @property
    def process(self):
        """
        multiprocessing.Process
        """
        if self._process is None:
            self._process = multiprocessing.Process(target = self._process_func, args = self._process_args)
        return self._process
    
    def cut(self, immediate = False):
        """
        ends inbox processing

        Parameters
        __________
        immediate : boolean, default False
            If True, inbox processing is ended in place, otherwise inbox processing continues for all values already in the queue.
        """
        if immediate: self._running_flag.value = -1
        else: self.inbox.put(Cut)

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
        SupportingActor.__init__(self, **kwargs)
        self.handle = _handle_direct
        self._process_func = _direct

class Collector(SupportingActor):
    """
    Data structure with operations for collecting objects put in its inbox.
    Note: Collector.process may remain alive as long as Collector.collected is not used.

    Parameters
    __________
    timeout : int or None, default None
        If not None, the number of seconds between message receptions before callback is executed
    kwargs : object
        Additional keyword arguments are set as attributes
    """
    def __init__(self, **kwargs):
        self.collect = _collect
        SupportingActor.__init__(self, **kwargs)
        self._pipe_in, self._pipe_out = multiprocessing.Pipe()
        self._collected = None

    @property
    def _process_args(self):
        return [self._running_flag, self.instance_attributes, self._pipe_in]

    @property
    def collected(self):
        """
        all collected messages if inbox processing is complete, otherwise None
        """
        if self._pipe_out.poll():                       # If there's data in the output end of the pipe,
            self._collected = self._pipe_out.recv()     # overwrite the private attribute using the data in the pipe,
        return self._collected                          # return the private attribute holding the collected messages.

class Cut:
    """
    when put in inbox of SupportingActor or SupportingCast instance shuts down inbox reception
    """
    _caine_cut_ = True
