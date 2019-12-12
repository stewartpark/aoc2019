from collections import namedtuple
import re

Token = namedtuple('Token', 'kind text')
ASTNode = namedtuple('ASTNode', 'kind children')


class NotMatched(Exception):
    pass


class Parser:
    TOKENS = {
        'AND': r'and',
        'OR': r'or',
        'NOT': r'not',
        'FN': r'fn',
        'IF': r'if',
        'ELSE': r'else',
        'END': r'end',
        'INT': r'-?[0-9]+',
        'IDENT': r'[a-zA-Z_][a-zA-Z0-9_]*',
        'LPAREN': r'\(',
        'RPAREN': r'\)',
        'LSQUARE': r'\[',
        'RSQUARE': r'\]',
        'COMMA': r',',
        'ADD': r'\+',
        'SUB': r'-',
        'MUL': r'\*',
        'DIV': r'/',
        'NEQ': r'!=',
        'GTE': r'>=',
        'LTE': r'<=',
        'EQ': r'=',
        'GT': r'>',
        'LT': r'<',
        'IGNORE': r'[ \t\r\n]|#.*'
    }

    def lex(self, source):
        tokens = []
        while source:
            for k, v in self.TOKENS.items():
                match = re.findall(f'^{v}', source)
                if match:
                    if k != 'IGNORE':
                        tokens.append(Token(k, match[0]))
                    source = source[len(match[0]):]
                    break
            else:
                near = source.split('\n')[0]
                raise NotMatched(f"Unexpected token near {near}")
        return tokens

    def take(self, tokens):
        try:
            return tokens.pop(0)
        except IndexError:
            return Token('EOF', '')

    def peek(self, tokens):
        try:
            return tokens[0]
        except IndexError:
            return Token('EOF', '')

    def parse(self, source):
        tokens = self.lex(source)
        _, tree = self.parse_program(tokens)
        return tree

    def parse_program(self, tokens):
        tokens = list(tokens)
        program = []
        while len(tokens) > 0:
            try:
                tokens, tree = self.parse_global_variable_definition(tokens)
                program.append(tree)
            except NotMatched:
                try:
                    tokens, tree = self.parse_function_definition(tokens)
                    program.append(tree)
                except NotMatched:
                    raise NotMatched(
                        "Expected a global variable or function definition")
        return tokens, ASTNode('program', program)

    def parse_statement(self, tokens):
        tokens = list(tokens)
        args = []
        try:
            tokens, tree = self.parse_assignment(tokens)
            args.append(tree)
        except NotMatched:
            try:
                tokens, tree = self.parse_expression(tokens)
                args.append(tree)
            except NotMatched:
                try:
                    tokens, tree = self.parse_if_statement(tokens)
                    args.append(tree)
                except NotMatched:
                    raise NotMatched(
                        "Expected expression/assignment/if")
        return tokens, ASTNode('statement', args)

    def parse_global_variable_definition(self, tokens):
        tokens = list(tokens)
        if self.peek(tokens).kind == 'IDENT':
            ident = self.take(tokens)
            if self.take(tokens).kind == 'EQ':
                if self.peek(tokens).kind == 'INT':
                    value = self.take(tokens)
                    return tokens, ASTNode('global_variable_definition', [ident, value])
                else:
                    raise NotMatched(
                        'Only INT is supported for a global variable value')
            else:
                raise NotMatched('Expected =')
        else:
            raise NotMatched('Expected a global variable name')

    def parse_function_definition(self, tokens):
        tokens = list(tokens)
        if self.take(tokens).kind == 'FN':
            func_name = self.take(tokens)
            if func_name.kind == 'IDENT':
                if self.take(tokens).kind == 'LPAREN':
                    params = []
                    while self.peek(tokens).kind != 'RPAREN':
                        param_name = self.take(tokens)
                        if param_name.kind == 'IDENT':
                            params.append(param_name)
                        else:
                            raise NotMatched(
                                "Expected a parameter name in fn(...)")
                        if self.peek(tokens).kind == 'COMMA':
                            self.take(tokens)
                    self.take(tokens)

                    func_body = []
                    while True:
                        try:
                            tokens, tree = self.parse_statement(tokens)
                            func_body.append(tree)
                        except NotMatched:
                            break
                    if self.peek(tokens).kind == 'END':
                        self.take(tokens)
                        return tokens, ASTNode('function_definition', [func_name, params, func_body])
                    else:
                        raise NotMatched(
                            "Expected end after the function body")
                else:
                    raise NotMatched("Expected ( after the function name")
            else:
                raise NotMatched("Expected an identifier after fn")
        else:
            raise NotMatched("Expected fn")

    def parse_if_statement(self, tokens):
        tokens = list(tokens)
        if self.take(tokens).kind == 'IF':
            tokens, expr = self.parse_expression(tokens)
            true_body = []
            false_body = []
            while True:
                try:
                    tokens, tree = self.parse_statement(tokens)
                    true_body.append(tree)
                except NotMatched:
                    break

            if self.peek(tokens).kind == 'ELSE':
                self.take(tokens)
                while True:
                    try:
                        tokens, tree = self.parse_statement(tokens)
                        false_body.append(tree)
                    except NotMatched:
                        break

            if self.take(tokens).kind == 'END':
                return tokens, ASTNode('if_statement', [expr, true_body, false_body])
            else:
                raise NotMatched('Expected end')
        else:
            raise NotMatched('Expected if')

    def parse_assignment(self, tokens):
        tokens = list(tokens)
        ident = self.take(tokens)
        if ident.kind == 'IDENT':
            indices = []
            while True:
                try:
                    tokens, tree = self.parse_expr_atom_index(tokens)
                    indices.append(tree)
                except NotMatched:
                    break
            if self.take(tokens).kind == 'EQ':
                try:
                    tokens, tree = self.parse_expression(tokens)
                    return tokens, ASTNode('assignment', [ident, indices, tree])
                except NotMatched:
                    raise NotMatched("Expected an expression after ... =")
            else:
                raise NotMatched("Expected =")
        else:
            raise NotMatched("Expected an identifier in an assignment")

    def parse_expression(self, tokens):
        tokens = list(tokens)
        tokens, tree = self.parse_expr_logical(tokens)
        return tokens, ASTNode("expression", [tree])

    def parse_expr_logical(self, tokens):
        tokens = list(tokens)
        expr_logical = []

        if self.peek(tokens).kind == 'NOT':
            expr_logical.append(self.take(tokens))
        else:
            expr_logical.append(Token(None, None))

        tokens, tree = self.parse_expr_comparison(tokens)
        expr_logical.append(tree)

        op = self.peek(tokens)
        if op.kind in ('AND', 'OR'):
            self.take(tokens)
            tokens, tree = self.parse_expr_logical(tokens)
            expr_logical.append(op)
            expr_logical.append(tree)
        return tokens, ASTNode('expr_logical', expr_logical)

    def parse_expr_comparison(self, tokens):
        tokens = list(tokens)
        expr_comparison = []
        tokens, tree = self.parse_expr_add(tokens)
        expr_comparison.append(tree)

        op = self.peek(tokens)
        if op.kind in ('GT', 'GTE', 'EQ', 'NEQ', 'LT', 'LTE'):
            self.take(tokens)
            tokens, tree = self.parse_expr_comparison(tokens)
            expr_comparison.append(op)
            expr_comparison.append(tree)
        return tokens, ASTNode('expr_comparison', expr_comparison)

    def parse_expr_add(self, tokens):
        tokens = list(tokens)
        expr_add = []
        tokens, tree = self.parse_expr_mul(tokens)
        expr_add.append(tree)

        op = self.peek(tokens)
        if op.kind in ('ADD', 'SUB'):
            self.take(tokens)
            tokens, tree = self.parse_expr_add(tokens)
            expr_add.append(op)
            expr_add.append(tree)
        return tokens, ASTNode('expr_add', expr_add)

    def parse_expr_mul(self, tokens):
        tokens = list(tokens)
        expr_mul = []
        tokens, tree = self.parse_expr_atom(tokens)
        expr_mul.append(tree)

        op = self.peek(tokens)
        if op.kind in ('MUL', 'DIV'):
            self.take(tokens)
            tokens, tree = self.parse_expr_mul(tokens)
            expr_mul.append(op)
            expr_mul.append(tree)
        return tokens, ASTNode('expr_mul', expr_mul)

    def parse_expr_atom(self, tokens):
        tokens = list(tokens)
        atom = []
        if self.peek(tokens).kind == 'LPAREN':
            self.take(tokens)
            tokens, tree = self.parse_expression(tokens)
            atom.append(tree)
            if self.take(tokens).kind != 'RPAREN':
                raise NotMatched('Expected )')
        elif self.peek(tokens).kind == 'LSQUARE':
            tokens, tree = self.parse_expr_atom_list(tokens)
            atom.append(tree)
        elif self.peek(tokens).kind == 'IDENT':
            atom.append(self.take(tokens))
        elif self.peek(tokens).kind == 'INT':
            atom.append(self.take(tokens))
        else:
            raise NotMatched('Not a value')

        try:
            tokens, tree = self.parse_expr_atom_func_args(tokens)
            atom.append(tree)
        except NotMatched:
            pass

        while True:
            try:
                tokens, tree = self.parse_expr_atom_index(tokens)
                atom.append(tree)
            except NotMatched:
                break
        return tokens, ASTNode('expr_atom', atom)

    def parse_expr_atom_list(self, tokens):
        tokens = list(tokens)
        items = []
        if self.take(tokens).kind == 'LSQUARE':
            while self.peek(tokens).kind != 'RSQUARE':
                try:
                    tokens, tree = self.parse_expression(tokens)
                    items.append(tree)
                except NotMatched:
                    raise NotMatched(
                        'Expected an expression in a list element')

                if self.peek(tokens).kind == 'COMMA':
                    self.take(tokens)
                elif self.peek(tokens).kind == 'RSQUARE':
                    pass
                else:
                    raise NotMatched("Expected , or ]")
            self.take(tokens)
            return tokens, ASTNode('expr_atom_list', items)
        else:
            raise NotMatched('Expected [')

    def parse_expr_atom_func_args(self, tokens):
        tokens = list(tokens)
        args = []
        if self.take(tokens).kind == 'LPAREN':
            while self.peek(tokens).kind != 'RPAREN':
                tokens, tree = self.parse_expression(tokens)
                args.append(tree)
                if self.peek(tokens).kind == 'COMMA':
                    self.take(tokens)
                elif self.peek(tokens).kind == 'RPAREN':
                    pass
                else:
                    raise NotMatched('Expected , or )')
            self.take(tokens)
            return tokens, ASTNode('expr_atom_func_args', args)
        else:
            raise NotMatched('Expected (')

    def parse_expr_atom_index(self, tokens):
        tokens = list(tokens)
        args = []
        if self.take(tokens).kind == 'LSQUARE':
            tokens, tree = self.parse_expression(tokens)
            args.append(tree)
            if self.take(tokens).kind == 'RSQUARE':
                return tokens, ASTNode('expr_atom_index', args)
            else:
                raise NotMatched('Expected ]')
        else:
            raise NotMatched('Expected [')
