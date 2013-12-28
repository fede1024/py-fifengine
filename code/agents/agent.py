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

from fife import fife
from code.common.common import ProgrammingError
from fife.extensions.fife_settings import Setting
import random

TDS = Setting(app_name="rio_de_hola")

# uniqInMap => there is a specific action litener for that agent

class Agent(fife.InstanceActionListener):
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True):
        fife.InstanceActionListener.__init__(self)
        self.settings = settings
        self.model = model
        self.agentName = agentName
        self.layer = layer
        self.callbacks = []
        self.soundmanager = soundmanager
        if uniqInMap:
            self.agent = layer.getInstance(agentName)
            self.agent.addActionListener(self)

    def onInstanceActionFinished(self, instance, action):
#         print "Agent action finished", instance.getObject().getId()
        if self.callbacks:
            callback = self.callbacks[0]                          # Call the callback
            if callback:
                callback()
            self.callbacks = self.callbacks[1:]   # Remove it from the list

    def onInstanceActionCancelled(self, instance, action):
        raise ProgrammingError('No OnActionFinished defined for Agent')

    def onInstanceActionFrame(self, instance, action, frame):
        raise ProgrammingError('No OnActionFrame defined for Agent')

    def start(self):
        raise ProgrammingError('No start defined for Agent')

    def getActionsList(self, target_instance, target_agent, distance):
        return []
    
    def doAction(self, name, reactionInstance, reactionAgent, callback):
        self.callbacks.append(callback)
        print "No action '%s' defined for %s to %s (agent %s)."%(name, self.agentName, reactionInstance.getObject().getId(), \
                                                                None if not reactionAgent else reactionAgent.agentName)

    # the "reactionAgent" is yourself of course
    def doReaction(self, name, actionAgent, reactionInstance):
        if name in ("inspect", "move"):
            pass
        else:
            print "No defined reaction for action '%s' for %s to %s."%(name, self.agentName, actionAgent.agentName)

# Not unique in map agents
def create_anonymous_agents(settings, model, objectName, layer, agentClass, soundmanager):
    agents = []
    instances = [a for a in layer.getInstances() if a.getObject().getId() == objectName]
    i = 0
    for a in instances:
        agentName = '%s:i:%d' % (objectName, i)
        i += 1
        agent = agentClass(settings, model, agentName, layer, soundmanager, False)
        agent.agent = a
        a.addActionListener(agent)
        agents.append(agent)
    return agents
