from waltz import Collector

def append_all(new_message, collected_messages, **collector_attributes):
  collected_messages = collected_messages if collected_messages is not None else []
  collected_messages.append(new_message)
  return collected_messages

c = Collector(collect = append_all)
c()

for i in xrange(11):
  c.inbox.put(i)

c.cut()

while c.process.is_alive():
  pass

collected_messages = c.collected_outbox.get()
print collected_messages

# Output
# ------
# No more messages in inbox.
# [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
