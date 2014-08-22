from waltz import Collector

def append_all(new_message, prior_messages, instance_attributes):
  print new_message
  prior_messages = prior_messages if prior_messages is not None else []
  prior_messages.append(new_message)
  return prior_messages

c = Collector(collect = append_all)
c()

for i in xrange(11):
  c.inbox.put(i)

c.cut()

while c.process.is_alive():
  pass

print c.collected

# Output
# ------
# Inbox processing done.
# [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
