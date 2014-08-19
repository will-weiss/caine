waltz
=====

supporting actors offer concurrent inbox processing

### Install

<pre><code>pip install git+git://github.com/will-weiss/waltz.git</code></pre>

### Usage

<pre><code>from waltz import SupportingActor

def print_square(message):
    print "%s squared is: %s" %(message, message**2)

square_printing_actor = SupportingActor(receive = print_square, timeout = 5)

square_printing_actor() # Call an instance of SupportingActor to commence receiving messages

for i in xrange(1,11):
    square_printing_actor.inbox.put(i)

### Output
1 squared is: 1
2 squared is: 4
3 squared is: 9
4 squared is: 16
5 squared is: 25
6 squared is: 36
7 squared is: 49
8 squared is: 64
9 squared is: 81
10 squared is: 100
No more messages in inbox.</code></pre>

### More Horsepower

<pre><code>from waltz import SupportingCast

def print_square(message):
    import random
    time.sleep(random.randint(0,4))
    print "%s squared is: %s" %(message, message**2)

square_printing_cast = SupportingCast(receive = print_square, num = 3, timeout = 5)

square_printing_cast() # Call an instance of SupportingCast to have its actors commence receiving messages

for i in xrange(1,11):
    square_printing_cast.inbox.put(i)

### Output
2 squared is: 4
1 squared is: 1
7 squared is: 49
8 squared is: 64
10 squared is: 100
3 squared is: 9
4 squared is: 16
5 squared is: 25
6 squared is: 36
9 squared is: 81
No more messages in inbox.</code></pre>