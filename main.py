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
from app.flow import *
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

    self.create_wall()
    self.create_floor()
    
    maker = CardMaker("")
    frameRatio = self.camLens.getAspectRatio()
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

      pic.setDepthWrite(False)
      pic.setDepthTest(False)

    print "Loaded in", str(clock() - before) + "s"

    self.selection = 0

    for (pic, pos, scale) in self.pics_pos_scale():
      pic.setScale(scale)
      pic.setPos(pos)

    self.cursor = Cursor(self)
    self.cursor_user = None
    
    base.cTrav = CollisionTraverser('CollisionTraverser')    
    pickerNode = CollisionNode('cursor')
    #pickerNode.setFromCollideMask(Thumbs.CollisionMask)
    self.cursor_ray = CollisionRay(self.cam.getPos(), Vec3.unitZ())
    pickerNode.addSolid(self.cursor_ray)
    pickerNP = render.attachNewNode(pickerNode)
    self.collision_handler = CollisionHandlerEvent()
    self.collision_handler.addInPattern('%fn-into-%in')
    self.collision_handler.addAgainPattern('%fn-again-%in')
    self.collision_handler.addOutPattern('%fn-out-%in')
    base.cTrav.addCollider(pickerNP, self.collision_handler)

    self.update_task = PythonTask(self.update, 'UpdateTask')
    self.taskMgr.add(self.update_task)

    self.hand_interpolator = cubic_interpolator(0, 6, 0)

    self.hand_tracker = HandTracker()
    states.Start()

    self.accept('slide', self.slide)
    self.accept('show-thumbnails', self.show_thumbnails)
    self.accept('hide-thumbnails', self.hide_thumbnails)

  def update(self, task):
    self.nui.update()
    self.hand_tracker.update(self.nui.users)

    if self.cursor_user is not None:
      left_hand = self.hand_tracker.hands.get((self.cursor_user, Skeleton.left), None)
      right_hand = self.hand_tracker.hands.get((self.cursor_user, Skeleton.right), None)
      if left_hand is None or (right_hand is not None and right_hand.position.y > left_hand.position.y):
        hand = right_hand
      else:
        hand = left_hand
      if hand:
        self.cursor.set_side(hand.side)
        pos = hand.position
        pos.x /= 0.25
        pos.y /= 0.2
        self.cursor.node.setPos(pos.x, 0, (pos.y + 1) / 2 * self.wall_top)
        self.cursor_ray.setDirection(self.cursor.node.getPos() - self.cam.getPos())

    return Task.cont

  # Iterate through the default positions and scales of the pictures
  def pics_pos_scale(self):
    index = 0
    for pic in self.picsNode.getChildren():
      texture = pic.getTexture()
      aspect_ratio = texture.getXSize() * 1.0 / texture.getYSize()
      (width, height) = self.fit_wall(aspect_ratio, pic_margin + pic_strip_width)
      scale = Vec3(width / 2, 1, height / 2)

      if index == self.selection - 1:
        x = -1 - scale.x + pic_strip_width
      elif index == self.selection:
        x = 0
      elif index == self.selection + 1:
        x = 1 + scale.x - pic_strip_width
      else:
        x = (index - self.selection) * 2
      pos = Vec3(x, -0.01, self.wall_top/2)

      yield (pic, pos, scale)
      index += 1

  def animate_pic(self, pic, pos, scale, time):
    interpolate('arrange', pic.setPos, cubic_interpolator(pic.getPos(), pos, Vec3()), time)
    interpolate('arrange', pic.setScale, cubic_interpolator(pic.getScale(), scale, Vec3(0,0,0)), time)

  # Move each picture to its default position based on the current selection
  def rearrange_pics(self, base_time_on_distance = False):
    base.taskMgr.remove('arrange')
    for (pic, pos, scale) in self.pics_pos_scale():
      time = 0.5 if not base_time_on_distance else self.time_between(pos, pic.getPos())
      self.animate_pic(pic, pos, scale, time)

  def slide(self, direction):
    new_selection = self.selection + direction
    if new_selection < 0 or new_selection >= self.picsNode.getNumChildren():
      return
    self.selection = new_selection
    self.reorder_pics()
    self.rearrange_pics()

  # Z order pictures to make the selection always on top
  def reorder_pics(self):
    index = 0
    for pic in self.picsNode.getChildren():
      pic.setBin('fixed', 41 if index == self.selection else 40)
      index += 1

  def show_thumbnails(self, user):
    self.cursor.node.show()
    self.cursor_user = user

    flow = Flow(self.pics_pos_scale(), 2, self.wall_top, pic_margin, thumbnail_margin)
    for (pic, pos, scale) in flow.layout_items:
      self.animate_pic(pic, pos, scale, self.time_between(pos, pic.getPos()))

  def hide_thumbnails(self):
    self.cursor_user = None
    self.cursor.node.hide()
    self.rearrange_pics(True)

  def time_between(self, a, b):
    return 0.3 + log(1 + (a - b).length()) / 5
    
  # Return the size that will fit the wall at a desired aspect ratio
  def fit_wall(self, aspect_ratio, margin):
    return fit(aspect_ratio, 2 - margin * 2, self.wall_top * pic_height_ratio)

  @property
  def wall_top(self):
    return (- self.cam.getPos().y) * tan(vfov()/2) + self.cam.getPos().z

  def create_wall(self):
    maker = CardMaker('wall')
    maker.setFrame(-1, 1, 0, self.wall_top)
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
