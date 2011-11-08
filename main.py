#!/usr/bin/env ppython
import sys
sys.path.append("./build/pynui")
from os import listdir
from math import *
from time import clock
from sets import Set

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

collision_mask = BitMask32(0x10)

def file_list():
  return [image_path + f for f in sorted(listdir(image_path))]

class App(ShowBase):
  def __init__(self):
    ShowBase.__init__(self)

    base.disableMouse()

    props = WindowProperties()
    props.setCursorHidden(base.win.isFullscreen())
    base.win.requestProperties(props)

    self.win.setClearColor(VBase4(0, 0, 0, 0))

    self.nui = Nui()
    self.nui.smooth_factor = 0.9
    
    self.camLens.setFov(90)
    self.camLens.setNear(0.01)
    self.camLens.setFar(2)
    cam_pos = Vec3(0, -1, 0)
    cam_pos.z = -cam_pos.y * tan(vfov()/2) * (1 - floor_ratio*2)
    self.cam.setPos(cam_pos)

    self.create_label_texture()

    self.picsNode = render.attachNewNode("Pics")

    self.create_wall()
    self.create_floor()
    self.create_url_overlay()

    self.loaded_files = Set()
    
    before = clock()
    print "Loading", len(file_list()), "files..."
    for file in file_list():
      self.load_file(file)
    self.picsNode.prepareScene(base.win.getGsg())
    print "Loaded in", str(clock() - before) + "s"

    self.selection = 0

    for (pic, pos, scale) in self.pics_pos_scale():
      pic.setScale(scale)
      pic.setPos(pos)

    self.cursor = Cursor(self)
    self.cursor_user = None
    
    base.cTrav = CollisionTraverser('CollisionTraverser')    
    pickerNode = CollisionNode('cursor')
    pickerNode.setFromCollideMask(collision_mask)
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

    self.hand_tracker = HandTracker()
    states.Start()

    self.last_look_for_new_file = 0

    self.thumbnail_layout = None

  def load_file(self, file):
    self.loaded_files.add(file)
    try:
         texture = loader.loadTexture(file)
    except:
      return
    texture.setMinfilter(Texture.FTLinearMipmapLinear)
    texture.setWrapU(Texture.WMClamp)
    texture.setWrapV(Texture.WMClamp)
    
    maker = CardMaker('pic')
    maker.setFrame(-1, 1, -1, 1)
    pic = self.picsNode.attachNewNode(maker.generate())
    pic.setTransparency(TransparencyAttrib.MAlpha, 1)
    pic.setTexture(texture)
    pic.setCollideMask(collision_mask)
    return pic

  def look_for_new_file(self):
    pic = None
    for file in file_list():
      if file not in self.loaded_files:
        print 'Loading new image ', file
        pic = self.load_file(file)
        (pic, pos, scale) = self.pics_pos_scale()[-1]
        pic.setScale(scale)
        pic.setPos(pos + Vec3(1,0,0))
        break

  def update(self, task):
    self.nui.update()
    self.label_texture.setRamMipmapPointerFromInt(self.nui.label_map, 0, 640*480*4)
    
    self.floor.prepareScene(base.win.getGsg())

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

    if task.time - self.last_look_for_new_file > look_for_files_interval:
      self.last_look_for_new_file = task.time
      self.look_for_new_file()

    return Task.cont

  # Iterate through the default positions and scales of the pictures
  def pics_pos_scale(self):
    items = []
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

      items.append((pic, pos, scale))
      index += 1
    return items

  def animate_pic(self, pic, pos, scale, time):
    name = str(pic.getKey())
    base.taskMgr.remove(name)
    interpolate(name, pic.setPos, cubic_interpolator(pic.getPos(), pos, Vec3()), time)
    interpolate(name, pic.setScale, cubic_interpolator(pic.getScale(), scale, Vec3(0,0,0)), time)

  # Move each picture to its default position based on the current selection
  def rearrange_pics(self, base_time_on_distance = False):
    for (pic, pos, scale) in self.pics_pos_scale():
      time = 0.5 if not base_time_on_distance else self.time_between(pos, pic.getPos())
      self.animate_pic(pic, pos, scale, time)

  def slide(self, direction):
    new_selection = self.selection + direction
    if new_selection < 0 or new_selection >= self.picsNode.getNumChildren():
      return
    self.selection = new_selection
    self.rearrange_pics()

  def arrange_thumbnails(self, user, reflow=True):
    self.cursor.show()
    self.cursor_user = user

    if reflow or not self.thumbnail_layout:
      self.thumbnail_layout = Flow(self.picsNode.getChildren(), 2, self.wall_top, pic_margin, thumbnail_margin)
    for (pic, pos, scale) in self.thumbnail_layout.layout_items:
      pos = Vec3(pos.x, 0, pos.y)
      scale = Vec3(scale.x, 1, scale.y)
      if pic.getPos() != pos or pic.getScale() != scale:
        self.animate_pic(pic, pos, scale, self.time_between(pos, pic.getPos()))
      else:
        base.taskMgr.remove(str(pic.getKey()))

  def arrange_normal(self):
    self.cursor_user = None
    self.rearrange_pics(True)

  def index_of_pic(self, pic):
    index = 0
    for p in self.picsNode.getChildren():
      if p == pic: return index
      index += 1
    return -1
    
  def highlight_pic(self, pic):
    index = self.index_of_pic(pic)
    if index >= len(self.thumbnail_layout.layout_items):
      print "Error: tried to highlight pic not in current thumbnail_layout."
      return
    pos = self.thumbnail_layout.layout_items[index][1]
    pos = Vec3(pos.x, 0, pos.y)
    dir = base.cam.getPos() - pos
    dir.normalize()
    pos += dir * 0.2
    base.taskMgr.remove(str(pic.getKey()))
    interpolate(str(pic.getKey()), pic.setPos, cubic_interpolator(pic.getPos(), pos, Vec3()), 0.3)

  def arrow(self)

  def select_pic(self, pic):
    self.selection = self.index_of_pic(pic)

  def time_between(self, a, b):
    return min(2, 0.2 + log(1 + (a - b).length()) / 5)
    
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
    camera = base.cam.attachNewNode(Camera('shadow'))
    display.setCamera(camera)
    camera.node().setLens(base.camLens)
    camera.node().setScene(self.picsNode)
    camera.setPos(-0.002, 0, 0.002)

    blur_x = make_filter_buffer(buffer, 'blur-x')
    blur = make_filter_buffer(blur_x, 'blur-y')

    wall.setShaderInput('shadow', blur.getTexture())

    texture = loader.loadTexture("resources/wall.png")
    texture.setWrapU(Texture.WMClamp)
    texture.setWrapV(Texture.WMClamp)
    wall.setShaderInput('diffuse', texture)

    wall.setShader(load_shader('wall'))

    wall.setBin('background', 10)
    wall.setDepthWrite(False)

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

    buffer = blur_buffer(buffer)

    maker = CardMaker(name)
    maker.setFrame(-1, 1, -1, 0)
    self.floor = render.attachNewNode(maker.generate())
    self.floor.setShader(load_shader('floor'))
    self.floor.setShaderInput('reflection_tex', buffer.getTexture())
    self.floor.setShaderInput('diffuse_tex', loader.loadTexture('resources/floor.jpg'))
    self.floor.setShaderInput('shadow_tex', self.blurred_label_texture)
    self.floor.setMat(Mat4.rotateMat(-90, VBase3.unitX()) * Mat4.translateMat(0, 0, z))

  def create_label_texture(self):
    self.label_texture = Texture()
    self.label_texture.setWrapU(Texture.WMBorderColor)
    self.label_texture.setWrapV(Texture.WMBorderColor)
    self.label_texture.setBorderColor(VBase4())
    self.label_texture.setCompression(Texture.CMOff)
    self.label_texture.setup2dTexture(640, 480, Texture.TUnsignedByte, Texture.FRgba8)
    self.label_texture.makeRamImage()

    buffer = base.win.makeTextureBuffer('labels', 640, 480)
    buffer.setClearColor(Vec4(0,0,0,0))
    camera = base.makeCamera2d(buffer)
    
    maker = CardMaker('labels')
    maker.setFrameFullscreenQuad()
    card = NodePath(maker.generate())
    card.setTexture(self.label_texture)
    camera.node().setScene(card)

    for i in range(5):
      buffer = blur_buffer(buffer)

    self.blurred_label_texture = buffer.getTexture()

  def create_url_overlay(self):
    texture = loader.loadTexture('resources/url.png')
    maker = CardMaker('')
    width = texture.getXSize() * 2.0 / 1920
    ratio = texture.getXSize() * 1.0 / texture.getYSize()
    maker.setFrame(1 - width, 1, -1, -1 + width/ratio*base.camLens.getAspectRatio())
    node = render2d.attachNewNode(maker.generate())
    node.setTransparency(TransparencyAttrib.MAlpha, 1)
    node.setTexture(texture)

if __name__ == '__main__':
  loadPrcFile("local-config.prc")
  app = App()
  app.run()
