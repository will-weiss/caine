import multiprocessing
import signal
import time
import functools
import inspect

class SupportingActor(object):
    """
    Data structure with operations for receiving objects put in its inbox.

    Parameters
    __________
    timeout : int or None, default None
        If not None, the number of seconds between message receptions before callback is executed
    maxsize : int or None, default None
        If not None, the maximum size of the inbox
    kwargs : object
        Additional keyword arguments are set as attributes
    """

    def __init__(self, timeout = None, maxsize = None, **kwargs):
        self.inbox = multiprocessing.Manager().Queue(maxsize)           # Set up a task queue with maximum size that can be inserted into and read by multiple processes.
        self.timeout = timeout                                          # The number of seconds before the process times out.
        self.receive = _receive                                         # The receive function, by default is the global private method _receive.
        self.callback = _callback                                       # The callback function, by default is the global private method _callback.
        self.handle = _handle                                           # The handle function, by default is the global private method _handle.
        self._process = None                                            # The private _process initially is None.
        self._running_flag = multiprocessing.Value('i', 0)              # A flag - 1 : inbox reception is ongoing, 0 : inbox reception ended naturally, -1 : inbox reception was cut immediately
        self._process_func = _listen_active                             # _listen_active is the target function of the inbox reception process.
        for nm, val in kwargs.iteritems(): setattr(self, nm, val)       # All other collected keyword arguments are set as attributes.

    @property
    def instance_attributes(self):
        """
        dict with public atributes of instance
        """
        instance_attributes = {}                                                                                    # Set up a dictionary for storing attributes.
        attr_dicts =  [self.__dict__] + [parent_class.__dict__ for parent_class in inspect.getmro(self.__class__)]  # Get a list of dictionaries with attributes with order identical to method resolution.
        for attr_dict in attr_dicts:                                                                                # For each dictionary with attributes,
            for nm, val in attr_dict.iteritems():                                                                   # for each attribute name, value pair
                if (nm == 'instance_attributes') or (nm.startswith('_')) or nm in instance_attributes:              # if the name is instance_attributes, starts with an underscore (is private), or is already represented
                    continue                                                                                        # do nothing with this name, value pair,
                instance_attributes[nm] = val                                                                       # otherwise store the attribute in instance_attributes.
        return instance_attributes                                                                                  # Return instance_attributes on completion.

    @property
    def _process_args(self):
        return [self._running_flag, self.instance_attributes] # pass these arguments to _listen_active

    @property
    def process(self):
        """
        multiprocessing.Process
        """
        if self._process is None:                                                                               # If _process is None,
            self._process = multiprocessing.Process(target = self._process_func, args = self._process_args)     # set it as a multiprocessing.Process running _process_func and using the arguments _process_args
        return self._process                                                                                    # return the private _process as public process.
    
    def cut(self, immediate = False):
        """
        ends inbox processing

        Parameters
        __________
        immediate : boolean, default False
            If True, inbox processing is ended in place, otherwise inbox processing continues until queue is empty.
        """
        if immediate: self._running_flag.value = -1     # Breaks inbox reception loop
        else: self.inbox.put(Cut)                       # Inbox processing terminates when inbox is empty

    def __call__(self):
        """
        begin receiving messages put in inbox
        """
        if self._process is not None:                           # If there is an ongoing private process,
            print "Cutting existing process..."                 # notify the user that the existing process is being cut immediately,
            self.cut(immediate = True)                          # cut that process immediately,
            while self._process.is_alive(): time.sleep(.1)      # wait for that process to die,
            print "Existing process has been cut."              # then notify the user that the existing process has been cut.
        self._process = None                                    # Set the private _process as None, such that a new multiprocessing.Process is generated when self.process is used,
        self.process.start()                                    # and start the new public process.

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
        SupportingActor.__init__(self, **kwargs)                                        # Inherit the attributes, methods of SupportingActor.
        if 'handle' not in kwargs : self.handle = _handle_direct                        # By default, SupportingCast.handle is the global method _handle_direct.
        self._process_func = _direct                                                    # _direct is the target function of the inbox reception process.
        self._num_actor_to_add = multiprocessing.Value('i', num)                        # To start, there are num actors to add.
        self._num_actors_added = multiprocessing.Value('i', 0)                          # To start, zero actors have been added.
        self._add = functools.partial(_add, num_actor_to_add = self._num_actor_to_add)  # This instance's _add method refers to the global method _add where the keyword argument num_actor_to_add refers to the instance's _num_actor_to_add

    @property
    def num(self):
        return self._num_actor_to_add.value + self._num_actors_added.value # num refers to the number of actors to add, plus the number of actors added

    def add(self, num = 1):
        """
        adds actor(s) to process inbox
        
        Parameters
        __________
        num : int, default 1
            The number of actors to add
        """
        self._add(num = num)

    def remove(self, num = 1):
        """
        removes existing actor(s)
        
        Parameters
        __________
        num : int, default 1
            The number of actors to remove
        """
        self._add(num = -num)

    @property
    def _process_args(self):
        return [self._running_flag, self._num_actor_to_add, self._num_actors_added, self.instance_attributes] # pass these arguments to _direct

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
        self.collect = _collect                                 # By default, Collector.collect is the global method _collect
        SupportingActor.__init__(self, **kwargs)                # Inherit the attributes, methods of SupportingActor.
        self._outbox = multiprocessing.Manager().Queue(1)       # A queue of maximum size 1 is used to receive collected messages upon completion.
        self._collected = None                                  # There are no collected messages to start.

    @property
    def _process_args(self):
        return [self._running_flag, self.instance_attributes, self._outbox] # pass these arguments to _listen_active

    @property
    def collected(self):
        """
        all collected messages if inbox processing is complete, otherwise None
        """
        if not self._outbox.empty():                # If there's data in the outbox,
            self._collected = self._outbox.get()    # overwrite the private attribute using the data in the outbox,
        return self._collected                      # return the private attribute holding the collected messages.

