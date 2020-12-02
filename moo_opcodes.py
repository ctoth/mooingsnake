from enum import Enum, auto

class opcodes(Enum):
  #control/statement constructs with 1 tick:
  IF = 0
  WHILE = auto()
  EIF = auto()
  FORK = auto()
  FORK_WITH_ID = auto()
  FOR_LIST = auto() # retired
  FOR_RANGE = auto()
  # expr-related opcodes with 1 tick:
  INDEX_SET = auto()
  PUSH_GET_PROP = auto()
  GET_PROP = auto()
  CALL_VERB = auto()
  PUT_PROP = auto()
  BI_FUNC_CALL = auto()
  IF_QUES = auto()
  REF = auto()
  RANGE_REF = auto()
  # arglist-related opcodes with 1 tick:
  MAKE_SINGLETON_LIST = auto()
  CHECK_LIST_FOR_SPLICE = auto()
  #arith binary ops -- 1 tick:
  MULT = auto()
  DIV = auto()
  MOD = auto()
  ADD = auto()
  MINUS = auto()
  # comparison binary ops -- 1 tick::
  EQ = auto()
  NE = auto()
  LT = auto()
  LE = auto()
  GT = auto()
  GE = auto()
  IN = auto()
  # logic binary ops -- 1 tick:
  AND = auto()
  OR = auto()
  # unary ops -- 1 tick:
  UNARY_MINUS = auto()
  NOT = auto()
  # assignments, 1 tick:
  PUT = NOT + 33
  PUSH = PUT + 33
  PUSH_CLEAR = PUSH + 33
  IMM = auto()
  MAKE_EMPTY_LIST = auto()
  LIST_ADD_TAIL = auto()
  list_append = auto()
  PUSH_REF = auto()
  PUT_TEMP = auto()
  PUSH_TEMP = auto()
  # control/statement constructs with no ticks:
  JUMP = auto()
  RETURN = auto()
  RETURN_0 = auto()
  DONE = auto()
  POP = auto()
  EXTENDED = auto()
  MAP_CREATE = auto()
  map_insert = auto()
