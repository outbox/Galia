from panda3d.core import *
from pynui import *

class Cursor:
  def __init__(self, app):
    size = 0.2
    maker = CardMaker("")
    maker.setFrame(-size/2, size/2, -size, 0)

    def texture(file):
      t = loader.loadTexture(file)
      t.setWrapU(Texture.WMBorderColor)
      t.setWrapV(Texture.WMBorderColor)
      t.setBorderColor(VBase4())
      return t
    self.texture = texture("resources/hand.png")
    self.drag_texture = texture("resources/hand-drag.png")

    self.node = NodePath(maker.generate())
    self.node.setTexture(self.texture)
    self.node.setTransparency(TransparencyAttrib.MAlpha, 1)
    self.node.setTwoSided(True)
    self.node.reparentTo(app.render)
    self.node.hide()

    # Always draw cursor on top
    self.node.setBin("fixed", 30)
    self.node.setDepthWrite(False)
    self.node.setDepthTest(False)

  def set_side(self, side):
    self.node.setScale(1 if side == Skeleton.right else -1, 1, 1)

  def set_drag(self, drag):
    self.node.setTexture(self.drag_texture if drag else self.texture)