class Cut:
    """
    shuts down inbox reception when put in inbox of SupportingActor or SupportingCast instance
    """

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

def _listen_active(running_flag, instance_attributes, collect_outbox = None):
    """
    listens for incoming messages, executes callback when inbox reception complete, executes handle when exception raised
    """
    running_flag.value = 1                                  # Flag inbox reception as ongoing.
    if collect_outbox is not None:                          # If collect_outbox is not None,
        prior_collected = None                              # previously collected messages are None,
        instance_attributes['collected'] = None             # and the collected attribute is None.
    
    # Use a timeout if timeout is an integer, otherwise do not.
    # If a timeout is being used, set an alarm to run _timeout after timeout seconds.
    use_timeout = True if type(instance_attributes['timeout']) == int else False
    if use_timeout: 
        signal.signal(signal.SIGALRM, functools.partial(_timeout, running_flag = running_flag))
        signal.alarm(instance_attributes['timeout'])
             
    while running_flag.value == 1:                                                                                  # While the listening process is ongoing:
        
        try:                                                                                                        # Try
            message = instance_attributes['inbox'].get_nowait()                                                     # to get a message immediately.
            if message is Cut:                                                                                      # If message is attribute Cut,
                running_flag.value = 0                                                                              # flag inbox reception as not ongoing
                break                                                                                               # and break the listening process                                                                                    
            if use_timeout: signal.alarm(0)                                                                         # Alarm turned off while running receive on message
        except:                                                                                                     # If any of the above fails
            continue                                                                                                # start the while loop again to ensure that the listening process should continue.
        
        try:                                                                                                        # With a non-Cut message,
            if collect_outbox is not None:                                                                          # if there is an outbox to collect messages,
                prior_collected = instance_attributes['collect'](message, prior_collected, instance_attributes)     # try executing the collect function on the message, the previously collected messages and the instance attributes
            else:                                                                                                   # otherwise,
                new_attrs = instance_attributes['receive'](message, instance_attributes)                            # execute the receive function on the message and the instance attributes.
                if type(new_attrs) is dict: actor_attributes.update(new_attrs)                                      # If receive returns any new attributes, update the instance attributes.
            if use_timeout : signal.alarm(instance_attributes['timeout'])                                           # if successful, reset the alarm if appropriate. 
        except Exception as exc: instance_attributes['handle'](exc, message, instance_attributes)                   # If an exception is raised, pass it, the message, and the instance atributes to handle.
    
    if running_flag.value != -1:                                                                                    # If running_flag does not have a value of -1 indicating the process was not cut immediately,
        if collect_outbox is not None:                                                                              # If collect_outbox is not None,
            collect_outbox.put(prior_collected)                                                                     # put the previously collected messages in the outbox,
            instance_attributes['collected'] = prior_collected                                                      # and set the collected attribute as prior_collected.
        instance_attributes['callback'](instance_attributes)                                                        # Execute callback.

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

