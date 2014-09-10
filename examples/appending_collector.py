# Example of caine.Collector

from caine import Collector

# A function which synthesizes a new message and prior messages
def print_even_collect_odd(new_number, collected_odds, instance_attributes):
    collected_odds = collected_odds if collected_odds is not None else []
    if new_number % 2 == 0: 
        print "I got the even number: %s" %(new_number)
    else: 
        collected_odds.append(new_number)
    return collected_odds

# A function called on completion
def print_collected(instance_attributes):
    print "I collected these odd numbers: %s" %(instance_attributes['collected'])

my_collector = Collector(collect = print_even_collect_odd, callback = print_collected)
my_collector()

for i in xrange(10):
    my_collector.inbox.put(i)

my_collector.cut()

# Output
# ------
# I got the even number: 0
# I got the even number: 2
# I got the even number: 4
# I got the even number: 6
# I got the even number: 8
# I collected these odd numbers: [1, 3, 5, 7, 9]