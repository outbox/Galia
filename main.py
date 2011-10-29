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

    # self.nui = Nui()
    # self.nui.smooth_factor = 0.9
    
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
    files = [image_path + f for f in listdir(image_path)]#[0:6]
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

      pic.setBin("fixed", 40)
      pic.setDepthWrite(False)
      pic.setDepthTest(False)

    print "Loaded in", str(clock() - before) + "s"

    self.selection = 0

    for (pic, pos, scale) in self.pics_pos_scale():
      pic.setScale(scale)
      pic.setPos(pos)

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
    self.accept('show-thumbnails', self.show_thumbnails)
    self.accept('hide-thumbnails', self.hide_thumbnails)

  def update(self, task):
    # self.nui.update()
    # self.hand_tracker.update(self.nui.users)
    self.hand_tracker.update({})
    return Task.cont

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

  def reorder_pics(self):
    index = 0
    for pic in self.picsNode.getChildren():
      pic.setBin('fixed', 41 if index == self.selection else 40)
      index += 1

  def show_thumbnails(self):
    one_row_width, average_height = 0, 0
    for (pic, pos, scale) in self.pics_pos_scale():
      one_row_width += scale.x * 2 + pic_margin
      average_height += scale.z * 2
    average_height /= self.picsNode.getNumChildren()
    one_row_width -= pic_margin
    
    def flow(rows):
      target_row_width = one_row_width / rows
      row = []
      row_size = Vec2()
      top = 0
      for (pic, pos, scale) in self.pics_pos_scale():
        if row_size.x == 0 or row_size.x + pic_margin + scale.x < target_row_width:
          if row_size.x > 0: row_size.x += pic_margin
          row_size.x += scale.x * 2
          row_size.y = max(scale.z * 2, row_size.y)
          row.append((pic, Vec3(row_size.x - scale.x, pos.y, top - scale.z), scale))
        else:
          yield (row, row_size)
          top -= row_size.y + pic_margin
          row = [(pic, Vec3(scale.x, pos.y, top - scale.z), scale)]
          row_size = Vec2(scale.x, scale.z) * 2
      yield (row, row_size)
    
    wall_aspect = (2 - pic_strip_width * 2) / (self.wall_top * pic_height_ratio)
    rows = round(sqrt(one_row_width / (average_height * wall_aspect)))

    total_width = 0
    total_height = 0
    for (row, size) in flow(rows):
      total_width = max(size.x, total_width)
      if total_height > 0: total_height += pic_margin
      total_height += size.y
    (width, height) = self.fit_wall(total_width / total_height, pic_strip_width)
    total_scale = min(width / total_width, height / total_height)
    top = height + (self.wall_top - height) / 2
    index = 0
    for (row, row_size) in flow(rows):
      for (pic, pos, scale) in row:
        target_pos = Vec3(
          pos.x * total_scale - row_size.x * total_scale / 2, 
          pos.y, 
          pos.z * total_scale + top - (row_size.y - scale.z * 2) / 2 * total_scale)
        target_scale = Vec3(scale.x * total_scale, scale.y, scale.z * total_scale)
        self.animate_pic(pic, target_pos, target_scale, self.time_between(pos, pic.getPos()))
        index += 1

  def hide_thumbnails(self):
    self.rearrange_pics(True)

  def time_between(self, a, b):
    return 0.3 + log(1 + (a - b).length()) / 5
    
  def fit_wall(self, aspect_ratio, margin):
    height = self.wall_top * pic_height_ratio
    width = height * aspect_ratio
    if width + margin * 2 > 2:
      width = 2 - margin * 2
      height = width / aspect_ratio
    return (width, height)
        
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
