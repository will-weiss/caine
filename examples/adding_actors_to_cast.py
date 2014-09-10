### Example of adding actors to an already running SupportingCast

from caine import SupportingCast
import time

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
