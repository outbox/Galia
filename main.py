import sys
sys.path.append("./build/pynui")
from os import listdir
from math import *
from time import clock

from pynui import *
from app.hands import *
from app.cursor import *
from app.helper import *
from app.config import *
import app.states as states

from panda3d.core import *
from direct.interval.MetaInterval import Sequence
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.filter.CommonFilters import CommonFilters

class App(ShowBase):
  def __init__(self):
    ShowBase.__init__(self)

    base.disableMouse()

    self.win.setClearColor(VBase4(0, 0, 0, 0))

    self.nui = Nui()
    self.nui.smooth_factor = 0.9
    
    self.camLens.setFov(90)
    self.camLens.setNear(0.01)
    self.camLens.setFar(2)
    cam_pos = Vec3(0, -1, 0)
    cam_pos.z = -cam_pos.y * tan(vfov()/2) * (1 - floor_ratio*2)
    self.cam.setPos(cam_pos)

    self.picsNode = render.attachNewNode("Pics")
    
    maker = CardMaker("")
    frameRatio = self.camLens.getAspectRatio()
    left = 0
    files = [image_path + f for f in listdir(image_path)][0:6]
    before = clock()
    print "Loading", len(files), "files..."
    for file in files:
      try:
         texture = loader.loadTexture(file)
      except:
        continue
      texture.setMinfilter(Texture.FTLinearMipmapLinear)
      texture.setWrapU(Texture.WMClamp)
      texture.setWrapV(Texture.WMClamp)
      
      maker = CardMaker('')
      maker.setFrame(-1, 1, -1, 1)
      pic = self.picsNode.attachNewNode(maker.generate())
      pic.setTransparency(TransparencyAttrib.MAlpha, 1)
      pic.setTexture(texture)

      aspect_ratio = texture.getOrigFileXSize() * 1.0 / texture.getOrigFileYSize()
      height = self.wall_top() * pic_height_ratio
      width = height * aspect_ratio
      
      if width + (pic_margin + pic_strip_width) * 2 > 2:
        width = 2 - (pic_margin + pic_strip_width) * 2
        height = width / aspect_ratio

      pic.setPos(left + width / 2, -0.01, self.wall_top()/2)
      pic.setScale(width / 2, 1, height / 2)
      
      left += width + pic_margin
      
    print "Loaded in", str(clock() - before) + "s"

    self.picsNode.setPos(-self.picsNode.getChildren()[0].getScale().x, 0, 0) 

    self.create_wall()
    self.create_floor()

    # base.cTrav = CollisionTraverser('CollisionTraverser')

    # self.cursor = Cursor(self)
    # self.cursor_hand = None
    
    # pickerNode = CollisionNode('cursor')
    # #pickerNode.setFromCollideMask(Thumbs.CollisionMask)
    # self.cursor_ray = CollisionRay(self.cam.getPos(), Vec3.unitZ())
    # pickerNode.addSolid(self.cursor_ray)
    # pickerNP = render.attachNewNode(pickerNode)
    # self.collision_handler = CollisionHandlerEvent()
    # self.collision_handler.addInPattern('%fn-into-%in')
    # self.collision_handler.addAgainPattern('%fn-again-%in')
    # self.collision_handler.addOutPattern('%fn-out-%in')
    # base.cTrav.addCollider(pickerNP, self.collision_handler)

    self.update_task = PythonTask(self.update, 'UpdateTask')
    self.taskMgr.add(self.update_task)

    self.hand_interpolator = cubic_interpolator(0, 6, 0)

    self.hand_tracker = HandTracker()
    states.Start()

    self.accept('slide', self.slide)

  def update(self, task):
    self.nui.update()
    self.hand_tracker.update(self.nui.users)
    return Task.cont

  def slide(self, direction):
    

  def wall_top(self):
    return (- self.cam.getPos().y) * tan(vfov()/2) + self.cam.getPos().z

  def create_wall(self):
    maker = CardMaker('wall')
    maker.setFrame(-1, 1, 0, self.wall_top())
    wall = render.attachNewNode(maker.generate())

    buffer = base.win.makeTextureBuffer('shadow', 512, 512)
    buffer.setClearColor(VBase4(0, 0, 0, 0))
    display = buffer.makeDisplayRegion()
    camera = render.attachNewNode(Camera('shadow'))
    display.setCamera(camera)
    camera.node().setLens(base.camLens)
    camera.setMat(base.cam.getMat())
    camera.node().setScene(self.picsNode)

    blur_x = make_filter_buffer(buffer, 'blur-x')
    blur = make_filter_buffer(blur_x, 'blur-y')

    wall.setShaderInput('shadow', blur.getTexture())

    texture = loader.loadTexture("resources/wall.png")
    texture.setWrapU(Texture.WMClamp)
    texture.setWrapV(Texture.WMClamp)
    wall.setShaderInput('diffuse', texture)

    wall.setShader(load_shader('wall'))

  def create_floor(self):
    name = 'floor'
    z = 0

    buffer = base.win.makeTextureBuffer(name, 512, 512)
    buffer.setClearColor(VBase4(0, 0, 0, 0))
    display = buffer.makeDisplayRegion()
    camera = render.attachNewNode(Camera(name))
    display.setCamera(camera)

    camera.node().setInitialState(RenderState.make(CullFaceAttrib.makeReverse()))
    camera.node().setLens(base.camLens)
    symmetry = Mat4.translateMat(0,0,-z) * Mat4.scaleMat(1,1,-1) * Mat4.translateMat(0,0,z)
    camera.setMat(base.cam.getMat() * symmetry)
    camera.node().setScene(self.picsNode)

    blur_x = make_filter_buffer(buffer, 'blur-x')
    blur = make_filter_buffer(blur_x, 'blur-y')

    maker = CardMaker(name)
    maker.setFrame(-1, 1, -1, 0)
    card = render.attachNewNode(maker.generate())
    card.setShader(load_shader('floor'))
    card.setTexture(blur.getTexture())
    card.setShaderInput('diffuse', loader.loadTexture('resources/floor.jpg'))
    card.setMat(Mat4.rotateMat(-90, VBase3.unitX()) * Mat4.translateMat(0, 0, z))

if __name__ == '__main__':
  loadPrcFile("local-config.prc")
  app = App()
  app.run()
