from mooparse import grammar

empty = ''
subscript_assignment = 'a["b"] = 1;'
ternary = 'a==1? 1 | 0;'
nested_ops = "a=(b-c)*(b*c)-d;"


def test_empty_parse_succeeds():
  assert grammar.parse(empty).is_valid

def test_subscript_assignment():
  assert grammar.parse(subscript_assignment).is_valid

def test_calling_verb_from_string():
  assert grammar.parse('this:("something");')

def test_ternary():
  assert grammar.parse(ternary)

def test_nested_ops():
  assert grammar.parse(nested_ops).is_valid