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

from humanAgent import HumanAgent
from fife.extensions.fife_settings import Setting
import random

TDS = Setting(app_name="rio_de_hola")

# Define constants
_STATE_KICK, _STATE_RUN = xrange(2)

class Boy(HumanAgent):
    
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True):
        super(Boy, self).__init__(settings, model, agentName, layer, soundmanager, uniqInMap)
        self.kickSound = self.soundmanager.createSoundEmitter('sounds/kick.ogg')
        self.bottle = True

    def onInstanceActionFinished(self, instance, action):
        #print "Action finished: " + str(action.getId())
        if action.getId() != 'stand':
            self.idlecounter = 1
        else:
            self.idlecounter += 1
        if self.idlecounter % 7 == 0:
            heroTexts = self.settings.get("rio", "boyIdleTexts")
            txtindex = random.randint(0, len(heroTexts) - 1)
            instance.say(heroTexts[txtindex], 2500)
#         print "Boy action finished", instance.getObject().getId()
        super(Boy, self).onInstanceActionFinished(instance, action)

    def kick(self, target):
        self.state = _STATE_KICK
        if self.bottle == True:
            self.agent.actOnce('kick_bottle', target)
        else:
            self.agent.actOnce('kick', target)
        self.kickSound.play()

    def run(self, location, bottle=True):
        if self.state != _STATE_RUN:
            self.footSound.play()
        self.state = _STATE_RUN
        if bottle:
            self.agent.move('run_bottle', location, 4 * self.settings.get("rio", "TestAgentSpeed"))
        else:
            self.agent.move('run', location, 4 * self.settings.get("rio", "TestAgentSpeed"))

    def getActionsList(self, target_instance, target_agent, distance):
        actions = []
        if distance < 1.5:
            if target_agent:  # If the target is an agent
                actions.append('kick');
        inherited_actions = super(Boy, self).getActionsList(target_instance, target_agent, distance)
        return inherited_actions + actions

    # Execute before default doAction of Agent
    def doAction(self, name, reactionInstance, reactionAgent, callback):
        self.callback = callback
        if name=="kick":
            self.kick(reactionInstance.getLocationRef())
        else:
            super(Boy, self).doAction(name, reactionInstance, reactionAgent, callback)

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            texts = TDS.get("rio", "boyTexts")
            reactionInstance.say(random.choice(texts), 5000)
            self.run(actionAgent.agent.getLocationRef())
        else:
            super(Boy, self).doReaction(name, actionAgent, reactionInstance)