def _listen_passive(inbox, receive, listening_flag, message_received_flag, handling_error_flag, cut_flag, error_queue, actor_attributes):
    """
    listens for incoming messages, passes exceptions and the message that caused them to handle
    """
    while listening_flag.value == 1:                                        # While the listening process is ongoing:
        
        try:                                                                # Try to get a message immediately.
            assert handling_error_flag.value == 0                           # First check that the process isn't currently handling an error,
            assert error_queue.empty()                                      # then check that the error queue is empty,
            message = inbox.get_nowait()                                    # now attempt to get a message at once.
            if message is Cut:                                              # If the message is Cut,
                cut_flag.value = 1                                          # toggle the flag to 1,
                break                                                       # and break the listening process.
            message_received_flag.value = 1                                 # If we get a non-Cut message without waiting, toggle flag indicating that a message was received.
        
        except:                                                             # If any of the above fails
            continue                                                        # start the while loop again to ensure that the listening process should continue.
        
        try: 
            new_attrs = receive(message, actor_attributes)                  # With a non-Cut message try executing the receive function on the message.
            if type(new_attrs) is dict: actor_attributes.update(new_attrs)  # If receive returns any new attributes, update the instance attributes.
        except Exception as exc:                                            # If an exception is raised:
            error_queue.put((exc, message, actor_attributes['actor_id']))   # put it, the message, and the actor_id in the error queue,
            handling_error_flag.value = 1                                   # and toggle the flag indicating that an error as being handled.
            while handling_error_flag.value == 1:                           # While the flag is toggled to 1,
                time.sleep(.1)                                              # wait to proceed with the listening process.

