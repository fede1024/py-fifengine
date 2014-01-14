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

class Priest(Agent):
    
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True, world = None, looseCallback=None, updateLifeCallback=None):
        super(Priest, self).__init__(settings, model, agentName, layer, soundmanager, uniqInMap)
        self.kickSound = self.soundmanager.createSoundEmitter('sounds/kick.ogg')
        self.world = world
        self.reaction = None
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

        super(Priest, self).onInstanceActionFinished(instance, action)

    def onInstanceActionCancelled(self, instance, action):
        pass
    
    # Execute before default doAction of Agent
    def doAction(self, name, reactionInstance, reactionAgent, callback, location=None):
        super(Priest, self).doAction(name, reactionInstance, reactionAgent, callback)

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            priestTexts = TDS.get("rio", "priestTexts")
            reactionInstance.say(priestTexts[self.textCount], 3000)
            self.textCount = (self.textCount+1)%len(priestTexts)
            self.walk(actionAgent.agent.getLocationRef())
            self.reaction = "talk"
        elif name=="kick":
            self.walk(actionAgent.agent.getLocationRef())
            reactionInstance.say("AOH!!!", 3000)
            self.reaction = "attack"
        else:
            super(Priest, self).doReaction(name, actionAgent, reactionInstance)
            
    def walk(self, location):
        self.state = _STATE_WALK
        self.agent.move('walk', location, 6 * self.settings.get("rio", "TestAgentSpeed"))

    def start(self):
        self.idle()

    def idle(self):
        self.state = _STATE_IDLE
        self.agent.actOnce('stand')
