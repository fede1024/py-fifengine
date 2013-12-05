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
from fife.extensions.fife_settings import Setting
import random

TDS = Setting(app_name="rio_de_hola")

_STATE_NONE, _STATE_TALK = 0, 1

class Beekeeper(Agent):
    def onInstanceActionFinished(self, instance, action):
        self.talk()

    def onInstanceActionCancelled(self, instance, action):
        pass

    def start(self):
        self.facingLoc = self.agent.getLocation()
        c = self.facingLoc.getExactLayerCoordinatesRef()
        c.x += random.randint(-1, 1)
        c.y += random.randint(-1, 1)
        self.talk()

    def talk(self):
        self.state = _STATE_TALK
        self.agent.actRepeat('talk', self.facingLoc) # never calls back

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            texts = TDS.get("rio", "beekeeperTexts")
            reactionInstance.say(random.choice(texts), 5000)
            #self.agent.move('run', actionAgent.agent.getLocationRef(), 4 * self.settings.get("rio", "TestAgentSpeed"))  # Beekeper cannot run
        else:
            super(Beekeeper, self).doReaction(name, actionAgent, reactionInstance)
