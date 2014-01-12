from fife.fife import Location

def moveObject(instance, x=None, y=None, z=None):
    location = Location(instance.getLocation())
    coords = location.getMapCoordinates()
    if x:
        coords.x = x
    if y:
        coords.y = y
    if z:
        coords.y = z
    location.setMapCoordinates(coords)
    instance.setLocation(location)

def moveObjectRelative(instance, x=None, y=None, z=None):
    location = Location(instance.getLocation())
    coords = location.getMapCoordinates()
    if x:
        coords.x += x
    if y:
        coords.y += y
    if z:
        coords.y += z
    location.setMapCoordinates(coords)
    instance.setLocation(location)

def makeDisappear(instance):
    moveObject(instance, x=100, y=100)