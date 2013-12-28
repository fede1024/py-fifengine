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
from fife import fife
from fife.fife import Location

# Define constants
_STATE_NONE, _STATE_IDLE, _STATE_RUN, _STATE_KICK, _STATE_TALK = xrange(5)

class HumanAgent(Agent):
    """ This class specify a general agent that can be controlled by the user """
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True):
        super(HumanAgent, self).__init__(settings, model, agentName, layer, soundmanager, uniqInMap)
        self.state = _STATE_NONE
        self.idlecounter = 1
        self.bottle = False
        self.footSound = self.soundmanager.createSoundEmitter('sounds/footstep.ogg')
        self.footSound.looping = True

    def onInstanceActionFinished(self, instance, action):
        self.idle()
#         print "Human action finished", instance.getObject().getId()
        super(HumanAgent, self).onInstanceActionFinished(instance, action)

    def onInstanceActionCancelled(self, instance, action):
        pass

    def start(self):
        self.idle()

    def idle(self):
        self.state = _STATE_IDLE
        if self.bottle:
            self.agent.actOnce('stand_bottle')
        else:
            self.agent.actOnce('stand')
        self.footSound.stop()

    def run(self, location):
        if self.state != _STATE_RUN:
            self.footSound.play()
        self.state = _STATE_RUN
        if self.bottle:
            self.agent.move('run_bottle', location, 4 * self.settings.get("rio", "TestAgentSpeed"))
        else:
            self.agent.move('run', location, 4 * self.settings.get("rio", "TestAgentSpeed"))

    def talk(self, target):
        self.state = _STATE_TALK
        self.idlecounter = 1
        self.agent.actOnce('talk', target)

    def keyPressed(self, keyval):
        if keyval in (fife.Key.LEFT, fife.Key.RIGHT, fife.Key.UP, fife.Key.DOWN):
            self.moveStep({fife.Key.LEFT:'l', fife.Key.RIGHT:'r', fife.Key.UP:'u', fife.Key.DOWN:'d'}[keyval])

    def moveStep(self, direction):
        location = self.agent.getLocationRef()
        coords = location.getMapCoordinates()
        rot = self.agent.getRotation()

        if direction == 'l':
            rot = (rot+45)%360
            self.idle()
            self.agent.setRotation(rot)
        elif direction == 'r':
            rot = (rot-45)%360
            self.idle()
            self.agent.setRotation(rot)
        elif direction == 'd':
            rot = (rot+180)%360
            self.idle()
            self.agent.setRotation(rot)
        elif direction == 'u':
            if(0 <= rot < 23 or rot >= 338):
                coords.x += +0.5
            elif (23 <= rot < 68):
                coords.x += +0.5
                coords.y += -0.5
            elif (68 <= rot < 113):
                coords.y += -0.5
            elif (113 <= rot < 158):
                coords.x += -0.5
                coords.y += -0.5
            elif (158 <= rot < 203):
                coords.x += -0.5
            elif (203 <= rot < 248):
                coords.x += -0.5
                coords.y += +0.5
            elif (248 <= rot < 293):
                coords.y += +0.5
            elif (293 <= rot < 338):
                coords.x += +0.5
                coords.y += +0.5
            nl = Location(location)
            nl.setMapCoordinates(coords)
            self.run(nl)
            
    def getActionsList(self, target_instance, target_agent, distance):
        actions = ['inspect']
        if distance > 1.5:
            actions.append('move')
        else:
            if target_agent:  # If the target is an agent
                if target_agent.agent.getObject().getId() != "dynamites_lid":
                    actions.append('talk');
                elif target_agent.isClosed():
                    actions.append('open');
        inherited_actions = super(HumanAgent, self).getActionsList(target_instance, target_agent, distance)
        return inherited_actions + actions

    # Execute before default doAction of Agent
    def doAction(self, name, reactionInstance, reactionAgent, callback):
        self.callback = callback
        if name=="inspect":
            saytext = []
            saytext.append('%s' % reactionInstance.getObject().getId())
            self.agent.say('\n'.join(saytext), 3500)
        elif name in ("move", "talk", "open"):
            self.run(reactionInstance.getLocationRef())
        else:
            super(HumanAgent, self).doAction(name, reactionInstance, reactionAgent, callback)
