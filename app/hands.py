from time import clock
from pynui import *
from helper import *
from panda3d.core import *
from math import *

class Hand(object):
  def __init__(self, user_side, pos):
    self.positions = []
    self.speeds = []
    self.time = []
    self.append(pos)
    self.user_side = user_side
    self.speed_smooth = 0.9
    self.generation = 0

  def append(self, pos):
    self.positions.append(pos)
    self.time.append(clock())
    if len(self.positions) >= 2:
      speed = (self.positions[-1] - self.positions[-2]) / (self.time[-1] - self.time[-2])
      self.speeds.append(lerp(speed, self.speeds[-1], self.speed_smooth))
    else:
      self.speeds.append(Vec3())

  @property
  def side_sign(self):
    return 1 if self.user_side[1] == Skeleton.right else -1

  @property
  def user(self):
    return self.user_side[0]

  @property
  def side(self):
    return self.user_side[1]

  @property
  def position(self):
    return self.positions[-1]

class HandTracker:
  def __init__(self):
    self.origin = Vec3(0, 0, -0.35)
    self.shoulders = {}
    self.hands = {}
    self.generation = 0

  def update(self, users):
    self.generation += 1

    for (user, skel) in users.items():
      if self.valid_user(skel):
        self.update_user_side(user, skel, Skeleton.right)
        self.update_user_side(user, skel, Skeleton.left)
    
    mouse = base.mouseWatcherNode
    if mouse.hasMouse() and not (mouse.getMouseX() == -1 and mouse.getMouseY() == 1):
      pos = Vec3(mouse.getMouseX(), mouse.getMouseY(), 0)
      self.create_or_update_hand(999, Skeleton.left if pos.x < 0 else Skeleton.right, pos)
      
    for (user_side, hand) in self.hands.items():
      if hand.generation != self.generation:
        del self.hands[user_side]
        if user_side in self.shoulders: del self.shoulders[user_side]
        messenger.send('lost-hand', [hand])
        if (hand.user, Skeleton.right) not in self.hands \
        and (hand.user, Skeleton.left) not in self.hands:
          messenger.send('lost-user', [hand.user])

  def valid_user(self, skel):
    if all([
    skel.right.shoulder.valid,
    skel.left.shoulder.valid,
    skel.right.hand.valid or skel.left.hand.valid]):
      right = skel.right.shoulder.position - skel.left.shoulder.position
      forward = Vec3(-right.z, 0, right.x)
      forward.normalize()
      return forward.dot(VBase3.unitZ()) > cos(pi/4)
    return False

  def update_user_side(self, user, skel, side):
    skel_side = side.__get__(skel)

    if not skel_side.shoulder.valid or not skel_side.hand.valid:
      return
    
    old_shoulder = self.shoulders.get((user, side), None)
    shoulder = skel_side.shoulder.position
    if old_shoulder: shoulder = lerp(shoulder, old_shoulder, 0.9)
    self.shoulders[user, side] = shoulder

    pos =  skel_side.hand.position - (shoulder + self.origin)
    
    self.create_or_update_hand(user, side, pos)

  def create_or_update_hand(self, user, side, pos):
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
