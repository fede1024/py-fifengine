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
_STATE_KICK = xrange(5)

class Boy(HumanAgent):
    def onInstanceActionFinished(self, instance, action):
        #print "Action finished: " + str(action.getId())
        self.idle()
        if action.getId() != 'stand':
            self.idlecounter = 1
        else:
            self.idlecounter += 1
        if self.idlecounter % 7 == 0:
            heroTexts = self.settings.get("rio", "boyIdleTexts")
            txtindex = random.randint(0, len(heroTexts) - 1)
            instance.say(heroTexts[txtindex], 2500)

    def kick(self, target):
        self.state = _STATE_KICK
        self.agent.actOnce('kick', target)

    # Execute before default doAction of Agent
    def doAction(self, name, reactionInstance, reactionAgent):
        if name=="kick":
            self.kick(reactionInstance.getLocationRef())
        else:
            super(Boy, self).doAction(name, reactionInstance, reactionAgent)

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            texts = TDS.get("rio", "boyTexts")
            reactionInstance.say(random.choice(texts), 5000)
        else:
            super(Boy, self).doReaction(name, actionAgent, reactionInstance)
