from panda3d.core import *
from direct.task import Task
from direct.showbase.DirectObject import DirectObject
from app.helper import *
from math import *

class Thumbs(DirectObject):
  CollisionMask = BitMask32(0x10)

  def __init__(self):
    self.start_task = PythonTask(self.start_interaction, 'ThumbsStartInteraction')
    self.start_task.setDelay(1)
    self.stop_task = PythonTask(self.stop_interaction, 'ThumbsStopInteraction')
    self.stop_task.setDelay(1)

    self.node = render.attachNewNode('Thumbs')
    self.node.setTransparency(TransparencyAttrib.MAlpha, 1)
    self.node.setSa(0)
    
    self.accept('cursor-into-thumb', self.cursor_into)
    self.accept('cursor-out-thumb', self.cursor_out)

    self.index = {}

    self.interacting = False
    self.hover_thumb = None

  def add(self, texture):
    stride = 2.05
    frameRatio = base.camLens.getAspectRatio()
    textureRatio = texture.getOrigFileXSize() * 1.0 / texture.getOrigFileYSize()
    thumb = create_card(-1, 1, -1/frameRatio, 1/frameRatio, textureRatio, 'thumb')
    self.index[thumb] = self.node.getNumChildren()
    thumb.setTexture(texture)
    thumb.setPos(self.node.getNumChildren() * stride, 0, 0);
    thumb.setCollideMask(Thumbs.CollisionMask)
    thumb.reparentTo(self.node)
    thumb.setTransparency(TransparencyAttrib.MAlpha, 1)
    thumb.setShader(load_shader('image'))

    scale = min(2/(self.node.getNumChildren() * stride), 0.1)
    self.node.setScale(scale)
    count = self.node.getNumChildren()
    self.node.setPos(-scale * count, 0, base.top() * (1 - scale))

  def fade(self, to, time=0.5):
    base.taskMgr.remove('thumbs-fade')
    cubic_interpolate('thumbs-fade', self.node.setSa, self.node.getSa(), to, time=time)
  
  def cursor_into(self, entry):
    base.taskMgr.remove(self.stop_task)
    self.hover_thumb = entry.getIntoNodePath()
    if not self.interacting:
      base.taskMgr.remove(self.start_task)
      base.taskMgr.add(self.start_task)
    else:
      self.goto(self.hover_thumb)

  def cursor_out(self, entry):
    self.hover_thumb = None
    base.taskMgr.remove(self.stop_task)
    base.taskMgr.add(self.stop_task)

  def start_interaction(self, task):
    self.interacting = True
    self.goto(self.hover_thumb)

  def stop_interaction(self, task):
    self.interacting = False
    self.updateThumbs();

  def goto(self, thumb):
    self.updateThumbs();
    if thumb:
      messenger.send('goto-item', [self.index[thumb]])

  def updateThumbs(self):
    taskName = 'thumbs-highlight'
    base.taskMgr.remove(taskName)
    for thumb in self.node.getChildren():
      selected = self.interacting and thumb == self.hover_thumb
      targetScale = 1.2 if selected else 1
      if targetScale != thumb.getScale().x:
        cubic_interpolate(taskName, thumb.setScale, thumb.getScale().x, targetScale, time=0.2)
      pos = thumb.getPos()
      pos.y = -0.01 if selected else 0
      thumb.setPos(pos)
