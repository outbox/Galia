from time import clock
from pynui import *
from helper import *
from panda3d.core import *

class Hand(object):
  def __init__(self, user_side, pos):
    self.positions = []
    self.speeds = []
    self.time = []
    self.append(pos)
    self.user_side = user_side
    self.speed_smooth = 0.9
    self.grab = False
    self.generation = 0

  def append(self, pos):
    self.positions.append(pos)
    self.time.append(clock())
    if len(self.positions) >= 2:
      speed = (self.positions[-1] - self.positions[-2]) / (self.time[-1] - self.time[-2])
      self.speeds.append(lerp(speed, self.speeds[-1], self.speed_smooth))
    else:
      self.speeds.append(Vec3())

class HandTracker:
  def __init__(self):
    self.size = Vec2(0.25, 0.25)
    self.origin = Vec3(0, 0, -0.35)
    self.shoulders = {}
    self.hands = {}
    self.generation = 0
    
  def update(self, users):
    self.generation += 1

    for (user, skel) in users.items():
      self.update_user_side(user, skel, Skeleton.right)
      self.update_user_side(user, skel, Skeleton.left)
    
    for (user_side, hand) in self.hands.items():
      if hand.generation != self.generation:
        del self.hands[user_side]
        del self.shoulders[user_side]
        if hand.grab: messenger.send('hand-grab-end', [hand])
        messenger.send('lost-hand', [hand])

  def update_user_side(self, user, skel, side):
    skel_side = side.__get__(skel)

    if not skel_side.shoulder.valid or not skel_side.hand.valid:
      return
    
    old_shoulder = self.shoulders.get((user, side), None)
    shoulder = skel_side.shoulder.position
    if old_shoulder: shoulder = lerp(shoulder, old_shoulder, 0.9)
    self.shoulders[user, side] = shoulder

    pos =  skel_side.hand.position - (shoulder + self.origin)
    pos.x /= self.size.x
    pos.y /= self.size.y

    if pos.y < -1: return

    hand = self.hands.get((user, side), None)
    if not hand:
      hand = Hand((user, side), pos)
      self.hands[user, side] = hand
      messenger.send('new-hand', [hand])
    else:
      hand.append(pos)
      if hand.positions[-1] != hand.positions[-2]:
        messenger.send('hand-move', [hand])

    hand.generation = self.generation

    if pos.z > 0 and hand.grab:
      hand.grab = False
      messenger.send('hand-grab-end', [hand])
    elif pos.z <= 0 and not hand.grab:
      hand.grab = True
      messenger.send('hand-grab-start', [hand])