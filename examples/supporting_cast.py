### Example of a SupportingCast

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