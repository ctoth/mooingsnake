import ast
import io
import sys

from attr import attr, attributes

OUTPUT = io.StringIO()

DEFAULT_VERB_ARGS = 'tnt'
DEFAULT_VERB_PERMS = 'RXD'

def load_ast(fname):
  with open(fname) as f:
    code = f.read()
  return ast.parse(code)

def convert_verb(node, context, output):
  verb_name = node.name
  obj_name = context.current_obj
  default_args = DEFAULT_VERB_ARGS
  default_perms = DEFAULT_VERB_PERMS
  output.write("@verb {obj_name}:{verb_name} {default_args} {default_perms}\n".format(**locals()))
  context.verb = verb_name

def convert_obj(node, context, output):
  class_name = node.name
  output.write("@create #1 named {class_name}\n".format(**locals()))
  context.current_obj = class_name

def convert_while(node, context, output):
  if context.current_obj is None and context.verb is None:
    raise RuntimeError("While loop not supported out of class or function.")
  if context.verb is None:
    raise RuntimeError("Loop not supported out of function call.")
  output.write("while ({0})\n".format(node.test.value))
  for subnode in node.body:
    convert_node(subnode, context, output)
  output.write("endwhile\n")


CONVERTERS = {
  ast.FunctionDef: convert_verb,
  ast.While: convert_while,
}

def convert_node(node, context, output):
  node_type = type(node)
  print(node_type)
  converter = CONVERTERS.get(node_type)
  if callable(converter):
    converter(node, context, output)

@attributes
class Context:
  current_obj = attr(default=None)
  verb = attr(default=None)

def convert_file(fname, output):
  loaded = load_ast(fname)
  context = Context()
  for node in ast.walk(loaded):
    convert_node(node, context, output)

def main(fname):
  convert_file(fname, OUTPUT)
  OUTPUT.seek(0)
  print(OUTPUT.read())

if __name__ == '__main__':
  main(sys.argv[1])
