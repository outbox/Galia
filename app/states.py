from panda3d.core import *
from direct.task import Task
from direct.showbase.DirectObject import DirectObject

# Helper stuff

class State(DirectObject):
  def __init__(self):
    self.tasks = []

  def next_state(self, state):
    for task in self.tasks:
      base.taskMgr.remove(task)
    self.ignoreAll();
    print 'New state:', state

  def timer(self, time, function):
    self.tasks.append(base.taskMgr.doMethodLater(time, function, 'state timer', extraArgs=[]))

class UserState(State):
  def __init__(self, user):
    State.__init__(self)
    self.user = user
    self.accept('hand-move', self.hand_move)
    self.accept('lost-hand', self.lost_hand)
  
  def lost_hand(self, hand):
    if self.user == hand.user:
      self.lost_user()
      self.next_state(Start())

  def hand_move(self, hand):
    if self.user is None or hand.user == self.user:
      if hand.positions[-1].x * hand.side_sign > 0.35:
        self.hand_in(hand)
      elif hand.positions[-1].x * hand.side_sign < 0.25:
        self.hand_out(hand)

  def lost_user(self):
    pass

  def hand_in(self, hand):
    pass

  def hand_out(self, hand):
    pass


# State classes

class Start(UserState):
  def __init__(self):
    UserState.__init__(self, None)
  
  def hand_in(self, hand):
    self.next_state(OneHandWait(hand))

class OneHandWait(UserState):
  def __init__(self, hand):
    UserState.__init__(self, hand.user)
    self.hand = hand
    self.timer(0.2, self.timeout)
  
  def timeout(self):
    self.next_state(SlideOne(self.hand))
  
  def hand_in(self, hand):
    if hand != self.hand and hand.user == self.hand.user:
      self.next_state(Thumbnails(self.hand.user))

  def hand_out(self, hand):
    if hand == self.hand:
      self.next_state(Start())

class SlideOne(UserState):
  def __init__(self, hand):
    UserState.__init__(self, hand.user)
    self.hand = hand
    self.timer(1, self.timeout)
    messenger.send('slide', [hand.side_sign])

  def timeout(self):
    self.next_state(SlideRepeat(self.hand))
  
  def hand_out(self, hand):
    if hand == self.hand:
      self.next_state(Start())

class SlideRepeat(UserState):
  def __init__(self, hand):
    UserState.__init__(self, hand.user)
    self.hand = hand
    self.timer(0.5, self.timeout)
    messenger.send('slide', [hand.side_sign])

  def timeout(self):
    self.next_state(SlideRepeat(self.hand))

  def hand_out(self, hand):
    if hand == self.hand:
      self.next_state(Start())

class Thumbnails(UserState):
  def __init__(self, user):
    UserState.__init__(self, user)
    self.user = user
    messenger.send('show-thumbnails')

  def lost_user(self):
    messenger.send('hide-thumbnails')

