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
from code.utils import makeDisappear, moveObject
import random

TDS = Setting(app_name="rio_de_hola")

# Define constants
_STATE_KICK, _STATE_RUN = xrange(2)

class Boy(HumanAgent):
    
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True, world = None):
        super(Boy, self).__init__(settings, model, agentName, layer, soundmanager, uniqInMap)
        self.kickSound = self.soundmanager.createSoundEmitter('sounds/kick.ogg')
        self.bottle = False
        self.lay = False
        self.world = world
        self.speed = 6

    def onInstanceActionFinished(self, instance, action):
        #print "Action finished: " + str(action.getId())
        if self.lay:
            location = self.agent.getLocation()
            coords = location.getMapCoordinates()
            moveObject(self.bottle, coords.x, coords.y)
            self.bottle = None
            #self.world.hideItems([0])
            self.moveStep('u')
            self.lay = False
            return
        
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
        if self.bottle:
            self.agent.actOnce('kick_bottle', target)
        else:
            self.agent.actOnce('kick', target)
        self.kickSound.play()

    def getActionsList(self, target_instance, target_agent, distance):
        actions = []
        if self.bottle and not target_instance:
            actions.append('lay')
        if target_instance and distance < 1.5:
            if target_instance.getObject().getId() == "flask_map":
                actions.append('pick');
            if target_agent:  # If the target is an agent
                actions.append('kick');
        inherited_actions = super(Boy, self).getActionsList(target_instance, target_agent, distance)
        return inherited_actions + actions

    # Execute before default doAction of Agent
    def doAction(self, name, reactionInstance, reactionAgent, callback, location=None):
        if name == "kick":
            self.kick(reactionInstance.getLocation())
            self.callbacks.append(callback)
        elif name == "pick":
            self.bottle = reactionInstance
            #self.world.showItems([0])
            self.run(self.bottle.getLocation())
            makeDisappear(self.bottle)
            self.idle()
        elif name == "lay":
            self.run(location)
            self.lay = True
        else:
            super(Boy, self).doAction(name, reactionInstance, reactionAgent, callback)

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            texts = TDS.get("rio", "boyTexts")
            reactionInstance.say(random.choice(texts), 5000)
            self.run(actionAgent.agent.getLocation())
        else:
            super(Boy, self).doReaction(name, actionAgent, reactionInstance)