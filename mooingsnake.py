import argparse
import astroid
import io
import os
import pdb
import sys
import importlib

import logging
from logging import getLogger
logger = getLogger("Transpiler")
from attr import attr, attributes, Factory

logger = getLogger("Transpiler")
logger.addHandler(logging.StreamHandler())

DEFAULT_VERB_ARGS = 'tnt'
DEFAULT_VERB_PERMS = 'RXD'
transformations_table = {
  'self': 'this',
  'str': 'tostr',
  'float': 'tofloat',
  'int': 'toint',
  'len': 'length',
  'print': 'player:tell',
  'TypeError': 'E_TYPE',
  'sum': '$math_utils:sum',
}

def load_ast(fname):
  with open(fname, encoding='UTF-8') as f:
    code = f.read()
  return astroid.parse(code)

@attributes
class Context:
  current_obj = attr(default=None)
  verb = attr(default=None)
  in_function_call = attr(default=False)


@attributes
class PythonToMoo:
  output = attr()
  context = attr(default=Factory(Context))
  debug = attr(default=False)

  def __attrs_post_init__(self):
    """Register converters here"""
    self.converters = {
      astroid.ClassDef: self.convert_obj,
      astroid.FunctionDef: self.convert_verb,
      astroid.While: self.convert_while,
      astroid.If: self.convert_if,
      astroid.For: self.convert_for,
      astroid.Break: self.convert_break,
      astroid.Continue: self.convert_continue,
      astroid.node_classes.Const: self.convert_const,
      astroid.node_classes.Compare: self.convert_comparison,
      astroid.Slice: self.convert_slice,
      astroid.Name: self.convert_name,
      astroid.Raise: self.convert_raise,
      astroid.Assign: self.convert_assign,
      astroid.node_classes.AssignName: self.convert_assign_name,
      astroid.AugAssign: self.convert_aug_assign,
      astroid.Expr: self.convert_expr,
      astroid.BinOp: self.convert_bin_op,

      #astroid.Num: self.convert_num,
      astroid.List: self.convert_list,
      astroid.Tuple: self.convert_list,
      astroid.Dict: self.convert_dict,
      astroid.Subscript: self.convert_subscript,
      astroid.BoolOp: self.convert_multi_comparison,
      astroid.Return: self.convert_return,
      astroid.Attribute: self.convert_attribute,
      astroid.AssignAttr: self.convert_attribute,
      astroid.node_classes.Arguments: self.convert_args,
      astroid.Call: self.convert_call,
    }

  def convert_verb(self, node):
    verb_name = node.name
    obj_name = self.context.current_obj
    default_args = DEFAULT_VERB_ARGS
    default_perms = DEFAULT_VERB_PERMS
    self.context.verb = verb_name
    self.write("@verb {obj_name}:{verb_name} {default_args} {default_perms}\n".format(**locals()))
    self.write("@program {obj_name}:{verb_name}\n".format(**locals()))
    self.convert_node(node.args)
    for subnode in node.body:
      self.convert_node(subnode, )
    self.write(".\n")
    self.context.verb = ""

  def convert_obj(self, node):
    class_name = node.name
    self.write("@create #1 named {class_name}\n".format(**locals()))
    self.context.current_obj = class_name
    for subnode in node.body:
      self.convert_node(subnode)

  def convert_scoped_node(self, node, start_token, end_token):
    self.write(start_token + " (")
    self.convert_node(node.test, )
    self.write(")\n")
    for subnode in node.body:
      self.convert_node(subnode, )
    self.write(end_token + "\n")

  def convert_while(self, node):
    if self.context.current_obj is None and self.context.verb is None:
      raise RuntimeError("While loop not supported out of class or function.")
    if self.context.verb is None:
      raise RuntimeError("Loop not supported out of function call.")
    self.convert_scoped_node(node, "while", "endwhile")

  def convert_if(self, node):
    if self.context.current_obj is None and self.context.verb is None:
      raise RuntimeError("If statement not supported out of class or function.")
    if self.context.verb is None:
      raise RuntimeError("If not supported out of function call.")
    self.convert_scoped_node(node, "if", "endif")

  def convert_for(self, node):
    if self.context.current_obj is None and self.context.verb is None:
      raise RuntimeError("for loop not supported out of class or function.")
    if self.context.verb is None:
      raise RuntimeError("For loop not supported out of function call.")
    self.write("for ")
    self.convert_node(node.target)
    self.write(" in ")
    self.write("(")
    self.convert_node(node.iter)
    self.write(")\n")
    for subnode in node.body:
      self.convert_node(subnode, )
    self.write("endfor\n")

  def convert_break(self, node):
    self.write("break;\n")

  def convert_continue(self, node):
    self.write("continue;\n")

  def convert_const(self, node):
    value = node.value
    if value is True:
      self.write('true');
    elif value is False:
      self.write("false");
    elif value is None:
      self.write("$nothing")
    elif value is "and":
      self.write("&&")
    elif value is "or":
      self.write("||")
    else:
      if isinstance(value, str):
        to_write = b"\"" + value.encode("unicode_escape") + b"\""
        self.write(to_write.decode('UTF-8'))
      else:
        self.write(str(value))

  def convert_node(self, node):
    node_type = type(node)
    logger.debug("Parsing node type: %r", node_type)
    converter = self.converters.get(node_type, self.default_converter)
    if callable(converter):
      logger.debug("Found converter %r", converter)
      converter(node, )

  def convert_and(self, node):
    self.write("&&")

  def convert_or(self, node):
    self.write("||")

  def convert_not(self, node):
    self.write("!")

  def convert_comparison(self, node):
    self.convert_node(node.left)
    for comp_type, subop in node.ops:
      self.write(self.convert_comp_op(comp_type))
      self.convert_node(subop)

  @staticmethod
  def convert_comp_op(op):
    transforms = {
      "is": "==",
      "is not": "!=",
    }
    op = transforms.get(op, op)
    return " " + op + " "

  def convert_name(self, node):
    new_name = self.transform_name(node.name)
    self.write(new_name)

  def convert_raise(self, node):
    self.output.write("raise (")
    self.convert_node(node.exc.func)
    self.write(");\n")


  @staticmethod
  def transform_name(name):
    return transformations_table.get(name, name)

  def convert_assign(self, node):
    if self.context.current_obj is not None and not self.context.verb:
      self.add_property(node)
    else:
      for target in node.targets:
        self.convert_node(target)
        self.write(" = ")
      self.convert_node(node.value)
      self.write(";\n")

  def add_property(self, node):
    obj = self.context.current_obj
    for prop in node.targets:
      self.write("@property {obj}.".format(**locals()))
      self.convert_node(prop)
      self.write("\n")
      self.write(";{obj}.".format(**locals()))
      self.convert_node(prop)
      self.write(" = ")
      self.convert_node(node.value)
      self.write(";\n")

  def convert_assign_name(self, node):
    self.write(node.name)

  def convert_aug_assign(self, node):
    self.convert_node(node.target)
    self.write(" = ")
    self.convert_node(node.target)
    self.write(" " + node.op[0] + " ")
    self.convert_node(node.value)
    self.write(";\n");

  def convert_bin_op(self, node):
    self.convert_node(node.left)
    self.write(" ")
    self.write(node.op)
    self.write(" ")
    self.convert_node(node.right)

  def convert_str(self, node):
    self.write(node.s.encode("unicode_escape"))

  def convert_expr(self, node):
    self.convert_node(node.value)
    self.write(";\n")


  def convert_num(self, node):
    self.write(str(node.n))

  def convert_list(self, node):
    if not node.elts:
      self.write("{}")
      return
    self.write("{")
    for elt in node.elts[:-1]:
      self.convert_node(elt)
      self.write(", ")
    self.convert_node(node.elts[-1])
    self.write("}")

  def convert_dict(self, node):
    if not node.items:
      self.write("[]")
      return
    self.write("[")
    n = 0;
    for key, value in node.items:
      n += 1;
      self.convert_node(key)
      self.write(" -> ")
      self.convert_node(value)
      if n < len(node.items):
        self.write(", ")
    self.write("]")

  def convert_subscript(self, node):
    self.convert_node(node.value)
    self.write("[")
    self.convert_node(node.slice)
    self.write("]")

  def convert_slice(self, node):
    self.convert_node(node.lower)
    if node.upper:
      self.write(":")
      self.convert_node(node.upper)

  def convert_multi_comparison(self, node):
    self.write("(")
    self.convert_node(node.values[0])
    self.write(") ")
    self.write_op(node.op)
    self.write("(")
    self.convert_node(node.values[1])
    self.write(")")

  def write_op(self, op):
    transforms = {'or': '||', 'not': '!', 'and': '&&'}
    self.write(transforms.get(op, op))

  def convert_return(self, node):
    self.write("return ")
    self.convert_node(node.value)
    self.write(";\n")

  def convert_args(self, node):
    positional = node.arguments[:len(node.arguments) - len(node.defaults)]
    positional = [i.name for i in positional]
    defaults = node.arguments[len(positional):]
    defaults = {i : node.defaults[n] for n, i in enumerate(defaults)}
    if positional and positional[0] == 'self':
      positional = positional[1:]
    if not positional and not defaults:
      return
    self.write("{")
    for n, p in enumerate(positional):
      self.write(p)
      if n < len(positional) - 1 and not defaults:
        self.write(", ")
    for n, what in enumerate(defaults.items()):
      arg_name, arg_value = what
      self.write("?")
      self.convert_node(arg_name)
      self.write("=")
      self.convert_node(arg_value)
      if n < len(defaults) - 1:
        self.write(", ")
    self.write("} = args;\n")

  def convert_attribute(self, node):
    self.convert_node(node.expr)
    if self.context.in_function_call:
      self.write(":")
    else:
      self.write(".")
    self.write(node.attrname)

  def convert_call(self, node):
    self.context.in_function_call = True
    self.convert_node(node.func)
    self.context.in_function_call = False
    arguments = []
    if node.args is not None:
      arguments.extend(node.args)
    if node.keywords is not None:
      arguments.extend(i.value for i in node.keywords)
    if not arguments:
      self.write("()");
      return
    self.write("(")
    for arg in arguments[:-1]:
      self.convert_node(arg)
      self.write(", ")
    self.convert_node(arguments[-1])
    self.write(")")

  def default_converter(self, node):
    if self.debug:
      pdb.set_trace()

  @classmethod
  def convert_file(cls, fname, output, debug=False):
    loaded = load_ast(fname)
    new = cls(output, debug=debug)
    for node in loaded.body:
      new.convert_node(node)

  def write(self, string):
    self.output.write(string)

  def write_comma_separated(self, node_list):
    for node in node_list[:-1]:
      self.convert_node(node)
      self.write(", ")
    self.convert_node(node_list[-1])

def main(args):
  if os.path.isfile(args.input) == False:
    raise RuntimeError("Input file {} not found.".format(args.input))
  OUTPUT = io.StringIO()
  if args.debug:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)
  PythonToMoo.convert_file(args.input, OUTPUT, args.debug)
  OUTPUT.seek(0)
  if args.output is None:
    logger.info("Done")
    print(OUTPUT.read())
    return
  else:
    with open(args.output, "w") as f:
      f.write(OUTPUT.read())
    logger.info("Wrote {}".format(args.output))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--input", help="Python file to convert to moo code", action="store", required=True)
  parser.add_argument("-o", "--output", help="File to write the moo code. If not specified, prints to the console.", action="store")
  parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
  args = parser.parse_args()
  main(args)
