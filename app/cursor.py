from panda3d.core import *
from pynui import *
from helper import *
from math import *

class Cursor:
  def __init__(self, app):
    size = 0.2
    maker = CardMaker("")
    maker.setFrame(-size/2, size/2, -size/2, size/2)

    def texture(file):
      t = loader.loadTexture(file)
      t.setWrapU(Texture.WMBorderColor)
      t.setWrapV(Texture.WMBorderColor)
      t.setBorderColor(VBase4())
      return t
    self.texture_right = texture('resources/hand-right.png')
    self.texture_left = texture('resources/hand-left.png')
    
    self.node = NodePath(maker.generate())
    self.node.setTexture(self.texture_right)
    self.node.setTransparency(TransparencyAttrib.MAlpha, 1)
    self.node.setTwoSided(True)
    self.node.reparentTo(app.render)
    self.node.hide()
    self.node.setColor(1, 0, 0, 1)

    self.node.setShader(load_shader('cursor'))
    self.node.setShaderInput('timer_tex', texture('resources/hand-timer.png'))
    
    # Always draw cursor on top
    self.node.setBin('fixed', 50)
    self.node.setDepthWrite(False)
    self.node.setDepthTest(False)

    self.set_timer_time(1)

  def set_alpha(self, alpha):
    self.node.setColor(1,1,1,alpha)

  def show(self):
    self.node.show()
    self.set_alpha(0)
    base.taskMgr.remove('cursor-show')
    interpolate('cursor-show', self.set_alpha, lambda t: t, 0.2)

  def hide(self):
    self.set_alpha(1)
    base.taskMgr.remove('cursor-show')
    interpolate('cursor-show', self.set_alpha, lambda t: 1-t, 0.25, on_done=self.node.hide)

  def set_side(self, side):
    self.node.setTexture(self.texture_right if side == Skeleton.right else self.texture_left)

  def play_timer(self, length):
    length = length * 1.28 # extra time for the timer to disappear with animation
    interpolate('cursor-timer', self.set_timer_time, lambda t: t, length)
    base.taskMgr.doMethodLater(length - 0.25, self.hide, 'cursor-timer', extraArgs=[])
    
  def cancel_timer(self):
    base.taskMgr.remove('cursor-timer')
    self.set_alpha(1)
    self.set_timer_time(1)

  def set_timer_time(self, time):
    x_frames, y_frames = 8, 8
    frame = round(time * (x_frames * y_frames - 1))
    x = frame % y_frames * 1.0 / x_frames
    y = (y_frames - frame // y_frames - 1) * 1.0 / y_frames
    self.node.setShaderInput('timer_frame', Vec4(x, y, 1.0 / x_frames, 1.0 / y_frames))