def _direct(running_flag, num_actor_to_add, num_actor_added, instance_attributes):
    """
    cast and direct multiple actors receiving messages from a common inbox
    """
    running_flag.value = 1                                  # Flag inbox reception as ongoing.
    del instance_attributes['num']                          # The num value for the instance of supporting cast may change so it is dropped as an attribute
    message_received_flag = multiprocessing.Value('i', 0)   # 1 : some actor recently received a message, 0 : actor has not received a message since last checked
    handling_error_flag = multiprocessing.Value('i', 0)     # 1 : _direct process is currently handling an error, 0 :  _direct process is not currently handling an error
    cut_flag = multiprocessing.Value('i', 0)                # 1 : an actor received cut, 0 : no actor has yet received cut
    error_queue = multiprocessing.Manager().Queue()         # This queue holds information about errors
    actors = {}                                             # This dictionary holds the listening flags and processes for each actor

    # Use a timeout if timeout is an integer, otherwise do not.
    # If a timeout is being used, set an alarm to run _timeout after timeout seconds.
    use_timeout = True if type(instance_attributes['timeout']) == int else False                                                                               
    if use_timeout:
        signal.signal(signal.SIGALRM, functools.partial(_timeout, running_flag = running_flag))
        signal.alarm(instance_attributes['timeout'])
    
    while running_flag.value == 1:                                                                  # While inbox reception is ongoing:
        
        try:                                                                                        # Try the following:

            if num_actor_to_add.value != 0:                                                         # If the number of actors to add is not equal to zero,
                if use_timeout: signal.alarm(0)                                                     # Turn off the alarm if appropriate.
                n = len(actors)                                                                     # n is the number of actors we currently have.
                if num_actor_to_add.value > 0:                                                      # If the number of actors to add is positive.
                    actors[n] = {'listening_flag' : multiprocessing.Value('i', 1)}                  # Create a dictionary for a new actor with a listening flag toggled to 1 indicating the listening process is ongoing.
                    actors[n]['process'] = multiprocessing.Process(                                 # The new actor has a process which runs _listen_passive and is passed the necessary arguments.
                        target = _listen_passive, 
                        args = [instance_attributes['inbox'], instance_attributes['receive'], 
                                actors[n]['listening_flag'], message_received_flag, 
                                handling_error_flag, cut_flag, error_queue, 
                                dict(instance_attributes.items() + {'actor_id': n}.items())])
                    actors[n]['process'].start()                                                    # The new actor process is started.
                    num_actor_to_add.value -= 1                                                     # The number of actors to add decreases by 1.
                    num_actor_added.value += 1                                                      # The number of actors added increases by 1.
                elif num_actor_to_add.value < 0:                                                    # If the number of actors to add is negative
                    if n <= 0: num_actor_to_add.value += 1                                          # but there are zero actors, increase the number of actors to add by 1 (toward zero), but make no other changes.
                    else:                                                                           # Otherwise, remove an actor
                        actors[n-1]['listening_flag'].value = 0                                     # by toggling off its listening flag,
                        while actors[n-1]['process'].is_alive(): time.sleep(.1)                     # waiting for its process to stop
                        del actors[n-1]                                                             # then removing the actor from the actors dictionary.
                        num_actor_to_add.value += 1                                                 # The number of actors to add increases by 1 (toward zero).
                        num_actor_added.value -= 1                                                  # The number of actors added decreases by 1.
                signal.alarm(instance_attributes['timeout'])                                        # Reset the alarm if appropriate
                continue                                                                            # and jump to the top of the loop.

            if not any([actor['process'].is_alive() for actor in actors.values()]):                 # If no actor is alive,
                running_flag.value = 0                                                              # flag inbox reception as complete,
                break                                                                               # and break inbox reception.
            
            while not error_queue.empty():                                                          # If there is an exception in the error queue,
                if use_timeout: signal.alarm(0)                                                     # turn the alarm off if appropriate,
                (exc, message, actor_id) = error_queue.get()                                        # catch the exception, the message, and the actor_id,
                instance_attributes['handle'](exc, message, actor_id, actors, instance_attributes)  # and pass them to handle.
                if use_timeout: signal.alarm(instance_attributes['timeout'])                        # Reset the alarm if appropriate.
            handling_error_flag.value = 0                                                           # When the error queue is empty, turn off the flag.    
            
            if cut_flag.value == 1:                                                                 # If one of the actors received Cut,
                if use_timeout: signal.alarm(0)                                                     # turn off the alarm,
                while not instance_attributes['inbox'].empty(): time.sleep(.1)                      # wait for the inbox to be empty,
                running_flag.value = 0                                                              # flag inbox reception as complete,      
                break                                                                               # and break inbox reception.

            if use_timeout:                                                                         # If a timeout is being used,
                if message_received_flag.value == 1:                                                # and a message was received
                    signal.alarm(instance_attributes['timeout'])                                    # reset the alarm,
                    message_received_flag.value = 0                                                 # and toggle the flag back to zero.

        except:                                                                                     # If any of the above failed,
            continue                                                                                # jump to the top of the while loop to check if inbox reception is ongoing.
    
    for actor in actors.values(): actor['listening_flag'].value = 0                                 # Once the main loop is escaped, the actors are toggled to stop listening,
    while any([actor['process'].is_alive() for actor in actors.values()]): time.sleep(.1)           # sleep while the actors are ongoing.
    if running_flag.value != -1: instance_attributes['callback'](instance_attributes)               # If running_flag does not have a value of -1 indicating the process was not cut immediately, execute callback.

def _add(num_actor_to_add, num):
    """
    adds num to num_actor_to_add
    """
    num_actor_to_add.value += num 

def _collect(new_message, prior_collected, instance_attributes):
    """
    returns collected messages when passed a new message and prior messages, requires implementation
    """
    raise NotImplemented()
