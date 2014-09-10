### Example of using a timeout

from caine import SupportingCast
import time

# The number of seconds to wait for a message before ending processing
timeout = 5 

# Wait a 1 second, then print stuff
def wait1_deliver(message_num, actor_attributes):
    time.sleep(1)
    print 'Actor #%s says, "I got message #%s in time to say it!"' %(actor_attributes['actor_id'], message_num)

def end_scene(instance_attributes):
    print "End scene."

# Create my_cast which will time out after 5 seconds
my_cast = SupportingCast(receive = wait1_deliver, callback = end_scene, num = 3, timeout = timeout)

for i in xrange(3):
    my_cast.inbox.put(i)

my_cast()

# Wait longer than the timeout
time.sleep(timeout + 1) 

# These messages will not be processed
for i in xrange(3,6):
    my_cast.inbox.put(i)

# Output
# ------
# Actor #0 says, "I got message #0 in time to say it!"
# Actor #1 says, "I got message #1 in time to say it!"
# Actor #2 says, "I got message #2 in time to say it!"
# End scene.