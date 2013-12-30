from agent import Agent
from fife.extensions.fife_settings import Setting
from fife.fife import Location
from code.utils import moveObjectRelative
import random, math

TDS = Setting(app_name="rio_de_hola")

# Define constants
_STATE_NONE, _STATE_IDLE, _STATE_FLY, _STATE_FOLLOW, _STATE_DEAD = xrange(5)

class Bee(Agent):
    
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True):
        super(Bee, self).__init__(settings, model, agentName, layer, soundmanager, uniqInMap)
        self.state = _STATE_IDLE
        self.idlecounter = 1
        location = self.agent.getLocation()
        self.initial_coords = location.getMapCoordinates()
        self.followed = None
        #self.boy = self.layer.getInstance('PC')
        self.beeHoneyTexts = TDS.get("rio", "beeHoneyTexts")

    def onInstanceActionFinished(self, instance, action):
        #if action.getId() == 'angry_fly' and self.state == _STATE_FOLLOW:
        #    self.agent.say("You are dead!", 3500)

        if self.state == _STATE_DEAD:
            self.agent.actOnce('dead')
            return
        elif self.followed:
            self.idlecounter = 1
            #self.idle()
            self.follow(self.followed)
        else:
            if self.idlecounter % 3 == 0:
                self.randomMove()
                self.idlecounter = 1
            else:
                self.idle()

        if action.getId() not in ('stand'):
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
        self.agent.actOnce('stand')

    def fly(self, location):
        self.state = _STATE_FLY
        self.idlecounter = 1
        self.agent.move('fly', location, 6 * self.settings.get("rio", "TestAgentSpeed"))

    def fall(self):
        self.state = _STATE_DEAD
        self.agent.actOnce('fall')
        moveObjectRelative(self.agent, z=-0.01)

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if self.isDead():
            pass
        elif name=="talk":
            reactionInstance.say("BZZZZZZZ", 5000)
            self.fly(actionAgent.agent.getLocation())
        elif name=="kick":
            location = self.agent.getLocation()
            my_coords = location.getMapCoordinates()
            his_coords = actionAgent.agent.getLocation().getMapCoordinates()
            dx = my_coords.x - his_coords.x
            dy = my_coords.y - his_coords.y
            dist = math.sqrt(dx*dx + dy*dy)
            if (dist < 1):
                self.agent.say("BZZ!!!", 3500)
                self.soundmanager.createSoundEmitter('sounds/bee.ogg', True, tuple).play()
                nl = Location(location)
                my_coords.x += dx*2
                my_coords.y += dy*2
                nl.setMapCoordinates(my_coords)
                self.fly(nl)
            else:
                self.agent.say("You missed me :P", 3500)
        else:
            super(Bee, self).doReaction(name, actionAgent, reactionInstance)

    def randomMove(self):
        location = self.agent.getLocation()
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
        
    def follow(self, instance):
        if instance:
            target_distance = self.agent.getLocation().getLayerDistanceTo(instance.getLocation())
            if target_distance > 1.5:
                if self.state != _STATE_FOLLOW:
                    self.agent.say(random.choice(self.beeHoneyTexts), 1000)
                self.fly(instance.getLocation())
                self.state = _STATE_FOLLOW
                #self.agent.follow('angry_fly', instance, 3 * self.settings.get("rio", "TestAgentSpeed"))
            else:
                self.idle()

    def isIdle(self):
        return self.state == _STATE_IDLE

    def isDead(self):
        return self.state == _STATE_DEAD