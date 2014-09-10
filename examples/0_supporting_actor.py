### Example of a SupportingActor

from caine import SupportingActor

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
my_actor.cut()

# Output
# ------
# Michael says, "You were only supposed to blow the bloody doors off!"
# Michael says, "She was only sixteen years old!"
# Michael says, "Not many people know that!"
# End scene.