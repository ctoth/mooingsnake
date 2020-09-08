class Test(object):
  def test_function(a, b, c=3):
    return a + b * c

def test_loop():
  while True:
    if True == True and False == False or "hi" != "lol123":
      test = "hello"
    break

  def test_builtins():
    test = float(0.0)
    test2 = hex(1)
    test3 = len([1, 2, 3])
    