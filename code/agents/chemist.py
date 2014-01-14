# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2013 by the FIFE team
#  http://www.fifengine.net
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

from agent import Agent
import random
from fife.extensions.fife_settings import Setting

TDS = Setting(app_name="rio_de_hola")
_STATE_NONE, _STATE_IDLE, _STATE_WALK = xrange(3)

class Chemist(Agent):
    
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True, world = None, winCallback=None, updateLifeCallback=None):
        super(Chemist, self).__init__(settings, model, agentName, layer, soundmanager, uniqInMap)
        self.kickSound = self.soundmanager.createSoundEmitter('sounds/kick.ogg')
        self.world = world
        self.reaction = None
        self.winCallback = winCallback
        self.textCount = 0

    def onInstanceActionFinished(self, instance, action):
        #print "Action finished: " + str(action.getId())
        if self.state == _STATE_WALK:
            if self.reaction:
                self.agent.actOnce(self.reaction)
                if self.reaction == "attack":
                    self.kickSound.play()
                self.reaction = None
            self.state = _STATE_IDLE
        else:
            self.idle()

        super(Chemist, self).onInstanceActionFinished(instance, action)

    def onInstanceActionCancelled(self, instance, action):
        pass
    
    # Execute before default doAction of Agent
    def doAction(self, name, reactionInstance, reactionAgent, callback, location=None):
        super(Chemist, self).doAction(name, reactionInstance, reactionAgent, callback)

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            texts = TDS.get("rio", "chemistTexts")
            reactionInstance.say(texts[self.textCount], 3000)
            self.textCount = (self.textCount+1)%len(texts)
            self.walk(actionAgent.agent.getLocationRef())
            self.reaction = "talk"
        else:
            super(Chemist, self).doReaction(name, actionAgent, reactionInstance)
            
    def walk(self, location):
        self.state = _STATE_WALK
        self.agent.move('walk', location, 6 * self.settings.get("rio", "TestAgentSpeed"))

    def start(self):
        self.idle()

    def idle(self):
        self.state = _STATE_IDLE
        self.agent.actOnce('stand')

    def update(self, agentPosition):            
        chemistInstance = self.agent
        chemist = chemistInstance.getLocation()
        agentDistance = chemist.getLayerDistanceTo(agentPosition)
        if agentDistance > 2.5:
            return
        flask = self.layer.getInstance('flask0').getLocation()
        coins = 0
        for i in xrange(3):
            coin = self.layer.getInstance('coins'+str(i)).getLocation()
            d = chemist.getLayerDistanceTo(coin)
            if d < 2.5:
                coins = coins+1
        fd = chemist.getLayerDistanceTo(flask)
        if fd < 2.5:
            if coins < 3:
                chemistInstance.say("Thanks! Bring more coins.", 3000)
                self.winCallback() # TODO remove
            else:
                self.winCallback()
        else:
            if coins < 3:
                chemistInstance.say("Thanks! Bring more coins and the honey.", 3000)
            else:
                chemistInstance.say("Thanks! Bring me the honey.", 3000)
