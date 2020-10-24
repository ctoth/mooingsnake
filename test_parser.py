from mooparse import grammar

empty = ''
subscript_assignment = 'a["b"] = 1;'
ternary = 'a==1? 1 | 0;'
nested_ops = "a=(b-c)*(b*c)-d;"
scatter_assignment = '{a, b, ?c=3} = args;'
complex_scatter_assignment = '{sender, recipient, message, verbatim, ?format = this.options["format"], ?Extra = []} = args;'
fork = """\
fork tasky (5)
player:tell("Ran in a fork!");
endfork
"""
multi_comparison = 'if ((a==b) && (c==d) || (frob==1)) endif'

def test_empty_parse_succeeds():
  assert grammar.parse(empty).is_valid

def test_subscript_assignment():
  assert grammar.parse(subscript_assignment).is_valid

def test_calling_verb_from_string():
  assert grammar.parse('this:("something");')

def test_ternary():
  assert grammar.parse(ternary)

def test_scatter_assignment():
  assert grammar.parse(scatter_assignment).is_valid
  assert grammar.parse(complex_scatter_assignment).is_valid

def test_fork():
  assert grammar.parse(fork).is_valid

def test_multi_comparison():
  assert grammar.parse(multi_comparison).is_valid

def test_nested_ops():
  assert grammar.parse(nested_ops).is_valid
