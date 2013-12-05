from agent import Agent
from fife import fife
from fife.fife import Location
import random, math

# Define constants
_STATE_NONE, _STATE_IDLE, _STATE_FLY, _STATE_FOLLOW = xrange(4)

class Bee(Agent):
    
    def __init__(self, settings, model, agentName, layer, uniqInMap=True):
        super(Bee, self).__init__(settings, model, agentName, layer, uniqInMap)
        self.state = _STATE_IDLE
        self.angry = False
        self.idlecounter = 1
        location = self.agent.getLocationRef()
        self.initial_coords = location.getMapCoordinates()
        self.boy = self.layer.getInstance('PC')

    def onInstanceActionFinished(self, instance, action):
        if action.getId() == 'angry_fly' and self.state == _STATE_FOLLOW:
            self.agent.say("You are dead!", 3500)

        if self.angry == True:
            self.idlecounter = 1
            self.followBoy()
        else:
            if self.idlecounter % 3 == 0:
                self.randomMove()
                self.idlecounter = 1
            else:
                self.idle()

        if action.getId() not in ('stand', 'angry_stand'):
            self.idlecounter = 1
        else:
            self.idlecounter += 1

        super(Bee, self).onInstanceActionFinished(instance, action)

    def onInstanceActionCancelled(self, instance, action):
        pass

    def start(self):
        self.idle()

    def idle(self):
        self.state = _STATE_IDLE
        if(self.angry):
            self.agent.actOnce('angry_stand')
        else:
            self.agent.actOnce('stand')

    def fly(self, location):
        self.state = _STATE_FLY
        if(self.angry):
            self.agent.move('angry_fly', location, 3 * self.settings.get("rio", "TestAgentSpeed"))
        else:
            self.agent.move('fly', location, 3 * self.settings.get("rio", "TestAgentSpeed"))

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            reactionInstance.say("BZZZZZZZ", 5000)
            self.fly(actionAgent.agent.getLocationRef())
        elif name=="kick":
            location = self.agent.getLocationRef()
            my_coords = location.getMapCoordinates()
            his_coords = actionAgent.agent.getLocationRef().getMapCoordinates()
            dx = my_coords.x - his_coords.x
            dy = my_coords.y - his_coords.y
            dist = math.sqrt(dx*dx + dy*dy)
            if (dist < 1.5):
                self.agent.say("BZZ!!!", 3500)
                nl = Location(location)
                my_coords.x += dx
                my_coords.y += dy
                nl.setMapCoordinates(my_coords)
                self.angry = True
                self.fly(nl)
            else:
                self.agent.say("You missed me :P", 3500)
        else:
            super(Bee, self).doReaction(name, actionAgent, reactionInstance)

    def randomMove(self):
        location = self.agent.getLocationRef()
        coords = location.getMapCoordinates()
        dx = coords.x - self.initial_coords.x
        dy = coords.y - self.initial_coords.y
        dist = math.sqrt(dx*dx + dy*dy)
        if (dist < 4):
            coords.x += random.uniform(-2, 2)
            coords.y += random.uniform(-2, 2)
        else:
            coords.x -= (dx/dist) * random.uniform(0, 2)
            coords.y -= (dy/dist) * random.uniform(0, 2)
        nl = Location(location)
        nl.setMapCoordinates(coords)
        self.fly(nl)
        
    def followBoy(self):
        self.state = _STATE_FOLLOW
        self.agent.follow('angry_fly', self.boy, 3 * self.settings.get("rio", "TestAgentSpeed"))
