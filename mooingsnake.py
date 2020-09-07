import ast
import io
import sys

from attr import attr, attributes, Factory

OUTPUT = io.StringIO()

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

  def convert_node(self, node):
    node_type = type(node)
    converter = self.converters.get(node_type)
    if callable(converter):
      converter(node, )

  @classmethod
  def convert_file(cls, fname, output):
    loaded = load_ast(fname)
    new = cls(output)
    for node in loaded.body:
      new.convert_node(node)

def main(fname):
  PythonToMoo.convert_file(fname, OUTPUT)
  OUTPUT.seek(0)
  print(OUTPUT.read())

if __name__ == '__main__':
  main(sys.argv[1])
