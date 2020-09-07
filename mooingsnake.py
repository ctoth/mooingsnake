import argparse
import ast
import io
import os
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

  def __attrs_post_init__(self):
    """Register converters here"""
    self.converters = {
      ast.ClassDef: self.convert_obj,
      ast.FunctionDef: self.convert_verb,
      ast.While: self.convert_while,
      ast.If: self.convert_if,
      ast.For: self.convert_for,
      ast.Break: self.convert_break,
      ast.NameConstant: self.convert_const,
    }

  def convert_verb(self, node):
    verb_name = node.name
    obj_name = self.context.current_obj
    default_args = DEFAULT_VERB_ARGS
    default_perms = DEFAULT_VERB_PERMS
    self.context.verb = verb_name
    self.output.write("@verb {obj_name}:{verb_name} {default_args} {default_perms}\n".format(**locals()))
    for subnode in node.body:
      self.convert_node(subnode, )
    self.output.write(".\n")

  def convert_obj(self, node):
    class_name = node.name
    self.output.write("@create #1 named {class_name}\n".format(**locals()))
    self.context.current_obj = class_name

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
    if self.context.current_obj is None and context.verb is None:
      raise RuntimeError("If statement not supported out of class or function.")
    if self.context.verb is None:
      raise RuntimeError("If not supported out of function call.")
    self.convert_scoped_node(node, "if", "endif")

  def convert_for(self, node):
    if self.context.current_obj is None and context.verb is None:
      raise RuntimeError("for loop not supported out of class or function.")
    if self.context.verb is None:
      raise RuntimeError("For loop not supported out of function call.")
    self.convert_scoped_node(node, "if", "endif")

  def convert_break(self, node):
    self.output.write("break;\n")

  def convert_const(self, node):
    value = node.value
    if value is True:
      self.output.write('true');
    elif value is False:
      self.output.write("false");
    else:
      raise RuntimeError("Don't know how to write value %r" % value)

  def convert_node(self, node):
    node_type = type(node)
    logger.debug("Parsing node type: %r", node_type)
    converter = self.converters.get(node_type)
    if callable(converter):
      logger.debug("Found converter %r", converter)
      converter(node, )

  @classmethod
  def convert_file(cls, fname, output):
    loaded = load_ast(fname)
    new = cls(output)
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
  PythonToMoo.convert_file(args.input, OUTPUT)
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
  parser.add_argument("-o", "--output", help="File to write the moo code. If not specified, prints to moo code to the console.", action="store")
  parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
  args = parser.parse_args()
  main(args)
