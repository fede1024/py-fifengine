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
from code.utils import makeDisappear, moveObject

TDS = Setting(app_name="rio_de_hola")

class Girl(HumanAgent):
    
    def __init__(self, settings, model, agentName, layer, soundmanager, uniqInMap=True, world = None, looseCallback=None, updateLifeCallback=None):
        super(Girl, self).__init__(settings, model, agentName, layer, soundmanager, uniqInMap)
        self.screamSound = self.soundmanager.createSoundEmitter('sounds/scream.ogg')
        self.dead = False
        self.coins = []
        self.world = world
        self.lay = False
        self.looseCallback = looseCallback
        self.updateLifeCallback = updateLifeCallback
        self.life = 100

    def onInstanceActionFinished(self, instance, action):
        #print "Action finished: " + str(action.getId())
        if self.lay:
            location = self.agent.getLocation()
            coords = location.getMapCoordinates()
            moveObject(self.coins[0], coords.x, coords.y)
            #self.world.hideItems([len(self.coins)])
            self.coins = self.coins[1:]
            self.moveStep('u')
            self.lay = False
            return
        
        super(Girl, self).onInstanceActionFinished(instance, action)

    def getActionsList(self, target_instance, target_agent, distance):
        actions = []
        if self.coins and not target_instance:
            actions.append('lay')
        if target_instance and distance < 1.5:
            if target_instance.getObject().getId() == "coins_map":
                actions.append('pick');
        inherited_actions = super(Girl, self).getActionsList(target_instance, target_agent, distance)
        return inherited_actions + actions
    
    # Execute before default doAction of Agent
    def doAction(self, name, reactionInstance, reactionAgent, callback, location=None):
        if name == "pick":
            coin = reactionInstance
            self.coins.append(coin)
            #self.world.showItems([n for n in xrange(1, len(self.coins)+1)])
            self.run(coin.getLocation())
            makeDisappear(coin)
            self.idle()
        elif name == "lay":
            self.run(location)
            self.lay = True
        else:
            super(Girl, self).doAction(name, reactionInstance, reactionAgent, callback)

    # Execute before default doReaction of Agent
    def doReaction(self, name, actionAgent, reactionInstance):
        if name=="talk":
            girlTexts = TDS.get("rio", "girlTexts")
            reactionInstance.say(random.choice(girlTexts), 5000)
            self.run(actionAgent.agent.getLocationRef())
        elif name=="kick" or name=='hit':
            if name=='kick':
                self.agent.say("Hey!!!", 3500)
            else:
                self.agent.say("Damn!!!", 3500)
            self.screamSound.play()
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
            
    def getHit(self, bee):
        if self.dead:
            return
        self.doReaction('hit', bee, self.agent)
        self.life -= 10
        self.updateLifeCallback(self.life)
        if self.life <= 0:
            self.die()
        
    def die(self):
        if not self.dead:
            self.footSound.stop()
            #self.screamSound.play()
            self.dead = True
            self.looseCallback()
            self.idle()
