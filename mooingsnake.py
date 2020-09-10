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
  'len': 'length',
}

def load_ast(fname):
  with open(fname) as f:
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
      astroid.Assign: self.convert_assign,
      astroid.node_classes.AssignName: self.convert_assign_name,
      astroid.AugAssign: self.convert_aug_assign,
      astroid.BinOp: self.convert_bin_op,

      #astroid.Num: self.convert_num,
      astroid.List: self.convert_list,
      astroid.Subscript: self.convert_subscript,
      astroid.BoolOp: self.convert_multi_comparison,
      astroid.Return: self.convert_return,
      astroid.Attribute: self.convert_attribute,
      astroid.node_classes.Arguments: self.convert_args,
      astroid.Call: self.convert_call,
      str: self.convert_const,
    }

  def convert_verb(self, node):
    verb_name = node.name
    obj_name = self.context.current_obj
    default_args = DEFAULT_VERB_ARGS
    default_perms = DEFAULT_VERB_PERMS
    self.context.verb = verb_name
    self.output.write("@verb {obj_name}:{verb_name} {default_args} {default_perms}\n".format(**locals()))
    self.output.write("@program {obj_name}:{verb_name}\n".format(**locals()))
    self.convert_node(node.args)
    for subnode in node.body:
      self.convert_node(subnode, )
    self.output.write(".\n")
    self.context.verb = ""

  def convert_obj(self, node):
    class_name = node.name
    self.output.write("@create #1 named {class_name}\n".format(**locals()))
    self.context.current_obj = class_name
    for subnode in node.body:
      self.convert_node(subnode)

  def convert_scoped_node(self, node, start_token, end_token):
    self.output.write(start_token + " (")
    self.convert_node(node.test, )
    self.output.write(")\n")
    for subnode in node.body:
      self.convert_node(subnode, )
    self.output.write(end_token + "\n")

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
    if self.context.current_obj is None and context.verb is None:
      raise RuntimeError("for loop not supported out of class or function.")
    if self.context.verb is None:
      raise RuntimeError("For loop not supported out of function call.")
    self.output.write("for ")
    self.convert_node(node.target)
    self.output.write(" in ")
    self.output.write("(")
    self.convert_node(node.iter)
    self.output.write(")\n")
    for subnode in node.body:
      self.convert_node(subnode, )
    self.output.write("endfor\n")

  def convert_break(self, node):
    self.output.write("break;\n")

  def convert_continue(self, node):
    self.output.write("continue;\n")

  def convert_const(self, node):
    if isinstance(node, str):
      value = node
    else:
      value = node.value
    if value is True:
      self.output.write('true');
    elif value is False:
      self.output.write("false");
    elif value is None:
      self.output.write("$nothing")
    elif value is "and":
      self.output.write("&&")
    elif value is "or":
      self.output.write("||")
    elif value is "is":
      self.output.write("==")
    elif value is "not":
      self.output.write("!")
    else:
      if isinstance(value, str):
        self.output.write("\""+str(value)+"\"")
      else:
        self.output.write(str(value))

  def convert_node(self, node):
    node_type = type(node)
    logger.debug("Parsing node type: %r", node_type)
    converter = self.converters.get(node_type, self.default_converter)
    if callable(converter):
      logger.debug("Found converter %r", converter)
      converter(node, )

  def convert_and(self, node):
    self.output.write("&&")

  def convert_or(self, node):
    self.output.write("||")

  def convert_not(self, node):
    self.output.write("!")

  def convert_comparison(self, node):
    self.convert_node(node.left)
    self.output.write(" ")
    for comp_type, subop in node.ops:
      self.output.write(self.convert_comp_op(comp_type))
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
    self.output.write(new_name)

  @staticmethod
  def transform_name(name):
    return transformations_table.get(name, name)

  def convert_assign(self, node):
    if self.context.current_obj is not None and not self.context.verb:
      self.add_property(node)
    else:
      for target in node.targets:
        self.convert_node(target)
        self.output.write(" = ")
      self.convert_node(node.value)
      self.output.write(";\n")

  def add_property(self, node):
    obj = self.context.current_obj
    for prop in node.targets:
      self.output.write("@property {obj}.".format(**locals()))
      self.convert_node(prop)
      self.output.write("\n")
      self.output.write(";{obj}.".format(**locals()))
      self.convert_node(prop)
      self.output.write(" = ")
      self.convert_node(node.value)
      self.output.write(";\n")

  def convert_assign_name(self, node):
    self.output.write(node.name)

  def convert_aug_assign(self, node):
    self.convert_node(node.target)
    self.output.write(" = ")
    self.convert_node(node.target)
    self.convert_node(node.op)
    self.convert_node(node.value)
    self.output.write(";\n");

  def convert_bin_op(self, node):
    self.convert_node(node.left)
    self.output.write(" ")
    self.convert_node(node.op)
    self.output.write(" ")
    self.convert_node(node.right)

  def convert_str(self, node):
    self.output.write("\"" + node.s + "\"")

  def convert_num(self, node):
    self.output.write(str(node.n))

  def convert_list(self, node):
    self.output.write("{")
    for elt in node.elts:
      self.convert_node(elt)
      self.output.write(", ")
    self.output.write("}")

  def convert_subscript(self, node):
    self.convert_node(node.value)
    self.output.write("[")
    self.convert_node(node.slice)
    self.output.write("]")

  def convert_slice(self, node):
    if hasattr(node, 'value') and type(node.value) == astroid.Num:
     self.output.write(node.value.n + 1)
    else:
     self.default_converter(node)
     
  def convert_multi_comparison(self, node):
    self.output.write("(")
    self.convert_node(node.values[0])
    self.output.write(")")
    self.convert_node(node.op)
    self.output.write("(")
    self.convert_node(node.values[1])
    self.output.write(")")

  def convert_return(self, node):
    self.output.write("return ")
    self.convert_node(node.value)
    self.output.write(";\n")

  def convert_args(self, node):
    positional = node.arguments[:len(node.arguments) - len(node.defaults)]
    positional = [i.name for i in positional]
    defaults = node.arguments[len(positional):]
    defaults = {i : node.defaults[n] for n, i in enumerate(defaults)}
    if positional and positional[0] == 'self':
      positional = positional[1:]
    if not positional and not defaults:
      return
    self.output.write("{")
    for n, p in enumerate(positional):
      self.convert_node(p)
      if n < len(positional) - 1:
        self.output.write(", ")
    for d, subnode in defaults.items():
      self.output.write("?")
      self.convert_node(d)
      self.output.write("=")
      self.convert_node(subnode)
    self.output.write("} = args;\n")

  def convert_attribute(self, node):
    self.convert_node(node.expr)
    if self.context.in_function_call:
      self.output.write(":")
    else:
      self.output.write(".")
    self.output.write(node.attrname)

  def convert_call(self, node):
    self.context.in_function_call = True
    self.convert_node(node.func)
    self.context.in_function_call = False
    self.output.write("(")
    if node.args is not None:
      for arg in node.args:
        self.convert_node(arg)
        self.output.write(", ")
    if node.keywords is not None:
      for kwarg in node.keywords:
        self.convert_node(kwarg.value)
        self.output.write(", ")
    self.output.write(")")

  def default_converter(self, node):
    if self.debug:
      pdb.set_trace()

  @classmethod
  def convert_file(cls, fname, output, debug=False):
    loaded = load_ast(fname)
    new = cls(output, debug=debug)
    for node in loaded.body:
      new.convert_node(node)

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
