from pyleri import Choice, Grammar, Keyword, List, Optional, Regex, Prio, Ref, Repeat, Sequence, THIS, Token, Tokens

class MooGrammar(Grammar):
  START = Ref()
  r_int = Regex('[0-9]+')
  r_string = Regex(r'(")(?:(?=(\\?))\2.)*?\1')
  r_float = Regex(r'-?[0-9]+\.?[0-9]+')
  r_var = Regex('\$?[a-zA-Z0-9]+')
  r_objnum = Regex('#[0-9]+')
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
  t_equals = Token('=')
  t_lparen = Token('(')
  t_rparen = Token(')')
  t_dot = Token('.')
  t_colon = Token(':')
  t_semi = Token(';')
  FUNCTION_CALL = Ref()
  VERB_CALL = Ref()
  PROP_REF = Sequence(Choice(r_objnum, r_var), t_dot, r_var)
  VALUE = Choice(r_int, r_objnum, r_string, r_float, VERB_CALL, FUNCTION_CALL, PROP_REF, r_var, most_greedy=False)
  BIN_OP = List(VALUE, delimiter=Tokens('+ -'))
  COMPARISON = Sequence(t_lparen, List(VALUE, delimiter=Tokens('< > <= >= == !=')), t_rparen)
  EXPRESSION = Ref()
  ASSIGNMENT = Sequence(Choice(PROP_REF, r_var), t_equals, EXPRESSION)
  WHILE_LOOP = Sequence(k_while, COMPARISON, Optional(START), Optional(k_break), Optional(k_continue), k_endwhile)
  FOR_CONDITION = Sequence(r_var, k_in, t_lparen, EXPRESSION, t_rparen)
  FOR_LOOP = Sequence(k_for, FOR_CONDITION, Optional(START), Optional(k_break), Optional(k_continue), k_endfor)
  CONDITIONAL = Sequence(k_if, COMPARISON, Optional(START), Optional(Sequence(k_elseif, COMPARISON, Optional(START))), Optional(Sequence(k_else, Optional(START))), k_endif)
  EXPRESSION = Choice(ASSIGNMENT, BIN_OP, VALUE, most_greedy=True)
  CALL_ARGS = List(VALUE)
  FUNCTION_CALL = Sequence(r_var, t_lparen, CALL_ARGS, t_rparen)
  VERB_CALL = Sequence(r_var, t_colon, r_var, t_lparen, CALL_ARGS, t_rparen)
  RETURN = Sequence(k_return, EXPRESSION)
  STATEMENT = Choice(RETURN, ASSIGNMENT, t_semi)
  START = Repeat(Choice(CONDITIONAL, WHILE_LOOP, FOR_LOOP, FUNCTION_CALL, VERB_CALL, STATEMENT, most_greedy=False))


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
for n in (range(5))
player:tell(n);
endfor
for i in (this.that)
endfor
"""

if __name__ == '__main__':
  result = grammar.parse(test)
  print(result)
  data = view_parse_tree(result)
