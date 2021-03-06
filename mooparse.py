from pyleri import Choice, Grammar, Keyword, List, Optional, Regex, Prio, Ref, Repeat, Sequence, THIS, Token, Tokens

class MooGrammar(Grammar):
  START = Ref()
  # Types we need regular expressions for
  r_int = Regex('-?[0-9]+')
  r_string = Regex(r'(")(?:(?=(\\?))\2.)*?\1')
  r_float = Regex(r'-?[0-9]+\.?[0-9]+')
  r_var = Regex(r'\$?[a-zA-Z_][a-zA-Z0-9_]*')
  r_objnum = Regex('#[0-9]+')
  # Keywords
  k_if = Keyword('if')
  k_else = Keyword('else')
  k_elseif = Keyword('elseif')
  k_endif = Keyword('endif')
  k_in = Keyword('in')
  k_for = Keyword('for')
  k_endfor = Keyword('endfor')
  k_while = Keyword('while')
  k_endwhile = Keyword('endwhile')
  k_break = Keyword('break')
  k_continue = Keyword('continue')
  k_return = Keyword('return')
  k_fork = Keyword('fork')
  k_endfork = Keyword('endfork')
  k_try = Keyword('try')
  k_endtry = Keyword('endtry')
  k_except = Keyword('except')
  k_finally = Keyword('finally')
  k_any = Keyword('ANY')
  # Tokens
  t_equals = Token('=')
  t_lparen = Token('(')
  t_rparen = Token(')')
  t_lbracket = Token('[')
  t_rbracket = Token(']')
  t_lbrace = Token('{')
  t_rbrace = Token('}')
  t_dot = Token('.')
  t_question = Token('?')
  t_bar = Token('|')
  t_arrow = Token('->')
  t_grave = Token('`')
  t_exclamation = Token('!')
  t_eg = Token('=>')
  t_colon = Token(':')
  t_tick = Token("'")
  t_semi = Token(';')
  # Forward References
  FUNCTION_CALL = Ref()
  PROP_REF = Ref()
  VERB_CALL = Ref()
  LIST = Ref()
  MAP = Ref()
  SUBSCRIPT = Ref()
  COMPARISON = Ref()
  MULTI_COMPARISON = Ref()
  EXPRESSION = Ref()
  # Complex types
  VALUE = Choice(r_int, r_objnum, r_string, r_float, LIST, MAP, VERB_CALL, FUNCTION_CALL, PROP_REF, MULTI_COMPARISON, r_var)
  LIST = Sequence(t_lbrace, List(VALUE), t_rbrace)
  MAP_KEY_VAL = Sequence(Choice(r_string, r_int), t_arrow, EXPRESSION)
  MAP = Sequence(t_lbracket, Optional(List(MAP_KEY_VAL)), t_rbracket)
  PROP_REF = Sequence(Choice(r_objnum, r_var), t_dot, Choice(r_var, Sequence(t_lparen, EXPRESSION, t_rparen)))
  OP_TOKENS = Tokens('+ - * /')
  BIN_OP = List(VALUE, mi=2, delimiter=OP_TOKENS)
  COMP_TOKENS = Tokens('< > <= >= == !=')
  COMPARISON = Sequence(t_lparen, List(EXPRESSION, delimiter=COMP_TOKENS), t_rparen)
  COMP_SEP_TOKENS = Tokens('&& ||')
  MULTI_COMPARISON = Sequence(List(COMPARISON, mi=1, delimiter=COMP_SEP_TOKENS))
  ASSIGNMENT = Sequence(Choice(PROP_REF, r_var, SUBSCRIPT), t_equals, EXPRESSION)
  WHILE_LOOP = Sequence(k_while, t_lparen, MULTI_COMPARISON, t_rparen, Optional(START), Optional(k_break), Optional(k_continue), k_endwhile)
  FOR_CONDITION = Sequence(Choice(r_var, List(r_var, mi=2)), k_in, t_lparen, EXPRESSION, t_rparen)
  FOR_LOOP = Sequence(k_for, FOR_CONDITION, Optional(START), Optional(k_break), Optional(k_continue), k_endfor)
  CONDITIONAL = Sequence(k_if, t_lparen, MULTI_COMPARISON, t_rparen, Optional(START), Optional(Sequence(k_elseif, COMPARISON, Optional(START))), Optional(Sequence(k_else, Optional(START))), k_endif)
  EXCEPTION_HANDLER = Sequence(k_except, Optional(r_var), t_lparen, r_var, t_rparen, Optional(START))
  TRY = Sequence(k_try, Optional(START), Optional(List(EXCEPTION_HANDLER)), Optional(Sequence(k_finally, Optional(START))), k_endtry)
  COMPACT_TRY = Sequence(t_grave, EXPRESSION, t_exclamation, Choice(k_any, EXPRESSION), Optional(Sequence(t_eg, EXPRESSION)), t_tick)
  FORK = Sequence(k_fork, Optional(r_var), t_lparen, EXPRESSION, t_rparen, Optional(START), k_endfork)
  EXPRESSION = Choice(ASSIGNMENT,BIN_OP, VALUE, SUBSCRIPT, COMPACT_TRY)
  CALL_ARGS = List(EXPRESSION)
  OPTIONAL_ARG = Sequence(t_question, ASSIGNMENT)
  SCATTER_NAMES = Sequence(t_lbrace, List(Choice(r_var, OPTIONAL_ARG)), t_rbrace)
  SCATTER_ASSIGNMENT = Sequence(SCATTER_NAMES, t_equals, EXPRESSION);
  FUNCTION_CALL = Sequence(r_var, t_lparen, Optional(CALL_ARGS), t_rparen)
  VERB_CALL = Sequence(r_var, t_colon, Choice(r_var, Sequence(t_lparen, r_string, t_rparen)), t_lparen, Optional(CALL_ARGS), t_rparen)
  SUBSCRIPT = Sequence(Choice(VERB_CALL, FUNCTION_CALL, PROP_REF, VALUE), t_lbracket, Choice(VERB_CALL, FUNCTION_CALL, VALUE), t_rbracket)
  TERNARY = Sequence(EXPRESSION, t_question, EXPRESSION, t_bar, EXPRESSION)
  RETURN = Sequence(k_return, EXPRESSION)
  STATEMENT = Sequence(Optional(Choice(RETURN, ASSIGNMENT, VERB_CALL, FUNCTION_CALL, TERNARY, SCATTER_ASSIGNMENT)), t_semi)
  START = Repeat(Choice(CONDITIONAL, WHILE_LOOP, FOR_LOOP, TRY, FORK, STATEMENT, Sequence(r_string, t_semi)))


