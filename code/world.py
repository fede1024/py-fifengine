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
from fife.extensions import pychan
from fife.extensions.pychan.internal import get_manager
import datetime

from code.utils import moveObject
from code.common.eventlistenerbase import EventListenerBase
from fife.extensions.savers import saveMapFile
from fife.extensions.soundmanager import SoundManager
from agents.boy import Boy
from agents.girl import Girl
from agents.bee import Bee
from agents.priest import Priest
from agents.chemist import Chemist
from agents.dynamite import Dynamite
from agents.beekeeper import Beekeeper
from agents.agent import create_anonymous_agents
from fife.extensions.fife_settings import Setting

TDS = Setting(app_name="rio_de_hola")

num_bees = 10

class World(EventListenerBase):
    """
    The world!

    This class handles:
      setup of map view (cameras ...)
      loading the map
      GUI for right clicks
      handles mouse/key events which aren't handled by the GUI.
       ( by inheriting from EventlistenerBase )

    That's obviously too much, and should get factored out.
    """
    def __init__(self, engine):
        super(World, self).__init__(engine, regMouse=True, regKeys=True)
        self.engine = engine
        self.eventmanager = engine.getEventManager()
        self.model = engine.getModel()
        self.filename = ''
        self.pump_ctr = 0 # for testing purposis
        self.ctrldown = False
        self.instancemenu = None
        self.instance_to_agent = {}
        self.dynamic_widgets = {}
        self.gui = None # Overwritten during GUI initialization

        self.light_intensity = 1
        self.light_sources = 0
        self.lightmodel = 1  # DK why

        self.soundmanager = SoundManager(self.engine)
        self.music = None

    def show_instancemenu(self, clickpoint, location, instance):
        """
        Build and show a popupmenu for an instance that the player
        clicked on. The available actions are dynamically added to
        the menu (and mapped to the onXYZ functions).
        """
        if instance and instance.getFifeId() == self.mainAgent.agent.getFifeId(): # click on yourself
            return

        # Create the popup.
        self.build_instancemenu()
        self.instancemenu.clickpoint = clickpoint
        self.instancemenu.location = location
        self.instancemenu.instance = instance

        # Add the buttons according to circumstances.
        if instance:
            target_distance = self.mainAgent.agent.getLocation().getLayerDistanceTo(instance.getLocation())
        else:
            target_distance = 0
        
        if instance and self.instance_to_agent.has_key(instance.getFifeId()):
            target_agent = self.instance_to_agent[instance.getFifeId()]
        else:
            target_agent = None
            
        actionList = self.mainAgent.getActionsList(instance, target_agent, target_distance)
        
        for action in actionList:
            if self.dynamic_widgets.has_key(action): 
                self.instancemenu.addChild(self.dynamic_widgets[action])
            else:
                print "ERROR: no defined action %s for instance menu."%action
        
