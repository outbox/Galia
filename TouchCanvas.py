from time import clock

import sys
sys.path.append("./build/pynui")
from pynui import *

from panda3d.core import *

def lerp(a, b, t):
  return a * (1 - t) + b * t

class Touch(object):
  def __init__(self, user, side, pos):
    self.positions = []
    self.speeds = []
    self.time = []
    self.append(pos)
    self.user = user
    self.side = side
    self.speed_smooth = 0.9

  def append(self, pos):
    self.positions.append(pos)
    self.time.append(clock())
    if len(self.positions) >= 2:
      speed = (self.positions[-1] - self.positions[-2]) / (self.time[-1] - self.time[-2])
      self.speeds.append(lerp(speed, self.speeds[-1], self.speed_smooth))
    else:
      self.speeds.append(Vec2())

class TouchCanvas:
  def __init__(self):
    self.touch_down = None
    self.touch_move = None
    self.touch_up = None
    self.touches = []
    self.size = Vec2(0.25, 0.25*9/16)
    self.origin = Vec3(0, 0, -0.35)
    
  def update(self, users):
    for (user, skel) in users.items():
      self.update_user_side(user, skel, Skeleton.right)
      self.update_user_side(user, skel, Skeleton.left)

  def update_user_side(self, user, skel, side):
    skel_side = side.__get__(skel)
    canvas_pos = skel_side.hand.position - (skel_side.shoulder.position + self.origin)
    normalized_pos = Vec2(canvas_pos.x / self.size.x, canvas_pos.y / self.size.y)

    touches = [t for t in self.touches if t.user == user and t.side == side]
    existing_touch = touches[0] if len(touches) > 0 else None

    if canvas_pos.z > 0:
      if existing_touch:
        self.touches.remove(existing_touch)
        self.touch_up and self.touch_up(existing_touch)
    else:
      if existing_touch:
        existing_touch.append(normalized_pos)
        self.touch_move and self.touch_move(existing_touch)
      else:
        touch = Touch(user, side, normalized_pos)
        self.touches.append(touch)
        self.touch_down and self.touch_down(touch)
