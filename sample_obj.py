
def loop():
  while True:
    if True == True and False == False or "hi" != "lol123":
      test = "hello"
    break

class SampleClass(object):
  def somefunction(a, b, c=3):
    return a + b * c

  def do_test_message():
    return message(message="it works")

  def _message(message="default message"):
    return message

  def builtins():
    test = str("hello")
    test = float(0.0)
    test2 = hex(1)
    test3 = len([1, 2, 3])
    