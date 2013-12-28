from agent import Agent
from fife import fife
from fife.fife import Location
import random, math

# Define constants
_STATE_NONE, _STATE_CLOSED, _STATE_OPENED, _STATE_EXPLODED = xrange(4)

class Dynamite(Agent):
    
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True):
        super(Dynamite, self).__init__(settings, model, agentName, layer, soundmanager, uniqInMap)
        self.state = _STATE_CLOSED
        self.boy = self.layer.getInstance('PC')
        self.explosionSound = self.soundmanager.createSoundEmitter('sounds/boom.ogg')

    def onInstanceActionFinished(self, instance, action):
        super(Dynamite, self).onInstanceActionFinished(instance, action)
        if self.state == _STATE_OPENED:
            self.agent.actOnce('opened')
        elif self.state == _STATE_EXPLODED:
            self.agent.actOnce('exploded')

    def onInstanceActionCancelled(self, instance, action):
        pass

    def start(self):
        pass
    
    def isClosed(self):
        return self.state == _STATE_CLOSED

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name =="open":
            if self.state == _STATE_CLOSED:
                self.agent.actOnce('open')
                self.state = _STATE_OPENED
        elif name =="kick":
            if self.state == _STATE_OPENED:
                self.agent.actOnce('explode')
                self.explosionSound.play()
                self.state = _STATE_EXPLODED
        else:
            super(Dynamite, self).doReaction(name, actionAgent, reactionInstance)
