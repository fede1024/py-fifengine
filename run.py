#!/usr/bin/env python

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
# This is the rio de hola client for FIFE.

from __future__ import division
import sys, os

fife_path = os.path.join('..','..','engine','python')
fife_path = os.path.join('/home','federico','tmp','sdproject','engine','python')
print "Importing fife from: "
print fife_path
if os.path.isdir(fife_path) and fife_path not in sys.path:
    sys.path.insert(0,fife_path)

from fife import fife
print "Using the FIFE python module found here: ", os.path.dirname(fife.__file__)

from fife.extensions import *
from code import world
from code.common import eventlistenerbase
from fife.extensions import pychan
from fife.extensions.pychan.pychanbasicapplication import PychanApplicationBase
from fife.extensions.pychan.fife_pychansettings import FifePychanSettings
from fife.extensions.fife_utils import getUserDataDirectory

TDS = FifePychanSettings(app_name="rio_de_hola")

class ApplicationListener(eventlistenerbase.EventListenerBase):
    def __init__(self, engine, world):
        super(ApplicationListener, self).__init__(engine,regKeys=True,regCmd=True, regMouse=False, regConsole=False, regWidget=True)
#        super(ApplicationListener, self).__init__(engine,regKeys=True,regCmd=True, regMouse=True, regConsole=False, regWidget=True)
        self.engine = engine
        self.world = world
        self.world.gui = self
        engine.getEventManager().setNonConsumableKeys([fife.Key.ESCAPE,])

        self.quit = False
        self.aboutWindow = None
        self.youLooseWindow = None

        self.rootpanel = pychan.loadXML('gui/xml/rootpanel.xml')
        self.rootpanel.mapEvents({ 
            'quitButton' : self.onQuitButtonPress,
            'aboutButton' : self.onAboutButtonPress,
            'optionsButton' : TDS.showSettingsDialog,
            'newsButton' : self.onNewsButtonPress,
            'soundButton' : self.onSoundButtonPress
        })
        button =  self.rootpanel.getNamedChildren()['soundButton'][0]
        if int(TDS.get("FIFE", "PlaySounds")):
            button.text = unicode("Music:  ON", "utf-8")
        else:
            button.text = unicode("Music: OFF", "utf-8")
        self.rootpanel.show()

        self.character_gui = pychan.loadXML('gui/xml/player.xml')
        self.character_gui.mapEvents({ 
             'boy' : self.onBoyButtonPress,
             'girl' : self.onGirlButtonPress
         })
        self.boyButton =  self.character_gui.getNamedChildren()['boy'][0]
        self.girlButton =  self.character_gui.getNamedChildren()['girl'][0]
        self.character_gui.show()
        self.girlButton.hide()

        self.itemsContainer = pychan.loadXML('gui/xml/items.xml')
        self.itemsImages = []
        self.itemsImages.append(self.itemsContainer.getNamedChildren()['flask'][0])
        self.itemsImages.append(self.itemsContainer.getNamedChildren()['coins1'][0])
        self.itemsImages.append(self.itemsContainer.getNamedChildren()['coins2'][0])
        self.itemsImages.append(self.itemsContainer.getNamedChildren()['coins3'][0])
        self.itemsContainer.show()
        #for x in self.itemsImages:
        #    x.hide()
        
        self.healthBar = pychan.loadXML('gui/xml/life.xml')
        self.healthImage = self.healthBar.getNamedChildren()['fg'][0]
        self.healthBar.show()
    
    def girlLifeUpdate(self, life):
        length = 199/100*life
        self.healthImage.width = int(length)
    
    def keyPressed(self, evt):
        keyval = evt.getKey().getValue()
        keystr = evt.getKey().getAsString().lower()
        if keyval == fife.Key.ESCAPE:
            self.quit = True
            evt.consume()
        elif keystr == 'p':
            self.engine.getRenderBackend().captureScreen('screenshot.png')
            evt.consume()
        elif keystr == 'x':
            if self.world.mainAgent.agent.getObject().getId() == 'girl':
                self.onGirlButtonPress()
            elif self.world.mainAgent.agent.getObject().getId() == 'boy':
                self.onBoyButtonPress()
            evt.consume()

    def onCommand(self, command):
        if command.getCommandType() == fife.CMD_QUIT_GAME:
            self.quit = True
            command.consume()

    def showItems(self, items):
        for n in items:
            self.itemsImages[n].show()

    def hideItems(self, items):
        for n in items:
            self.itemsImages[n].hide()

    def youLoose(self):
        if not self.youLooseWindow:
            self.youLooseWindow = pychan.loadXML('gui/xml/youLoose.xml')
            def restartWorld():
                self.world.restart()
                self.girlLifeUpdate(100)
                self.youLooseWindow.hide()
            self.youLooseWindow.mapEvents({ 'closeButton' : restartWorld })
            self.youLooseWindow.distributeData({ 'looseText' : "The girl got killed. You loose. Try again!" })
        self.youLooseWindow.show()
        
    def onQuitButtonPress(self):
        cmd = fife.Command()
        cmd.setSource(None)
        cmd.setCommandType(fife.CMD_QUIT_GAME)
        self.engine.getEventManager().dispatchCommand(cmd)

    def onAboutButtonPress(self):
        if not self.aboutWindow:
            self.aboutWindow = pychan.loadXML('gui/xml/help.xml')
            self.aboutWindow.mapEvents({ 'closeButton' : self.aboutWindow.hide })
            self.aboutWindow.distributeData({ 'helpText' : open("misc/infotext.txt").read() })
        self.aboutWindow.show()
    
    def onNewsButtonPress(self):
        if not self.aboutWindow:
            self.aboutWindow = pychan.loadXML('gui/xml/news.xml')
            self.aboutWindow.mapEvents({ 'closeButton' : self.aboutWindow.hide })
            #self.aboutWindow.distributeData({ 'helpText' : open("misc/infotext.txt").read() })
            self.aboutWindow.distributeData({ 'newsText' : open("game_changes.txt").read() })
        self.aboutWindow.show()

    def onSoundButtonPress(self):
        button =  self.rootpanel.getNamedChildren()['soundButton'][0]
        if (self.world.soundActive == True):
            self.world.music.stop()
            self.world.soundActive = False
            button.text = unicode("Music: OFF", "utf-8")
            TDS.set("FIFE", "PlaySounds", False)
            TDS.saveSettings()
        else:
            self.world.music.play()
            self.world.soundActive = True
            button.text = unicode("Music:  ON", "utf-8")
            TDS.set("FIFE", "PlaySounds", True)
            TDS.saveSettings()

    def onBoyButtonPress(self):
        self.girlButton.show()
        self.boyButton.hide()
        self.world.switchMainAgentTo('girl')
        
    def onGirlButtonPress(self):
        self.boyButton.show()
        self.girlButton.hide()
        self.world.switchMainAgentTo('boy')



class IslandDemo(PychanApplicationBase):
    def __init__(self):
        super(IslandDemo,self).__init__(TDS)
        self.world = world.World(self.engine)
        self.listener = ApplicationListener(self.engine, self.world)
        self.world.load(str(TDS.get("rio", "MapFile"))) # Create world and agents

    def createListener(self):
        pass # already created in constructor

    def _pump(self):
        if self.listener.quit:
            self.breakRequested = True
            
            # get the correct directory to save the map file to
            mapSaveDir = getUserDataDirectory("fife", "rio_de_hola") + "/maps"
            
            # create the directory structure if it does not exist
            if not os.path.isdir(mapSaveDir):
                os.makedirs(mapSaveDir)
            
            # save map file to directory
            self.world.save(mapSaveDir + "/savefile.xml")
        else:
            self.world.pump()

def main():
    app = IslandDemo()
    app.run()

if __name__ == '__main__':
    main()
