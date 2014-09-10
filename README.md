caine
=====

supporting actors process queues concurrently

### Install

<pre><code>pip install caine</code></pre>

### Usage

<pre><code>from caine import SupportingActor

# Print the name attribute of the instance and the message
def deliver(message, instance_attributes):
    print '%s says, "%s"' %(instance_attributes['name'], message)

# Print end scene
def end_scene(instance_attributes):
    print "End scene."

# Create my_actor which executes deliver using messages in its inbox 
# and executes end_scene on successful completion
my_actor = SupportingActor(receive = deliver, callback = end_scene, name = 'Michael')

# Begin receiving messages
my_actor()

# Put messages in inbox of my_actor.
my_actor.inbox.put("You were only supposed to blow the bloody doors off!")
my_actor.inbox.put("She was only sixteen years old!")
my_actor.inbox.put("Not many people know that!")

# Tell my_actor that it is complete when its inbox is empty.
my_actor.cut()</code></pre>

<pre><code># Output
# ------
# Michael says, "You were only supposed to blow the bloody doors off!"
# Michael says, "She was only sixteen years old!"
# Michael says, "Not many people know that!"
# End scene.</code></pre>

### More Horsepower

<pre><code>from caine import SupportingCast
import time
import random

# SupportingCast will have 3 actors
num_actors = 3 

# Wait a random number of seconds, then print stuff
def wait_rand_deliver(message, actor_attributes):
    wait_secs = random.randint(1,5)
    time.sleep(wait_secs)
    print 'Actor #%s waited %s seconds to say, "%s"' %(actor_attributes['actor_id'], wait_secs, message)

# Create my_cast with 3 actors
my_cast = SupportingCast(receive = wait_rand_deliver, callback = end_scene, num = num_actors)

my_cast()

for i in xrange(10):
    my_cast.inbox.put("I got message #%s." %(i))

my_cast.cut()</code></pre>

<pre><code># Output
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
# End scene.</code></pre>

### Collecting Messages

<pre><code>from caine import Collector

# A function which synthesizes a new message and prior messages
def print_even_collect_odd(new_number, collected_odds, instance_attributes):
    
    # Initially there are no prior messages so set collected_odds to be an empty list if collected_odds is None
    if collected_odds is None:
        collected_odds = []
    
    # Print even numbers
    if new_number % 2 == 0: 
        print "I got the even number: %s" %(new_number)
    
    # Append odd numbers to collected_odds
    else: 
        collected_odds.append(new_number)
    
    # Return collected_odds
    return collected_odds

# A function called on completion
def print_collected(instance_attributes):
    print "I collected these odd numbers: %s" %(instance_attributes['collected'])

# Create my_collector which collects messages using print_even_collect_odd
# and executes print_collected on successful completion
my_collector = Collector(collect = print_even_collect_odd, callback = print_collected)

my_collector()

for i in xrange(10):
    my_collector.inbox.put(i)

my_collector.cut()</code></pre>

<pre><code># Output
# ------
# I got the even number: 0
# I got the even number: 2
# I got the even number: 4
# I got the even number: 6
# I got the even number: 8
# I collected these odd numbers: [1, 3, 5, 7, 9]</code></pre>

### Other Functions

##### Immediate Cut

<pre><code># maximum number of seconds an actor will wait before delivering a message
max_wait = 5

def wait_rand_deliver(message, actor_attributes):
    wait_secs = random.randint(1,max_wait)
    time.sleep(wait_secs)
    print 'Actor #%s waited %s seconds to say, "%s"' %(actor_attributes['actor_id'], wait_secs, message)

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
    my_cast.inbox.put("I did not get this message in time to say it!")</code></pre>

<pre><code># Output
# ------
# Actor #2 waited 2 seconds to say, "I got this message in time to say it!"
# Actor #0 waited 4 seconds to say, "I got this message in time to say it!"
# Actor #1 waited 4 seconds to say, "I got this message in time to say it!"</code></pre>

##### Adding Actors to Cast

<pre><code># The cast starts with 2 actors
original_actor_count = 2 

# The cast will have 3 actors added to it
add_actor_count = 3      

def wait1_deliver(message_num, actor_attributes):
    time.sleep(1)
    if actor_attributes['actor_id'] &lt; original_actor_count:
        print 'I am an actor from the original cast! I got message #%s' %(message_num)
    else:
        print 'I am an actor created later! I got message #%s' %(message_num)

# Create my_cast with 2 actors
my_cast = SupportingCast(receive = wait1_deliver, callback = end_scene, num = original_actor_count)

my_cast()

for i in xrange(original_actor_count):
    my_cast.inbox.put(i)

# Add 3 actors to my_cast
my_cast.add(add_actor_count)

for i in xrange(original_actor_count, original_actor_count + add_actor_count):
    my_cast.inbox.put(i)

my_cast.cut()</code></pre>

<pre><code># Output
# ------
# I am an actor from the original cast! I got message #0
# I am an actor from the original cast! I got message #1
# I am an actor created later! I got message #2
# I am an actor created later! I got message #3
# I am an actor created later! I got message #4
# End scene.</code></pre>
