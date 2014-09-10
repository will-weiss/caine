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

# Put messages in inbox of my_actor.
my_actor.inbox.put("You were only supposed to blow the bloody doors off!")
my_actor.inbox.put("She was only sixteen years old!")
my_actor.inbox.put("Not many people know that!")

# Call my_actor to commence inbox processing.
my_actor()

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

def wait_deliver(message, actor_attributes):
    wait_secs = random.randint(1,5)
    time.sleep(wait_secs)
    print 'Actor #%s waited %s seconds to say, "%s"' %(actor_attributes['actor_id'], wait_secs, message)

my_cast = SupportingCast(receive = wait_deliver, callback = end_scene, num = 3)

for i in xrange(1,11):
    my_cast.inbox.put("I got message #%s." %(i))

my_cast()
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

Other Functions
~~~~~~~~~~~~~~~

for i in xrange(3):
    my_cast.inbox.put("I got this message in time to say it!")

my_cast()
time.sleep(6)

# Items put in inbox after this will not be processed
my_cast.cut(immediate = True)

for i in xrange(3):
    my_cast.inbox.put("I did not get this message in time to say it!")

# Output
# ------
# Actor #2 waited 2 seconds to say, "I got this message in time to say it!"
# Actor #0 waited 4 seconds to say, "I got this message in time to say it!"
# Actor #1 waited 4 seconds to say, "I got this message in time to say it!"