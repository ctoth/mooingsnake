from attr import attr, attributes, Factory
from abc import abstractmethod
import lark
import typing

def parse(code):
  import moo_parser
  parse_tree = moo_parser.parser.parse(code)
  return build_ast(parse_tree)

def build_ast(parse_tree, current_node=None):
  if isinstance(parse_tree, lark.Token):
    transformer = TOKEN_TRANSFORMERS.get(parse_tree.type)
    if transformer:
      current_node = transformer(value=parse_tree.value)
    else:
      raise ValueError("Unknown token type " + parse_tree.type)
    return current_node
  if current_node == None and parse_tree.data == 'start':
    current_node = Verb()
    for child in parse_tree.children:
      current_node.body.append(build_ast(child, current_node))
    return current_node
  if parse_tree.data in ('expression', "statement", "flow_statement") and len(parse_tree.children) == 1:
    return build_ast(parse_tree.children[0], current_node)
  node_type = NODE_BUILDERS.get(parse_tree.data)
  if callable(node_type):
    current_node = node_type.build_from_parse_tree(parse_tree.children)
  else:
    raise ValueError("Unknown node type " + parse_tree.data)
  return current_node

@attributes(auto_attribs=True, slots=True)
class ASTNode:

  @classmethod
  @abstractmethod
  def build_from_parse_tree(cls, children: typing.List):
    pass

@attributes(auto_attribs=True, slots=True)
class ASTValueNode(ASTNode):

  def evaluate(self):
    return this.value

@attributes(auto_attribs=True, slots=True)
class Int(ASTValueNode):
  value: int = attr(default=0, converter=int)

@attributes(auto_attribs=True, slots=True)
class Float(ASTValueNode):
  value: float = attr(default=0.0, converter=float)

@attributes(auto_attribs=True, slots=True)
class ObjNum(ASTValueNode):
  value: float = attr(default=-1)

@attributes(auto_attribs=True, slots=True)
class List(ASTValueNode):
  value: tuple = attr(default=())

@attributes(auto_attribs=True, slots=True)
class String(ASTValueNode):
  value: str = attr(default='', converter=str)

@attributes(auto_attribs=True, slots=True)
class Map(ASTValueNode):
  value: dict = attr(default={})

@attributes(auto_attribs=True, slots=True)
class Variable(ASTNode):
  name: str = attr(default='')

  @classmethod
  def build_from_parse_tree(cls, children):
    node = cls()
    node.name = build_ast(children[0], node)
    return node

@attributes(auto_attribs=True, slots=True)
class VerbCall(ASTNode):
  obj: ASTNode = Factory(ASTNode)
  verb: str = attr(default="")
  args: typing.Tuple[ASTNode] = Factory(tuple)

  @classmethod
  def build_from_parse_tree(cls, children):
    node = cls()
    node.obj = build_ast(children[0], node)
    verb = children[1]
    verb = String(value=verb.value)
    node.verb = verb
    args = children[2].children
    node.args = tuple([build_ast(arg, node) for arg in args])
    return node

@attributes(auto_attribs=True, slots=True)
class FunctionCall(ASTNode):
  function: str = attr(default="")
  args: typing.Tuple[ASTNode] = Factory(tuple)

  @classmethod
  def build_from_parse_tree(cls, children):
    node = cls()
    node.function = build_ast(children[0], node)
    args = children[1].children
    node.args = tuple([build_ast(arg, node) for arg in args])
    return node

@attributes(auto_attribs=True, slots=True)
class Return(ASTNode):
  value: ASTNode = Factory(ASTNode)

  @classmethod
  def build_from_parse_tree(cls, children):
    node = cls()
    node.value = build_ast(children[0], node)
    return node

@attributes(auto_attribs=True, slots=True)
class If(ASTNode):
  condition: ASTNode = Factory(ASTNode)
  body: typing.List['ASTNode'] = Factory(list)

  @classmethod
  def build_from_parse_tree(cls, children):
    node = cls()
    node.condition = build_ast(children[0], node)
    for child in children[1].children:
      node.body.append(build_ast(child, node))
    return node

@attributes(auto_attribs=True, slots=True)
class Comparison(ASTNode):
  condition1: ASTNode = Factory(ASTNode)
  operator: str = attr(default='')
  condition2: ASTNode = Factory(ASTNode)

  @classmethod
  def build_from_parse_tree(cls, children):
    node = cls()
    node.condition1 = build_ast(children[0], node)
    node.operator = children[1].value
    node.condition2 = build_ast(children[2], node)
    return node

@attributes(auto_attribs=True, slots=True)
class Assign(ASTNode):
  lhs: ASTNode = Factory(ASTNode)
  rhs: ASTNode = Factory(ASTNode)

  @classmethod
  def build_from_parse_tree(cls, children):
    node = cls()
    node.lhs= build_ast(children[0], node)
    node.rhs = build_ast(children[1], node)
    return node

@attributes(auto_attribs=True, slots=True)
class ScatterAssign(ASTNode):
  lhs: typing.List[ASTNode] = Factory(list)
  rhs: ASTNode = Factory(ASTNode)

  @classmethod
  def build_from_parse_tree(cls, children):
    node = cls()
    node.lhs = build_ast(children[0], node)
    node.rhs = build_ast(children[1], node)
    return node

@attributes(auto_attribs=True, slots=True)
class Verb(ASTNode):
  body: typing.List['ASTNode'] = Factory(list)

TOKEN_TRANSFORMERS = {
  'SIGNED_INT': Int,
  'ESCAPED_STRING': String,
  'OBJ_NUM': ObjNum,
  'VAR': lambda value: Variable(name=value),
}

NODE_BUILDERS = {
  'if': If,
  'comparison': Comparison,
  'assignment': Assign,
  'return': Return,
  'function_call': FunctionCall,
  'verb_call': VerbCall,
  'scatter_assignment': ScatterAssign,
}
