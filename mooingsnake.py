import argparse
import ast
import io
import os
import pdb
import sys

import logging
from logging import getLogger
logger = getLogger("Transpiler")
from attr import attr, attributes, Factory

logger = getLogger("Transpiler")
logger.addHandler(logging.StreamHandler())

DEFAULT_VERB_ARGS = 'tnt'
DEFAULT_VERB_PERMS = 'RXD'

def load_ast(fname):
  with open(fname) as f:
    code = f.read()
  return ast.parse(code)

@attributes
class Context:
  current_obj = attr(default=None)
  verb = attr(default=None)

@attributes
class PythonToMoo:
  output = attr()
  context = attr(default=Factory(Context))
  debug = attr(default=False)

  def __attrs_post_init__(self):
    """Register converters here"""
    self.converters = {
      ast.ClassDef: self.convert_obj,
      ast.FunctionDef: self.convert_verb,
      ast.While: self.convert_while,
      ast.If: self.convert_if,
      ast.For: self.convert_for,
      ast.Break: self.convert_break,
      ast.Continue: self.convert_continue,
      ast.NameConstant: self.convert_const,
      ast.Eq: self.convert_eq,
      ast.NotEq: self.convert_not_eq,
      ast.Lt: self.convert_lt,
      ast.LtE: self.convert_lte,
      ast.Gt: self.convert_gt,
      ast.GtE: self.convert_gte,
      ast.Is: self.convert_eq, # for now
      ast.IsNot: self.convert_not_eq, # for now
      ast.And: self.convert_and,
      ast.Or: self.convert_or,
      ast.Not: self.convert_not,
      ast.Compare: self.convert_comparison,
      ast.Slice: self.convert_slice,
      ast.Name: self.convert_name,
      ast.Assign: self.convert_assign,
      ast.AugAssign: self.convert_aug_assign,
      ast.BinOp: self.convert_bin_op,
      ast.Add: self.convert_add,
      ast.Sub: self.convert_sub,
      ast.Mult: self.convert_mult,
      ast.Div: self.convert_div,
      ast.Mod: self.convert_mod,
      ast.Str: self.convert_str,
      ast.Num: self.convert_num,
      ast.List: self.convert_list,
      ast.Subscript: self.convert_subscript,
      ast.BoolOp: self.convert_multi_comparison,
      ast.Return: self.convert_return,
      ast.Attribute: self.convert_attribute,
      ast.arguments: self.convert_args,
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
    if node.iter.value:
      self.convert_node(node.iter.value)
      self.output.write(".")
    self.output.write(node.iter.attr)
    self.output.write(")\n")
    for subnode in node.body:
      self.convert_node(subnode, )
    self.output.write("endfor\n")

  def convert_break(self, node):
    self.output.write("break;\n")

  def convert_continue(self, node):
    self.output.write("continue;\n")

  def convert_const(self, node):
    value = node.value
    if value is True:
      self.output.write('true');
    elif value is False:
      self.output.write("false");
    elif value is None:
      self.output.write("$nothing")
    else:
      raise RuntimeError("Don't know how to write value %r" % value)

  def convert_node(self, node):
    node_type = type(node)
    logger.debug("Parsing node type: %r", node_type)
    converter = self.converters.get(node_type, self.default_converter)
    if callable(converter):
      logger.debug("Found converter %r", converter)
      converter(node, )

  def convert_eq(self, node):
    self.output.write("==")

  def convert_not_eq(self, node):
    self.output.write("!=")

  def convert_lt(self, node):
    self.output.write("<")

  def convert_gt(self, node):
    self.output.write(">")

  def convert_gte(self, node):
    self.output.write(">=")

  def convert_lte(self, node):
    self.output.write("<=")

  def convert_and(self, node):
    self.output.write("&&")

  def convert_or(self, node):
    self.output.write("||")

  def convert_not(self, node):
    self.output.write("!")

  def convert_comparison(self, node):
    self.convert_node(node.left)
    self.output.write(" ")
    for subop in node.ops:
      for subnode in node.comparators:
        self.convert_node(subop)
        self.output.write(" ")
        self.convert_node(subnode)

  def convert_name(self, node):
    new_name = self.transform_name(node.id)
    self.output.write(new_name)

  @staticmethod
  def transform_name(name):
    transformations = {
      'self': 'this',
    }
    return transformations.get(name, name)

  def convert_assign(self, node):
    for target in node.targets:
      self.convert_node(target)
      self.output.write(" = ")
    self.convert_node(node.value)
    self.output.write(";\n")

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

  def convert_add(self, node):
    self.output.write("+")

  def convert_sub(self, node):
    self.output.write("-")

  def convert_mult(self, node):
    self.output.write("*")

  def convert_div(self, node):
    self.output.write("/")

  def convert_mod(self, node):
    self.output.write("%")

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
    if type(node.value) == ast.Num:
     self.output.write(node.value.n + 1)
    else:
     self.convert_node(node.value)
     
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
    positional = node.args[:len(node.args) - len(node.defaults)]
    positional = [i.arg for i in positional]
    defaults = node.args[len(positional):]
    defaults = {i.arg : node.defaults[n] for n, i in enumerate(defaults)}
    if not positional and not defaults:
      return
    if positional and positional[0] == 'self':
      positional = positional[1:]
    if not positional and not defaults:
      return
    self.output.write("{")
    for p in positional:
      self.output.write(p + ", ")
    for d, subnode in defaults.items():
      self.output.write("?" + d + "=")
      self.convert_node(subnode)
    self.output.write("} = args;\n")

  def convert_attribute(self, node):
    self.convert_node(node.value)
    self.output.write(".")
    self.output.write(node.attr)

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