#         self.instancemenu.addChild(self.dynamic_widgets['inspect'])
#         if target_distance > 3.0:
#             self.instancemenu.addChild(self.dynamic_widgets['move'])
#         else:
#             if self.instance_to_agent.has_key(instance.getFifeId()):
#                 self.instancemenu.addChild(self.dynamic_widgets['talk'])
#                 if self.mainAgent == self.boy:
#                     self.instancemenu.addChild(self.dynamic_widgets['kick'])
        # And show it :)
        self.instancemenu.position = (clickpoint.x, clickpoint.y)
        self.instancemenu.show()

    def build_instancemenu(self):
        """
        Just loads the menu from an XML file
        and hooks the events up.
        The buttons are removed and later re-added if appropiate.
        """
        self.hide_instancemenu()
        dynamicbuttons = ('move', 'talk', 'open', 'kick', 'inspect', 'pick', 'lay') 
        self.instancemenu = pychan.loadXML('gui/xml/instancemenu.xml')
        self.instancemenu.mapEvents({
            'move' : lambda: self.onAction('move'),
            'talk' : lambda: self.onAction('talk'),
            'kick' : lambda: self.onAction('kick'),
            'open' : lambda: self.onAction('open'),
            'pick' : lambda: self.onAction('pick'),
            'lay' : lambda: self.onAction('lay'),
            'inspect' : lambda: self.onAction('inspect'),
        })
        for btn in dynamicbuttons:
            self.dynamic_widgets[btn] = self.instancemenu.findChild(name=btn)
        self.instancemenu.removeAllChildren()

    def hide_instancemenu(self):
        if self.instancemenu:
            self.instancemenu.hide()

    def reset(self):
        """
        Clear the agent information and reset the moving secondary camera state.
        """
        if self.music:
            self.music.stop()
            
        self.map, self.agentlayer = None, None
        self.cameras = {}
        self.boy, self.girl, self.clouds, self.beekeepers = None, None, [], []
        self.cur_cam2_x, self.initial_cam2_x, self.cam2_scrolling_right = 0, 0, True
        self.target_rotation = 0
        self.instance_to_agent = {}

    def load(self, filename):
        """
        Load a xml map and setup agents and cameras.
        """
        
        self.filename = filename
        self.reset()
        loader = fife.MapLoader(self.engine.getModel(), 
                                self.engine.getVFS(), 
                                self.engine.getImageManager(), 
                                self.engine.getRenderBackend())
                                
        if loader.isLoadable(filename):
            self.map = loader.load(filename)

        self.initAgents()
        self.initCameras()

        #Set background color
        self.engine.getRenderBackend().setBackgroundColor(80,80,255)

        # play track as background music
        self.music = self.soundmanager.createSoundEmitter('music/hang.ogg')
        self.music.looping = True
        self.music.gain = 128

        if int(Setting(app_name="rio_de_hola").get("FIFE", "PlaySounds")):
            self.music.play()
            self.soundActive = True
        else:
            self.soundActive = False
            
    def loose(self):
        self.cameras['main'].setOverlayColor(0,0,0,180)
        self.gui.youLoose()
    
    def win(self):
        self.cameras['main'].setOverlayColor(0,0,255,180)
        self.gui.youWin()
    
    def showItems(self, items):
        self.gui.showItems(items)

    def hideItems(self, items):
        self.gui.hideItems(items)

    def restart(self):
        self.model.deleteMaps()
        self.load(self.filename)
        
    def initAgents(self):
        """
        Setup agents.

        For this techdemo we have a very simple 'active things on the map' model,
        which is called agents. All rio maps will have a separate layer for them.

        Note that we keep a mapping from map instances (C++ model of stuff on the map)
        to the python agents for later reference.
        """
        self.agentlayer = self.map.getLayer('TechdemoMapGroundObjectLayer')
        self.boy = Boy(TDS, self.model, 'PC', self.agentlayer, self.soundmanager, world = self)
        self.instance_to_agent[self.boy.agent.getFifeId()] = self.boy
        self.mainAgent = self.boy
        self.boy.start()

        self.girl = Girl(TDS, self.model, 'NPC:girl', self.agentlayer, self.soundmanager, world = self, looseCallback = self.loose, updateLifeCallback = self.gui.girlLifeUpdate)
        self.instance_to_agent[self.girl.agent.getFifeId()] = self.girl
        self.girl.start()

        self.priest = Priest(TDS, self.model, 'priest', self.agentlayer, self.soundmanager, world = self)
        self.instance_to_agent[self.priest.agent.getFifeId()] = self.priest
        self.priest.start()

        self.chemist = Chemist(TDS, self.model, 'chemist', self.agentlayer, self.soundmanager, world = self, winCallback=self.win)
        self.instance_to_agent[self.chemist.agent.getFifeId()] = self.chemist
        self.chemist.start()

        self.bees = []
        for i in xrange(num_bees):
            bee = Bee(TDS, self.model, 'bee' + str(i), self.agentlayer, self.soundmanager, girl = self.girl)
            self.instance_to_agent[bee.agent.getFifeId()] = bee
            bee.start()
            self.bees.append(bee)

        for i in xrange(12):
            dynamite = Dynamite(TDS, self.model, 'dyn_' + str(i), self.agentlayer, self.soundmanager, bees=self.bees, girl=self.girl)
            self.instance_to_agent[dynamite.agent.getFifeId()] = dynamite
            dynamite.start()

        self.beekeepers = create_anonymous_agents(TDS, self.model, 'beekeeper', self.agentlayer, Beekeeper, self.soundmanager)
        for beekeeper in self.beekeepers:
            self.instance_to_agent[beekeeper.agent.getFifeId()] = beekeeper
            beekeeper.start()
            
        moveObject(self.agentlayer.getInstance('flask0'), x=3.5, y=9.5)
        moveObject(self.agentlayer.getInstance('coins0'), x=-18, y=-15)
        moveObject(self.agentlayer.getInstance('coins1'), x=-22.5, y=-14.5)
        moveObject(self.agentlayer.getInstance('coins2'), x=-18, y=-14.5)
            
    def initCameras(self):
        """
        Before we can actually see something on screen we have to specify the render setup.
        This is done through Camera objects which offer a viewport on the map.

        For this techdemo two cameras are used. One follows the boy(!) via 'attach'
        the other one scrolls around a bit (see the pump function).
        """
        camera_prefix = self.filename.rpartition('.')[0] # Remove file extension
        camera_prefix = camera_prefix.rpartition('/')[2] # Remove path
        camera_prefix += '_'
        self.target_rotation  = 0
        self.cameras = {}
        
        for cam in self.map.getCameras():
            camera_id = cam.getId().replace(camera_prefix, '')
            self.cameras[camera_id] = cam
            cam.resetRenderers()
            
        self.cameras['main'].attach(self.mainAgent.agent)

        # Floating text renderers currntly only support one font.
        # ... so we set that up.
        # You'll se that for our demo we use a image font, so we have to specify the font glyphs
        # for that one.
        renderer = fife.FloatingTextRenderer.getInstance(self.cameras['main'])
        textfont = get_manager().createFont('fonts/rpgfont.png', 0, str(TDS.get("FIFE", "FontGlyphs")));
        renderer.setFont(textfont)
        renderer.activateAllLayers(self.map)
        renderer.setBackground(100, 255, 100, 165)
        renderer.setBorder(50, 255, 50)
        renderer.setEnabled(True)
        
        # Activate the grid renderer on all layers
        renderer = self.cameras['main'].getRenderer('GridRenderer')
        renderer.activateAllLayers(self.map)
        
        # The small camera shouldn't be cluttered by the 'humm di dums' of our boy.
        # So we disable the renderer simply by setting its font to None.
        renderer = fife.FloatingTextRenderer.getInstance(self.cameras['small'])
        renderer.setFont(None)

        # The following renderers are used for debugging.
        # Note that by default ( that is after calling View.resetRenderers or Camera.resetRenderers )
        # renderers will be handed all layers. That's handled here.
        renderer = fife.CoordinateRenderer.getInstance(self.cameras['main'])
        renderer.setFont(textfont)
        renderer.clearActiveLayers()
        renderer.addActiveLayer(self.map.getLayer(str(TDS.get("rio", "CoordinateLayerName"))))

        renderer = self.cameras['main'].getRenderer('QuadTreeRenderer')
        renderer.setEnabled(True)
        renderer.clearActiveLayers()
        if str(TDS.get("rio", "QuadTreeLayerName")):
            renderer.addActiveLayer(self.map.getLayer(str(TDS.get("rio", "QuadTreeLayerName"))))

        # Fog of War stuff
        renderer = fife.CellRenderer.getInstance(self.cameras['main'])
        renderer.setEnabled(True)
        renderer.clearActiveLayers()
        renderer.addActiveLayer(self.map.getLayer('TechdemoMapGroundObjectLayer'))
        concimg = self.engine.getImageManager().load("misc/black_cell.png")
        maskimg = self.engine.getImageManager().load("misc/mask_cell.png")
        renderer.setConcealImage(concimg)
        renderer.setMaskImage(maskimg)
        renderer.setFogOfWarLayer(self.map.getLayer('TechdemoMapGroundObjectLayer'))
        
        #disable FoW by default.  Users can turn it on with the 'f' key.
        renderer.setEnabledFogOfWar(False)

        # Set up the second camera
        # NOTE: We need to explicitly call setLocation, there's a bit of a messup in the Camera code.
        self.cameras['small'].setLocation(self.boy.agent.getLocation())
        self.cameras['small'].attach(self.girl.agent)
        self.cameras['small'].setOverlayColor(100,0,0,100)
        self.cameras['small'].setEnabled(False)

        self.target_rotation = self.cameras['main'].getRotation()


    def save(self, filename):
        saveMapFile(filename, self.engine, self.map)

    def getInstancesAt(self, clickpoint):
        """
        Query the main camera for instances on our active(agent) layer.
        """
        return self.cameras['main'].getMatchingInstances(clickpoint, self.agentlayer)

    def getLocationAt(self, clickpoint):
        """
        Query the main camera for the Map location (on the agent layer)
        that a screen point refers to.
        """
        target_mapcoord = self.cameras['main'].toMapCoordinates(clickpoint, False)
        target_mapcoord.z = 0
        location = fife.Location(self.agentlayer)
        location.setMapCoordinates(target_mapcoord)
        return location

    def keyPressed(self, evt):
        if self.girl.dead:
            return
        keyval = evt.getKey().getValue()
        keystr = evt.getKey().getAsString().lower()
        if keystr == 't':
            r = self.cameras['main'].getRenderer('GridRenderer')
            r.setEnabled(not r.isEnabled())
        elif keystr == 'c':
            r = self.cameras['main'].getRenderer('CoordinateRenderer')
            r.setEnabled(not r.isEnabled())
        elif keystr == 's':
            c = self.cameras['small']
            c.setEnabled(not c.isEnabled())
        elif keystr == 'r':
            self.model.deleteMaps()
            self.load(self.filename)
            self.gui.girlLifeUpdate(100)
            self.startTime = datetime.datetime.now()
        elif keystr == 'f':
            renderer = fife.CellRenderer.getInstance(self.cameras['main'])
            renderer.setEnabledFogOfWar(not renderer.isEnabledFogOfWar())
            self.cameras['main'].refresh()
        elif keystr == 'o':
            self.target_rotation = (self.target_rotation + 90) % 360
        elif keystr == '2':
            self.lightIntensity(0.1)
        elif keystr == '1':
            self.lightIntensity(-0.1)
        elif keystr == '5':
            self.lightSourceIntensity(25)
        elif keystr == '4':
            self.lightSourceIntensity(-25)
        elif keystr == '0' or keystr == fife.Key.NUM_0:
            if self.ctrldown:
                self.cameras['main'].setZoom(1.0)
        elif keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
            self.ctrldown = True
        else:
            self.mainAgent.keyPressed(keyval)

    def keyReleased(self, evt):
        if self.girl.dead:
            return
        keyval = evt.getKey().getValue()
        if keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
            self.ctrldown = False

    def mouseWheelMovedUp(self, evt):
        if self.girl.dead:
            return
        if self.ctrldown:
            self.cameras['main'].setZoom(self.cameras['main'].getZoom() * 1.05)

    def mouseWheelMovedDown(self, evt):
        if self.girl.dead:
            return
        if self.ctrldown:
            self.cameras['main'].setZoom(self.cameras['main'].getZoom() / 1.05)

    def changeRotation(self):
        """
        Smoothly change the main cameras rotation until
        the current target rotation is reached.
        """
        if "main" in self.cameras:
            currot = self.cameras['main'].getRotation()
            if self.target_rotation != currot:
                self.cameras['main'].setRotation((currot + 5) % 360)

    def mousePressed(self, evt):
        if evt.isConsumedByWidgets() or self.girl.dead:
            return

        clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
        if (evt.getButton() == fife.MouseEvent.LEFT):
            self.hide_instancemenu()
            self.mainAgent.run(self.getLocationAt(clickpoint) )

        if (evt.getButton() == fife.MouseEvent.RIGHT):
            location = self.getLocationAt(clickpoint)
            instances = self.getInstancesAt(clickpoint)
            #print "selected instances on agent layer: ", [i.getObject().getId() for i in instances]
            if instances:
                self.show_instancemenu(clickpoint, location, instances[0])
            else:
                self.show_instancemenu(clickpoint, location, None)

    def mouseMoved(self, evt):
        if not self.girl or self.girl.dead:
            return
        renderer = fife.InstanceRenderer.getInstance(self.cameras['main'])
        renderer.removeAllOutlines()

        pt = fife.ScreenPoint(evt.getX(), evt.getY())
        instances = self.getInstancesAt(pt);
        agent_names = set([y.agent.getObject().getId() for _, y in self.instance_to_agent.iteritems()])
        agent_names.add('flask_map')
        agent_names.add('coins_map')
        for i in instances:
            aid = i.getObject().getId() 
            me = self.mainAgent.agent.getObject().getId()
            if aid in agent_names and aid != me:
                renderer.addOutlined(i, 173, 255, 47, 2)

    def lightIntensity(self, value):
        if self.light_intensity+value <= 1 and self.light_intensity+value >= 0:
            self.light_intensity = self.light_intensity + value

            if self.lightmodel == 1:
                self.cameras['main'].setLightingColor(self.light_intensity, self.light_intensity, self.light_intensity)

    def lightSourceIntensity(self, value):
        if self.light_sources+value <= 255 and self.light_sources+value >= 0:
            self.light_sources = self.light_sources+value
            renderer = fife.LightRenderer.getInstance(self.cameras['main'])

            renderer.removeAll("beekeeper_simple_light")
            renderer.removeAll("boy")
            renderer.removeAll("girl_simple_light")

            if self.lightmodel == 1:
                node = fife.RendererNode(self.boy.agent)
                renderer.addSimpleLight("boy", node, self.light_sources, 64, 32, 1, 1, 255, 255, 255)

                node = fife.RendererNode(self.girl.agent)       
                renderer.addSimpleLight("girl_simple_light", node, self.light_sources, 64, 32, 1, 1, 255, 255, 255)

                for beekeeper in self.beekeepers:
                    node = fife.RendererNode(beekeeper.agent)
                    renderer.addSimpleLight("beekeeper_simple_light", node, self.light_sources, 120, 32, 1, 1, 255, 255, 255)       

    def onConsoleCommand(self, command):
        result = ''
        try:
            result = str(eval(command))
        except Exception, e:
            result = str(e)
        return result

    def onAction(self, name):
        """ self.mainAgent is performing action 'name' relate to some instance menu"""
        self.hide_instancemenu()
        destInstance = self.instancemenu.instance
        if destInstance and self.instance_to_agent.has_key(destInstance.getFifeId()):        # The reactor is an agent
            destAgent = self.instance_to_agent[destInstance.getFifeId()]
            def callback():
                print "Performing reaction to", name
                destAgent.doReaction(name, self.mainAgent, destInstance)
            print "Performing action", name
            self.mainAgent.doAction(name, destInstance, destAgent, callback)
        else:                                                                                                               # The reactor is not an agent
            self.mainAgent.doAction(name, destInstance, None, None, self.instancemenu.location)

    def pump(self):
        """
        Called every frame.
        """
        
        if not self.girl or self.girl.dead:
            return
        
        if self.boy.bottle:
            if self.gui.itemsImages[0].x < 5:
                self.gui.itemsImages[0].x += 2
        else:
            if self.gui.itemsImages[0].x > -60:
                self.gui.itemsImages[0].x -= 2
           
        coins = len(self.girl.coins) 

        for i in xrange(3):
            if i < coins:
                if self.gui.itemsImages[i+1].x < 5:
                    self.gui.itemsImages[i+1].x += 2
            else:
                if self.gui.itemsImages[i+1].x > -60:
                    self.gui.itemsImages[i+1].x -= 2

        bee = self.bees[self.pump_ctr%num_bees]
        
        flask = self.agentlayer.getInstance('flask0')
        #bees = [y for _, y in self.instance_to_agent.iteritems() if y.agent.getObject().getId() == 'bee']
        boy_distance = 1000

        if self.boy.bottle:
            boy_distance = self.boy.agent.getLocation().getLayerDistanceTo(bee.agent.getLocation())
        flask_distance = flask.getLocation().getLayerDistanceTo(bee.agent.getLocation())
        girl_distance = self.girl.agent.getLocation().getLayerDistanceTo(bee.agent.getLocation())
        f = ""
        if bee.followed:
            f = bee.followed.getObject().getId()
        if girl_distance < 5 and not bee.isDead():
            if f == "girl" and not bee.isIdle():
                return
            #print "1) Following:", f
            if not bee.isAttacking():
                bee.followed = self.girl.agent
                bee.follow(self.girl.agent)
        elif flask_distance < 5  and not bee.isDead():
            if f == "flask_map" and not bee.isIdle():
                return
            #print "2) Following:", f
            bee.followed = flask
            bee.follow(flask)
        elif boy_distance < 5 and not bee.isDead():
            if f == "boy" and not bee.isIdle():
                return
            #print "3) Following:", f
            bee.followed = self.boy.agent
            bee.follow(self.boy.agent)
                
        self.changeRotation()
        self.pump_ctr = (self.pump_ctr+1) % 1000
        
    def switchMainAgentTo(self, name):
        if name == 'boy':
            self.mainAgent = self.boy
            other = self.girl
        elif name == 'girl':
            self.mainAgent = self.girl
            other = self.boy
        else:
            return
        self.cameras['main'].attach(self.mainAgent.agent)
        self.cameras['small'].attach(other.agent)
        print "Switching to " + name
