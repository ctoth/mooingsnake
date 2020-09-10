
def test_loop():
  while True:
    if True == True and False == False or "hi" != "lol123":
      test = "hello"
    break

class Test(object):
  def test_function(a, b, c=3):
    return a + b * c

  def do_test_message():
    return test_message(message="it works")
  def test_message(message="default message"):
    return message

  def test_builtins():
    test = str("hello")
    test = float(0.0)
    test2 = hex(1)
    test3 = len([1, 2, 3])
    