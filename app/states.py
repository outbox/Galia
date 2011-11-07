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
    def lost_user(u):
      if u == user: 
        self.lost_user()
        self.next_state(Start())
    self.accept('lost-user', lost_user)

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
    self.accept('space', self.thumbnails)
  
  def hand_in(self, hand):
    self.next_state(Slide(hand, 1))

  def thumbnails(self):
    self.next_state(Thumbnails(999))

class Slide(UserState):
  def __init__(self, hand, time):
    UserState.__init__(self, hand.user)
    self.hand = hand
    self.timer(time, self.timeout)
    messenger.send('slide', [hand.side_sign])

  def hand_in(self, hand):
    if hand.side != self.hand.side and hand.user == self.hand.user:
      self.next_state(Thumbnails(self.hand.user))

  def timeout(self):
    self.next_state(Slide(self.hand, 0.5))
  
  def hand_out(self, hand):
    if hand.user_side == self.hand.user_side:
      self.next_state(Start())

class Thumbnails(UserState):
  def __init__(self, user):
    UserState.__init__(self, user)
    messenger.send('show-thumbnails', [user])
    
    self.accept('cursor-into-pic', self.cursor_into_pic)
    self.accept('cursor-again-pic', self.cursor_into_pic)

  def cursor_into_pic(self, entry):
    pic = entry.getIntoNodePath()
    if base.taskMgr.hasTaskNamed(str(pic.getKey())): return
    self.next_state(ThumbnailHover(self.user, pic))
  
  def lost_user(self):
    messenger.send('hide-thumbnails')

class ThumbnailHover(UserState):
  def __init__(self, user, pic):
    UserState.__init__(self, user)
    self.pic = pic
    messenger.send('highlight-pic', [pic])
    messenger.send('cursor-play-timer')
    self.accept('cursor-out-pic', self.cursor_out)
    self.accept('cursor-timer-end', self.timer_end)

  def cursor_out(self, entry):
    if self.pic != entry.getIntoNodePath(): return
    messenger.send('cursor-cancel-timer')
    self.next_state(Thumbnails(self.user))

  def timer_end(self):
    messenger.send('select-pic', [self.pic])
    messenger.send('hide-thumbnails')
    self.next_state(Start())

  def lost_user(self):
    messenger.send('hide-thumbnails')
    messenger.send('cursor-cancel-timer')
