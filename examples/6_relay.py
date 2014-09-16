### Example of setting up a relay of actors

from caine import SupportingActor, Collector, Cut
import time

def square_then_relay(num, instance_attributes):
    num_sq = num**2
    print "I got %s and am relaying its square, %s." %(num, num_sq)
    instance_attributes['outbox'].put(num_sq)
    time.sleep(.2)

def add_three_then_relay(num, instance_attributes):
    num_plus_three = num + 3
    print "I got %s and am relaying that number plus three, %s." %(num, num_plus_three)
    instance_attributes['outbox'].put(num_plus_three)

def append_all(num, num_list, instance_attributes):
    print "I got %s and am appending it to my list." %(num)
    return num_list + [num] if num_list is not None else [num]

# Used as callback to signal to next actor in relay that it is done
def relay_cut(instance_attributes):
    instance_attributes['outbox'].put(Cut)

def print_collected(instance_attributes):
    print "I collected these numbers: %s" %(instance_attributes['collected'])

my_collector = Collector(collect = append_all, callback = print_collected)

# The inbox of my_collector is the outbox attribute of three_adder
three_adder = SupportingActor(receive = add_three_then_relay, callback = relay_cut, outbox = my_collector.inbox)

# The inbox of three_adder is the outbox attribute of number_squarer
number_squarer = SupportingActor(receive = square_then_relay, callback = relay_cut, outbox = three_adder.inbox)

my_collector()
three_adder()
number_squarer()

for i in xrange(10):
    number_squarer.inbox.put(i)

number_squarer.cut()

# Output
# ------
# I got 0 and am relaying its square, 0.
# I got 0 and am relaying that number plus three, 3.
# I got 3 and am appending it to my list.
# I got 1 and am relaying its square, 1.
# I got 1 and am relaying that number plus three, 4.
# I got 4 and am appending it to my list.
# I got 2 and am relaying its square, 4.
# I got 4 and am relaying that number plus three, 7.
# I got 7 and am appending it to my list.
# I got 3 and am relaying its square, 9.
# I got 9 and am relaying that number plus three, 12.
# I got 12 and am appending it to my list.
# I got 4 and am relaying its square, 16.
# I got 16 and am relaying that number plus three, 19.
# I got 19 and am appending it to my list.
# I got 5 and am relaying its square, 25.
# I got 25 and am relaying that number plus three, 28.
# I got 28 and am appending it to my list.
# I got 6 and am relaying its square, 36.
# I got 36 and am relaying that number plus three, 39.
# I got 39 and am appending it to my list.
# I got 7 and am relaying its square, 49.
# I got 49 and am relaying that number plus three, 52.
# I got 52 and am appending it to my list.
# I got 8 and am relaying its square, 64.
# I got 64 and am relaying that number plus three, 67.
# I got 67 and am appending it to my list.
# I got 9 and am relaying its square, 81.
# I got 81 and am relaying that number plus three, 84.
# I got 84 and am appending it to my list.
# I collected these numbers: [3, 4, 7, 12, 19, 28, 39, 52, 67, 84]