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
import random
from fife.extensions.fife_settings import Setting
from fife.fife import Location

TDS = Setting(app_name="rio_de_hola")

class Girl(HumanAgent):

    # Execute before default doAction of Agent
    def doAction(self, name, reactionInstance, reactionAgent, callback):
        self.callback = callback
        if name=="inspect":
            saytext = []
            saytext.append('%s' % reactionInstance.getObject().getId())
            self.agent.say('\n'.join(saytext), 3500)
        elif name=="move":
            self.run(reactionInstance.getLocationRef())
        else:
            super(Girl, self).doAction(name, reactionInstance, reactionAgent, callback)

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            girlTexts = TDS.get("rio", "girlTexts")
            reactionInstance.say(random.choice(girlTexts), 5000)
            self.run(actionAgent.agent.getLocationRef())
        elif name=="kick":
            self.agent.say("Hey!!!", 3500)
            location = self.agent.getLocationRef()
            my_coords = location.getMapCoordinates()
            his_coords = actionAgent.agent.getLocationRef().getMapCoordinates()
            dx = my_coords.x - his_coords.x
            dy = my_coords.y - his_coords.y
            nl = Location(location)
            my_coords.x += dx
            my_coords.y += dy
            nl.setMapCoordinates(my_coords)
            self.run(nl)
        else:
            super(Girl, self).doReaction(name, actionAgent, reactionInstance)
