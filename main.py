from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
import os

image_path = "/Users/max/Pictures/iPhoto Library/Originals/2011/Parque Lecocq/"
 
class MyApp(ShowBase):
  def __init__(self):
    ShowBase.__init__(self)
    
    files = [image_path + f for f in os.listdir(image_path)]
    files.sort()

    self.win.setClearColor(VBase4(0, 0, 0, 0))

    self.cam.setPos(0, -2, 0)
    self.camLens.setFov(90)
    self.camLens.setNear(0.01)
    self.camLens.setFar(1000)
    
    maker = CardMaker("")
    maker.setFrameFullscreenQuad()
    card = NodePath(maker.generate())
    card.reparentTo(render)

    texture = loader.loadTexture(files[0])
    card.setTexture(texture)
 
app = MyApp()
app.run()
