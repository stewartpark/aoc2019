from collections import namedtuple

from intlang.code_generator import CodeGenerator, MemorySection, Immediate, Position, Address

GlobalVariableBuilder = namedtuple('GlobalVariableBuilder', 'address')


class Compiler:

    def __init__(self, stack_size, heap_size):
        self.stack_size = stack_size
        self.heap_size = heap_size
        self.reset()

    def reset(self):
        self.global_scope = {}
        self.local_scope = {}
        self.code_generator = CodeGenerator(
            stack_size=self.stack_size,
            heap_size=self.heap_size
        )

    def set_var(self, f, scope, name, value):
        if name in scope and type(scope[name]) == str:
            raise Exception(
                f'You cannot write to a read-only variable: {name}')
        elif name in self.global_scope:
            if type(self.global_scope[name]) == Address:
                addr = self.global_scope[name]
            else:
                # FunctionBuilder contains its address as a property.
                # Since the user would want the address of the function, not
                # the first value of the function, here we are wrapping it with Immediate.
                addr = Immediate(self.global_scope[name].address)
            f.add(Immediate(0), value, addr)
        else:
            f.write_local(scope[name], value)

    def get_var(self, f, scope, name, target):
        if name in scope and type(scope[name]) == str:
            f.read_arg(int(scope[name]), target)
        elif name in scope:
            f.read_local(scope[name], target)
        elif name in self.global_scope:
            if type(self.global_scope[name]) == Address:
                addr = self.global_scope[name]
            else:
                # FunctionBuilder contains its address as a property.
                # Since the user would want the address of the function, not
                # the first value of the function, here we are wrapping it with Immediate.
                addr = Immediate(self.global_scope[name].address)
            f.add(Immediate(0), addr, target)
        else:
            raise Exception(f'Undefined variable: {name}')

    def compile_expression(self, f, scope, tree, stack_size_neg):
        if tree.kind == 'expression':
            self.compile_expression(f, scope, tree.children[0], stack_size_neg)
        elif tree.kind == 'expr_logical':
            self.compile_expression(f, scope, tree.children[1], stack_size_neg)
            if tree.children[0].kind == 'NOT':
                f.pop('r0')

                # handling the edge case of `not 0`
                f.jge('r0', Immediate(1), '$+9')
                f.jge(Immediate(-1), 'r0', '$+5')
                f.add('r0', Immediate(-1), 'r0')

                f.mul('r0', Immediate(-1), 'r0')  # negate the value
                f.push('r0')
            if len(tree.children) == 4:
                op = tree.children[2]
                self.compile_expression(
                    f, scope, tree.children[3], stack_size_neg)
                f.pop('r1')
                f.pop('r0')
                if op.kind == 'AND':
                    # multipication works as a logical AND.
                    f.mul('r0', 'r1', 'r0')
                elif op.kind == 'OR':
                    # addition works as a logical OR.
                    f.add('r0', 'r1', 'r0')
                else:
                    raise Exception(f"Unimplemented: {op}")
                f.push('r0')
        elif tree.kind == 'expr_comparison':
            self.compile_expression(f, scope, tree.children[0], stack_size_neg)
            if len(tree.children) == 3:
                op = tree.children[1]
                self.compile_expression(
                    f, scope, tree.children[2], stack_size_neg)
                f.pop('r1')
                f.pop('r0')
                if op.kind == 'LT':
                    # if -r0 + r1 is a positive integer, true.
                    f.mul('r0', Immediate(-1), 'r0')
                    f.add('r0', 'r1', 'r0')
                elif op.kind == 'LTE':
                    # if -r0 + (r1 + 1) is a positive integer, true.
                    f.add('r1', Immediate(1), 'r1')
                    f.mul('r0', Immediate(-1), 'r0')
                    f.add('r0', 'r1', 'r0')
                elif op.kind == 'EQ':
                    f.add(Immediate(0), Immediate(1), 'r2')
                    f.jge('r0', 'r1', Immediate('$+5'))
                    f.add(Immediate(0), Immediate(0), 'r2')
                    f.jge('r1', 'r0', Immediate('$+5'))
                    f.add(Immediate(0), Immediate(0), 'r2')
                    f.add('r2', Immediate(0), 'r0')
                elif op.kind == 'NEQ':
                    f.add(Immediate(0), Immediate(0), 'r2')
                    f.jge('r0', 'r1', Immediate('$+5'))
                    f.add(Immediate(0), Immediate(1), 'r2')
                    f.jge('r1', 'r0', Immediate('$+5'))
                    f.add(Immediate(0), Immediate(1), 'r2')
                    f.add('r2', Immediate(0), 'r0')
                elif op.kind == 'GT':
                    f.mul('r1', Immediate(-1), 'r1')
                    f.add('r0', 'r1', 'r0')
                elif op.kind == 'GTE':
                    f.add('r0', Immediate(1), 'r0')
                    f.mul('r1', Immediate(-1), 'r1')
                    f.add('r0', 'r1', 'r0')
                else:
                    raise Exception(f"Unimplemented: {op}")
                f.push('r0')
        elif tree.kind == 'expr_add':
            self.compile_expression(f, scope, tree.children[0], stack_size_neg)
            if len(tree.children) == 3:
                op = tree.children[1]
                self.compile_expression(
                    f, scope, tree.children[2], stack_size_neg)
                f.pop('r1')
                f.pop('r0')
                if op.kind == 'ADD':
                    f.add('r0', 'r1', 'r0')
                elif op.kind == 'SUB':
                    f.mul('r1', Immediate(-1), 'r1')
                    f.add('r0', 'r1', 'r0')
                else:
                    raise Exception(f"Unimplemented: {op}")
                f.push('r0')
        elif tree.kind == 'expr_mul':
            self.compile_expression(f, scope, tree.children[0], stack_size_neg)
            if len(tree.children) == 3:
                op = tree.children[1]
                self.compile_expression(
                    f, scope, tree.children[2], stack_size_neg)
                f.pop('r1')
                f.pop('r0')
                if op.kind == 'MUL':
                    f.mul('r0', 'r1', 'r0')
                elif op.kind == 'DIV':
                    f.div('r0', 'r1', 'r0')
                else:
                    raise Exception(f"Unimplemented: {op}")
                f.push('r0')
        elif tree.kind == 'expr_atom':
            if len(tree.children) > 1:
                if tree.children[1].kind == 'expr_atom_func_args':
                    func_args = tree.children[1]
                    indices = tree.children[2:]
                else:
                    func_args = []
                    indices = tree.children[1:]
            else:
                func_args = []
                indices = []

            if func_args:
                # Args are pushed in reverse order
                for arg in reversed(func_args.children):
                    self.compile_expression(f, scope, arg, stack_size_neg)

            self.compile_expression(f, scope, tree.children[0], stack_size_neg)

            if func_args:
                f.pop('r0')
                f.call('r0')
                f.add('sp', Immediate(len(func_args.children)), 'sp')
                f.push('r0')

            if indices:
                for ind in indices:
                    self.compile_expression(
                        f, scope, ind.children[0], stack_size_neg)
                    f.pop('r1')
                    f.pop('r0')
                    f.add('r0', 'r1', '$+3')  # r0 = base, r1 = offset
                    f.add(Immediate(0), 0, 'r0')
                    f.push('r0')
        elif tree.kind == 'IDENT':
            self.get_var(f, scope, tree.text, 'r0')
            f.push('r0')
        elif tree.kind == 'INT':
            f.push(Immediate(int(tree.text)))
        elif tree.kind == 'expr_atom_list':
            # Allocate stack for the value
            var = -stack_size_neg.intcode
            stack_size_neg.intcode -= len(tree.children)
            for i, elm in enumerate(reversed(tree.children)):
                self.compile_expression(f, scope, elm, stack_size_neg)
                f.pop('r0')
                f.write_local(var + i, 'r0')
            # Get the start address of the array
            f.add('bp', Immediate(-(var + len(tree.children))), 'r0')
            f.push('r0')
        else:
            raise Exception(f"Unimplemented: {tree.kind}")

    def compile_statement(self, f, scope, tree, stack_size_neg):
        if tree.kind == 'statement':
            self.compile_statement(f, scope, tree.children[0], stack_size_neg)
        elif tree.kind == 'expression':
            self.compile_expression(f, scope, tree, stack_size_neg)
            # Clean up what the expression pushed.
            # Pop it into r0 so the last expression can be a return value
            f.pop('r0')
        elif tree.kind == 'assignment':
            # Evaluate the expression
            self.compile_expression(f, scope, tree.children[2], stack_size_neg)

            var = tree.children[0].text
            if len(tree.children[1]):  # a[x][y]... = expr
                self.get_var(f, scope, var, 'r0')
                f.push('r0')
                for ind in tree.children[1]:
                    self.compile_expression(
                        f, scope, ind.children[0], stack_size_neg)
                    f.pop('r1')
                    f.pop('r0')
                    f.add('r0', 'r1', '$+3')
                    f.add(Immediate(0), Immediate(0), 'r0')
                f.pop('r1')  # value to assign
                f.add(Immediate(0), 'r0', '$+4')
                f.add(Immediate(0), 'r1', 0)
            else:  # a = expr
                f.pop('r0')
                # If not exist
                if var not in self.global_scope and var not in scope:
                    # Assign a space within the stack frame
                    scope[var] = -stack_size_neg.intcode
                    stack_size_neg.intcode -= 1  # Grow negatively
                # Save it in the variable.
                self.set_var(f, scope, var, 'r0')
        elif tree.kind == 'if_statement':
            else_addr = Immediate(0)
            end_addr = Immediate(0)

            self.compile_expression(f, scope, tree.children[0], stack_size_neg)
            f.pop('r0')
            f.jge(Immediate(0), 'r0', else_addr)

            # if block
            start = f.address.size
            for stat in tree.children[1]:
                self.compile_statement(f, scope, stat, stack_size_neg)
            f.jge(Immediate(0), Immediate(0), end_addr)

            # else block
            else_addr.intcode = f'$+{f.address.size - start + 1}'
            start = f.address.size
            for stat in tree.children[2]:
                self.compile_statement(f, scope, stat, stack_size_neg)
            end_addr.intcode = f'$+{f.address.size - start + 1}'
        else:
            raise Exception(f"Unimplemented: {tree.kind}")

    def compile_function(self, name, stats):
        f = self.global_scope[name]

        # To allocate local variable stack area, we add a negative value to the stack pointer
        # so that can be effectively "pushed" to empty the area.
        # However, we are not calculating the stack size ahead of time. So, we're making this variable lazy.
        stack_size_neg = Immediate(0)
        local_scope = self.local_scope[name]

        # Save and set bp and allocate
        f.push('bp')
        f.add(Immediate(2), 'sp', 'bp')  # 2 = bp + ret addr
        f.add('sp', stack_size_neg, 'sp')

        for stat in stats:
            self.compile_statement(f, local_scope, stat, stack_size_neg)

        # clean up and ret
        f.add('sp', Immediate(-stack_size_neg.intcode), 'sp')
        f.pop('bp')
        f.ret('r0')

    def add_builtin(self):
        # Memory section access (stack, text, data, heap)
        self.global_scope['_sections'] = GlobalVariableBuilder(
            self.code_generator.section_info)

        # print(x)
        name = 'print'
        f = self.global_scope[name] = self.code_generator.new_function()
        f.read_stack(1, 'r0')
        f.out('r0')
        f.ret('r0')

    def compile(self, ast):
        self.reset()
        self.add_builtin()

        # Register all functions/global vars first so it can reference each other regardless of the order of definitions
        for stat in ast.children:
            if stat.kind == 'function_definition':
                name, params, _ = stat.children
                self.global_scope[name.text] = self.code_generator.new_function()
                self.local_scope[name.text] = {
                    # a string value means an argument vs. an int value in scope means a local variable.
                    x.text: f'{i}' for i, x in enumerate(params)
                }
            elif stat.kind == 'global_variable_definition':
                name, value = stat.children
                self.global_scope[name.text] = self.code_generator.data.obtain(
                    1)
                self.global_scope[name.text].content[0] = int(value.text)

        # Compile all functions
        for func_def in [x for x in ast.children if x.kind == 'function_definition']:
            name, _, body = func_def.children
            self.compile_function(name.text, body)

        if 'main' not in self.global_scope:
            raise Exception("function main does not exist")

        # Set up entrypoint
        entrypoint = self.code_generator.new_function()
        entrypoint.call(Immediate(self.global_scope['main'].address))
        entrypoint.halt()
        self.code_generator.set_entrypoint(entrypoint.address)

        return self.code_generator.generate()
