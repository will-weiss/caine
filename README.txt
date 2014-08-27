caine
=====

supporting actors offer concurrent inbox processing

Install
~~~~~~~

pip install caine

Usage
~~~~~

from caine import SupportingActor

def print_square(message, instance_attributes):
   print "%s says %s squared is: %s" %(instance_attributes['name'] , message, message**2)

square_printing_actor = SupportingActor(receive = print_square, timeout = 5, name = 'Bob')

# Call an instance of SupportingActor to commence receiving messages
square_printing_actor()

for i in xrange(1,11):
   square_printing_actor.inbox.put(i)

# Output
# ------
# Bob says 1 squared is: 1
# Bob says 2 squared is: 4
# Bob says 3 squared is: 9
# Bob says 4 squared is: 16
# Bob says 5 squared is: 25
# Bob says 6 squared is: 36
# Bob says 7 squared is: 49
# Bob says 8 squared is: 64
# Bob says 9 squared is: 81
# Bob says 10 squared is: 100
# Inbox processing done.

More Horsepower
~~~~~~~~~~~~~~~

from caine import SupportingCast
import time

def print_square(message, actor_attributes):
   import random
   time.sleep(random.randint(2,4))
   print "Actor #%s says %s squared is: %s" %(actor_attributes['actor_id'], message, message**2)

square_printing_cast = SupportingCast(receive = print_square, timeout = 5, num = 3)

# Call an instance of SupportingCast to commence receiving messages with each of its actors
square_printing_cast() 

for i in xrange(1,11):
   square_printing_cast.inbox.put(i)

# Output
# ------
# Actor #2 says 3 squared is: 9
# Actor #0 says 2 squared is: 4
# Actor #1 says 1 squared is: 1
# Actor #1 says 6 squared is: 36
# Actor #2 says 4 squared is: 16
# Actor #0 says 5 squared is: 25
# Actor #1 says 7 squared is: 49
# Actor #2 says 8 squared is: 64
# Actor #1 says 10 squared is: 100
# Actor #0 says 9 squared is: 81
# Inbox processing done.

Other Functions
~~~~~~~~~~~~~~~

square_printing_cast() 

for i in xrange(11,21):
   square_printing_cast.inbox.put(i)

square_printing_cast.cut() # Items put in inbox after this will not be processed

# These items will not be processed and will remain in the inbox
for i in xrange(21,31):
   square_printing_cast.inbox.put(i)

# Output
# ------
# Actor #1 says 11 squared is: 121
# Actor #0 says 12 squared is: 144
# Actor #2 says 13 squared is: 169
# Actor #1 says 14 squared is: 196
# Actor #0 says 15 squared is: 225
# Actor #2 says 16 squared is: 256
# Actor #1 says 17 squared is: 289
# Actor #0 says 18 squared is: 324
# Actor #2 says 19 squared is: 361
# Actor #1 says 20 squared is: 400
# Inbox processing done.