from attr import attr, attributes, Factory
from typing import List
from enum import Enum, auto
import operator
from moo_opcodes import opcodes

class ExecutionResult(Enum):
  RETURN = auto()
  RAISE = auto()
  CALL = auto()
  SUSPEND = auto()
  KILL = auto()

@attributes
class VM:
  stack: List = attr(default=Factory(list))
  pc: int = attr(default=0)
  code: List = attr(default=Factory(list), repr=False)
  constants: List = attr(default=Factory(list))
  return_value = attr(default=0)

  def push(self, what):
    self.stack.append(what)

  def pop(self):
    return self.stack.pop()

  def push_constant(self, value):
    self.constants.append(value)
    address = len(self.constants) - 1
    self.push(address)


  def read_bytes(self, amount=1):
    new_pc = self.pc + amount
    if new_pc > len(self.code) - 1:
      return []
    result = self.code[self.pc:new_pc]
    self.pc = new_pc
    return result

  def read_byte(self):
    res = self.read_bytes()
    if res:
      return res[0]

  def run(self, opcodes: List) -> ExecutionResult:
    self.reset()
    self.code = opcodes
    while opcode := self.read_byte():
      print(self)
      self.dispatch_opcode(opcode)
    print(self)

  def reset(self):
    self.stack.clear()
    self.pc = 0

  def dispatch_opcode(self, opcode):
    name = opcode.name.lower()
    func_name = 'do_' + name
    handler = getattr(self, func_name, None)
    if not callable(handler):
      raise NotImplementedError("No handler for opcode %r" % name)
    handler()

  def do_test(self):
    cond = self.pop()

  def jump(self, label):
    pass

  def do_map_create(self):
    new_map = dict()
    self.push(new_map)

  def do_map_insert(self):
    key = self.pop()
    value = self.pop()
    map = self.pop()

  def do_add(self):
    rhs = self.pop()
    lhs = self.pop()
    ans = lhs + rhs
    self.push(ans)

  def do_binary_op(self, operator):
    rhs = self.pop()
    lhs = self.pop()
    self.push(operator(lhs, rhs))

  do_minus = lambda self: self.do_binary_op(operator.sub)

  do_mult = lambda self: self.do_binary_op(operator.mul)

  do_mod = lambda self: self.do_binary_op(operator.mod)

  def do_pop(self):
    self.pop()

  def do_imm(self):
    constant = self.read_byte()
    self.push(constant)

  def do_return(self):
    ret_val = self.pop()
    self.return_value = ret_val

  def do_return_0(self):
    pass

  do_done = do_return_0
