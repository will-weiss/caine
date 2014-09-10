caine
=====

supporting actors process queues concurrently

Contact/Contribute
~~~~~~~

Email: will.weiss1230@gmail.com
GitHub:  https://github.com/will-weiss/caine

Install
~~~~~~~

pip install caine

Usage
~~~~~

from caine import SupportingActor

def deliver(line, instance_attributes):
    print '%s says, "%s"' %(instance_attributes['name'], line)

def end_scene(instance_attributes):
    print "End scene."

# An actor which executes deliver using messages in its inbox and executes end_scene on completion
my_actor = SupportingActor(receive = deliver, callback = end_scene, name = 'Michael')

# Call my_actor to commence inbox processing.
my_actor()

# Put messages in inbox of my_actor.
my_actor.inbox.put("You were only supposed to blow the bloody doors off!")
my_actor.inbox.put("She was only sixteen years old!")
my_actor.inbox.put("Not many people know that!")

# Tell my_actor that it is complete when its inbox is empty.
my_actor.cut()

# Output
# ------
# Michael says, "You were only supposed to blow the bloody doors off!"
# Michael says, "She was only sixteen years old!"
# Michael says, "Not many people know that!"
# End scene.

More Horsepower
~~~~~~~~~~~~~~~

from caine import SupportingCast
import time
import random

num_actors = 3 # SupportingCast will have 3 actors

def wait_deliver(message, actor_attributes):
    wait_secs = random.randint(1,5)
    time.sleep(wait_secs)
    print 'Actor #%s waited %s seconds to say, "%s"' %(actor_attributes['actor_id'], wait_secs, message)

def end_scene(instance_attributes):
    print "End scene."

my_cast = SupportingCast(receive = wait_deliver, callback = end_scene, num = num_actors)

my_cast()

for i in xrange(10):
    my_cast.inbox.put("I got message #%s." %(i))

my_cast.cut()

# Output
# ------
# Actor #0 waited 2 seconds to say, "I got message #0."
# Actor #0 waited 1 seconds to say, "I got message #3."
# Actor #1 waited 5 seconds to say, "I got message #1."
# Actor #2 waited 5 seconds to say, "I got message #2."
# Actor #0 waited 3 seconds to say, "I got message #4."
# Actor #1 waited 2 seconds to say, "I got message #5."
# Actor #2 waited 2 seconds to say, "I got message #6."
# Actor #0 waited 3 seconds to say, "I got message #7."
# Actor #2 waited 2 seconds to say, "I got message #9."
# Actor #1 waited 2 seconds to say, "I got message #8."
# End scene.

Collecting Messages
~~~~~~~~~~~~~~~~~~~

from caine import Collector

# A function which synthesizes a new message and prior messages
def print_even_collect_odd(new_number, collected_odds, instance_attributes):
    collected_odds = collected_odds if collected_odds is not None else []
    if new_number % 2 == 0: 
        print "I got the even number: %s" %(new_number)
    else: 
        collected_odds.append(new_number)
    return collected_odds

# A function called on completion
def print_collected(instance_attributes):
    print "I collected these odd numbers: %s" %(instance_attributes['collected'])

my_collector = Collector(collect = print_even_collect_odd, callback = print_collected)
my_collector()

for i in xrange(10):
    my_collector.inbox.put(i)

my_collector.cut()

# Output
# ------
# I got the even number: 0
# I got the even number: 2
# I got the even number: 4
# I got the even number: 6
# I got the even number: 8
# I collected these odd numbers: [1, 3, 5, 7, 9]

Other Functions
~~~~~~~~~~~~~~~

# Immediate Cut

for i in xrange(3):
    my_cast.inbox.put("I got this message in time to say it!")

my_cast()
time.sleep(6)

# Items put in inbox after this will not be processed and callback will not be executed
my_cast.cut(immediate = True) 

for i in xrange(3):
    my_cast.inbox.put("I did not get this message in time to say it!")

# Output
# ------
# Actor #2 waited 2 seconds to say, "I got this message in time to say it!"
# Actor #0 waited 4 seconds to say, "I got this message in time to say it!"
# Actor #1 waited 4 seconds to say, "I got this message in time to say it!"

# Adding Actors to Cast

original_actor_count = 3 # The cast starts with 3 actors
add_actor_count = 3      # The cast will have 3 actors added to it

def deliver(message_num, actor_attributes):
    time.sleep(1)
    if actor_attributes['actor_id'] < original_actor_count:
        print 'I am an actor from the original cast! I got message #%s' %(message_num)
    else:
        print 'I am an actor created later! I got message #%s' %(message_num)

def end_scene(instance_attributes):
    print "End scene."

my_cast = SupportingCast(receive = deliver, callback = end_scene, num = original_actor_count)
my_cast()

for i in xrange(3):
    my_cast.inbox.put(i)

my_cast.add(add_actor_count)

for i in xrange(3,6):
    my_cast.inbox.put(i)

my_cast.cut()

# Output
# ------
# I am an actor from the original cast! I got message #0
# I am an actor from the original cast! I got message #1
# I am an actor from the original cast! I got message #2
# I am an actor created later! I got message #3
# I am an actor created later! I got message #5
# I am an actor created later! I got message #4
# End scene.
