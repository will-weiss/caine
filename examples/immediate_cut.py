### Example of a SupportingCast

from caine import SupportingCast
import time
import random

def wait_deliver(message, actor_attributes):
    wait_secs = random.randint(1,5)
    time.sleep(wait_secs)
    print 'Actor #%s waited %s seconds to say, "%s"' %(actor_attributes['actor_id'], wait_secs, message)

def end_scene(instance_attributes):
    print "End scene."

my_cast = SupportingCast(receive = wait_deliver, callback = end_scene, num = 3)

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