from moo_vm import VM
from moo_opcodes import opcodes

vm = VM()
vm.run([opcodes.IMM, 1, opcodes.IMM, 2, opcodes.ADD, opcodes.IMM, 3, opcodes.MULT, opcodes.RETURN, opcodes.DONE])
