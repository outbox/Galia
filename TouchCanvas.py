from time import clock

import sys
sys.path.append("./build/pynui")
from pynui import *

from panda3d.core import *

def lerp(a, b, t):
  return a * (1 - t) + b * t

class Touch:
  def __init__(self, user_side, pos):
    self.positions = []
    self.speeds = []
    self.time = []
    self.append(pos)
    self.user_side = user_side
    self.speed_smooth = 0.9

  def append(self, pos):
    self.positions.append(pos)
    self.time.append(clock())
    if len(self.positions) >= 2:
      speed = (self.positions[-1] - self.positions[-2]) / (self.time[-1] - self.time[-2])
      self.speeds.append(lerp(speed, self.speeds[-1], self.speed_smooth))
    else:
      self.speeds.append(Vec3())

class TouchCanvas:
  def __init__(self):
    self.touch_down = None
    self.touch_move = None
    self.touch_up = None
    self.cursor_appear = None
    self.cursor_move = None
    self.cursor_disappear = None
    self.touches = {}
    self.size = Vec2(0.25, 0.25)
    self.origin = Vec3(0, 0, -0.35)
    self.cursor = None
    self.shoulders = {}
    self.hands = {}
    
  def update(self, users):
    self.hands = {}
    for (user, skel) in users.items():
      self.update_user_side(user, skel, Skeleton.right)
      self.update_user_side(user, skel, Skeleton.left)

    def valid_cursor(user_side):
      return user_side in self.hands and self.hands[user_side].y > -1
    
    if not valid_cursor(self.cursor):
      if not self.cursor is None:
        self.cursor_disappear and self.cursor_disappear()
      self.cursor = None
      for (user_side, hand) in self.hands.items():
        if valid_cursor(user_side):
          self.cursor_appear and self.cursor_appear()
          self.cursor = user_side
          break

    if self.cursor:
      pos = self.hands[self.cursor]
      self.cursor_move and self.cursor_move(pos, self.cursor[0], self.cursor[1])
      
  def update_user_side(self, user, skel, side):
    skel_side = side.__get__(skel)

    if not skel_side.shoulder.valid or not skel_side.hand.valid:
      if (user, side) in self.shoulders: del self.shoulders[user, side]
      if (user, side) in self.hands: del self.hands[user, side]
      return
    
    old_shoulder = self.shoulders.get((user, side), None)
    shoulder = skel_side.shoulder.position
    shoulder = lerp(shoulder, old_shoulder, 0.9) if old_shoulder else shoulder
    self.shoulders[user, side] = shoulder

    hand =  skel_side.hand.position - (shoulder + self.origin)
    hand.x /= self.size.x
    hand.y /= self.size.y
    self.hands[user, side] = hand

    existing_touch = self.touches.get((user, side), None)

    if hand.z > 0:
      if existing_touch:
        del self.touches[user, side]
        self.touch_up and self.touch_up(existing_touch)
    else:
      if existing_touch:
        existing_touch.append(hand)
        self.touch_move and self.touch_move(existing_touch)
      else:
        touch = Touch((user, side), hand)
        self.touches[user, side] = touch
        self.touch_down and self.touch_down(touch)
