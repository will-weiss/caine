### Example of a SupportingActor

from caine import SupportingActor

def deliver(line, instance_attributes):
    print '%s says, "%s"' %(instance_attributes['name'], line)

def end_scene(instance_attributes):
    print "End scene."

# An actor which executes deliver using messages in its inbox and executes end_scene on completion
my_actor = SupportingActor(receive = deliver, callback = end_scene, name = 'Michael')

# Call my_actor to commence inbox processing.
my_actor()

# Put messages in inbox of my_actor.
my_actor.inbox.put("You were only supposed to blow the bloody doors off!")
my_actor.inbox.put("She was only sixteen years old!")
my_actor.inbox.put("Not many people know that!")

# Tell my_actor that it is complete when its inbox is empty.
my_actor.cut()

# Output
# ------
# Michael says, "You were only supposed to blow the bloody doors off!"
# Michael says, "She was only sixteen years old!"
# Michael says, "Not many people know that!"
# End scene.