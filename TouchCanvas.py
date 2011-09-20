from time import clock

import sys
sys.path.append("./build/pynui")
from pynui import *

from panda3d.core import *

class Touch(object):
  def __init__(self, user, side, pos):
    self.positions = []
    self.smooth_positions = []
    self.time = []
    self.append(pos)
    self.user = user
    self.side = side
    self.smooth_factor = 0.5

  def append(self, pos):
    self.positions.append(pos)
    self.time.append(clock())
    if len(self.smooth_positions) > 0:
      self.smooth_positions.append(pos * (1 - self.smooth_factor) + self.smooth_positions[-1] * self.smooth_factor)
    else:
      self.smooth_positions.append(pos)

class TouchCanvas:
  def __init__(self):
    self.touch_down = None
    self.touch_move = None
    self.touch_up = None
    self.touches = []
    self.size = Vec2(0.8, 0.8*9/16)
    self.origin = Vec3(0, 0, -0.35)

  def update(self, users):
    for (user, skel) in users.items():
      self.update_user_side(user, skel, Skeleton.right)
      self.update_user_side(user, skel, Skeleton.left)

  def update_user_side(self, user, skel, side):
    camera_pos = side.__get__(skel).hand.position
    canvas_pos = camera_pos - (skel.neck.position + self.origin)
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