def walk(root):
  yield root
  for child in root.children:
    for node in walk(child):
      yield node

def node_props(node, children):
  return {
    'start': node.start,
    'end': node.end,
    'name': node.element.name if hasattr(node.element, 'name') else None,
    'element': node.element.__class__.__name__,
    'string': node.string,
    'children': children}


# Recursive method to get the children of a node object:
def get_children(children):
  return [node_props(c, get_children(c.children)) for c in children]


# View the parse tree:
def view_parse_tree(res):
  start = res.tree.children[0] if res.tree.children else res.tree
  return node_props(start, get_children(start.children))

def name_or_class(node):
  if hasattr(node.element, 'name'):
    return node.element.name
  return node.element.__class__.__name__

def error_line(text, position):
  prev_linebreak = text.rfind("\n", 0, position)
  next_linebreak = text.find("\n", position)
  if prev_linebreak == -1:
    prev_linebreak = 0
  else:
    prev_linebreak += 1
  if next_linebreak == -1:
    next_linebreak = len(text)
  line = text[prev_linebreak:next_linebreak]
  return line


def overview(nodes):
  return [name_or_class(i ) for i in nodes]

grammar = MooGrammar()

test = """\
a=0;
b=a;
if (a!=b)
return 1;
endif
i=0;
while (i < 5)
i = i + 1;
endwhile
for n in ($list_utils:range(5))
player:tell(n);
endfor
test = {1, 2, "chicken"};
for i in (this.that)
player:tell(test[i]);
endfor
this.("testing") = 4.0;
"""


if __name__ == '__main__':
  result = grammar.parse(test)
  print(result)
  data = view_parse_tree(result)
  import json
  print(json.dumps(data, indent=2))
