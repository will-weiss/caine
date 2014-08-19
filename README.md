waltz
=====

supporting actors offer concurrent inbox processing

### Install

<pre><code>pip install git+git://github.com/will-weiss/waltz.git</code></pre>

### Usage

<pre><code>from waltz import SupportingActor

def print_square(message, **instance_kwargs):
    print "%s says %s squared is: %s" %(instance_kwargs['name'] , message, message**2)

square_printing_actor = SupportingActor(receive = print_square, timeout = 5, name = 'Bob')

# Call an instance of SupportingActor to commence receiving messages
square_printing_actor()

for i in xrange(1,11):
    square_printing_actor.inbox.put(i)

### Output
Bob says 1 squared is: 1
Bob says 2 squared is: 4
Bob says 3 squared is: 9
Bob says 4 squared is: 16
Bob says 5 squared is: 25
Bob says 6 squared is: 36
Bob says 7 squared is: 49
Bob says 8 squared is: 64
Bob says 9 squared is: 81
Bob says 10 squared is: 100
No more messages in inbox.</code></pre>

### More Horsepower

<pre><code>from waltz import SupportingCast
import time

def print_square(message, **actor_kwargs):
    import random
    time.sleep(random.randint(2,4))
    print "Actor #%s says %s squared is: %s" %(actor_kwargs['actor_id'], message, message**2)

square_printing_cast = SupportingCast(receive = print_square, timeout = 5, num = 3)

# Call an instance of SupportingCast to commence receiving messages with each of its actors
square_printing_cast() 

for i in xrange(1,11):
    square_printing_cast.inbox.put(i)

### Output
Actor #2 says 3 squared is: 9
Actor #0 says 2 squared is: 4
Actor #1 says 1 squared is: 1
Actor #1 says 6 squared is: 36
Actor #2 says 4 squared is: 16
Actor #0 says 5 squared is: 25
Actor #1 says 7 squared is: 49
Actor #2 says 8 squared is: 64
Actor #1 says 10 squared is: 100
Actor #0 says 9 squared is: 81
No more messages in inbox.</code></pre>
