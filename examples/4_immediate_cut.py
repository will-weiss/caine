### Example of cutting a process immediately

from caine import SupportingCast
import time
import random

# maximum number of seconds an actor will wait before delivering a message
max_wait = 5

def wait_rand_deliver(message, actor_attributes):
    wait_secs = random.randint(1,max_wait)
    time.sleep(wait_secs)
    print 'Actor #%s waited %s seconds to say, "%s"' %(actor_attributes['actor_id'], wait_secs, message)

def end_scene(instance_attributes):
    print "End scene."

my_cast = SupportingCast(receive = wait_rand_deliver, callback = end_scene, num = 3)

for i in xrange(3):
    my_cast.inbox.put("I got this message in time to say it!")

my_cast()

# Wait longer than maximum time an actor will take a process a message
time.sleep(max_wait + 1)

# Inbox processing is cut immediately
my_cast.cut(immediate = True)

# These messages will not be processed
for i in xrange(3):
    my_cast.inbox.put("I did not get this message in time to say it!")

# Output
# ------
# Actor #2 waited 2 seconds to say, "I got this message in time to say it!"
# Actor #0 waited 4 seconds to say, "I got this message in time to say it!"
# Actor #1 waited 4 seconds to say, "I got this message in time to say it!"
