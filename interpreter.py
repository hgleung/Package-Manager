# Basic interpreter for the toy language
from parser import VarDecl, Assignment, ExpressionStmt, StatementList, PrintStmt, Block, IfStmt, WhileStmt, FunctionDecl, Call, ReturnStmt, ParseError, ReturnException, Variable, Literal
from tokens import TokenType

class Environment:
    def __init__(self, enclosing=None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, name, value):
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.enclosing:
            return self.enclosing.get(name)
        raise RuntimeError(f"Undefined variable '{name}'.")

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing:
            self.enclosing.assign(name, value)
            return
        raise RuntimeError(f"Undefined variable '{name}'.")

class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.env = self.globals
        self.functions = {}
        # Register built-in functions
        self.functions['print'] = self._builtin_print

    def _builtin_print(self, *args):
        print(*args)

    def interpret(self, statements):
        try:
            if isinstance(statements, list):
                for stmt in statements:
                    self.execute(stmt)
            else:
                self.execute(statements)
        except RuntimeError as e:
            print(f"Runtime error: {e}")

    def execute(self, stmt):
        if isinstance(stmt, VarDecl):
            value = self.evaluate(stmt.initializer) if stmt.initializer else None
            self.env.define(stmt.name.lexeme, value)
        elif isinstance(stmt, Assignment):
            value = self.evaluate(stmt.value)
            self.env.assign(stmt.name.lexeme, value)
        elif isinstance(stmt, ExpressionStmt):
            self.evaluate(stmt.expression)
        elif isinstance(stmt, StatementList):
            for s in stmt.statements:
                self.execute(s)
        elif isinstance(stmt, PrintStmt):
            value = self.evaluate(stmt.expression)
            print(value)
        elif isinstance(stmt, Block):
            self.execute_block(stmt.statements, Environment(self.env))
        elif isinstance(stmt, IfStmt):
            cond = self.evaluate(stmt.condition)
            if cond:
                self.execute(stmt.then_branch)
            elif stmt.else_branch:
                self.execute(stmt.else_branch)
        elif isinstance(stmt, WhileStmt):
            while self.evaluate(stmt.condition):
                self.execute(stmt.body)
        elif isinstance(stmt, FunctionDecl):
            self.functions[stmt.name.lexeme] = stmt
        elif isinstance(stmt, ReturnStmt):
            value = self.evaluate(stmt.value) if stmt.value else None
            raise ReturnException(value)
        else:
            raise RuntimeError(f"Unknown statement: {stmt}")

    def execute_block(self, statements, env):
        previous = self.env
        try:
            self.env = env
            for stmt in statements:
                self.execute(stmt)
        finally:
            self.env = previous

    def evaluate(self, expr):
        if expr is None:
            return None
        # Variable (identifier)
        if isinstance(expr, Variable):
            return self.env.get(expr.name.lexeme)
        # Literal (number, string, boolean, nil)
        if isinstance(expr, Literal):
            return expr.value
        # Assignment as expression
        if isinstance(expr, Assignment):
            value = self.evaluate(expr.value)
            self.env.assign(expr.name.lexeme, value)
            return value
        # Binary expression
        if hasattr(expr, 'operator') and hasattr(expr, 'left') and hasattr(expr, 'right'):
            left = self.evaluate(expr.left)
            right = self.evaluate(expr.right)
            op = expr.operator.type
            if op == TokenType.PLUS:
                return left + right
            if op == TokenType.MINUS:
                return left - right
            if op == TokenType.STAR:
                return left * right
            if op == TokenType.SLASH:
                return left / right
            if op == TokenType.EQUAL_EQUAL:
                return left == right
            if op == TokenType.BANG_EQUAL:
                return left != right
            if op == TokenType.GREATER:
                return left > right
            if op == TokenType.GREATER_EQUAL:
                return left >= right
            if op == TokenType.LESS:
                return left < right
            if op == TokenType.LESS_EQUAL:
                return left <= right
            raise RuntimeError(f"Unknown binary operator: {expr.operator}")
        # Unary expression
        if hasattr(expr, 'operator') and hasattr(expr, 'right') and not hasattr(expr, 'left'):
            right = self.evaluate(expr.right)
            op = expr.operator.type
            if op == TokenType.MINUS:
                return -right
            if op == TokenType.BANG:
                return not right
            raise RuntimeError(f"Unknown unary operator: {expr.operator}")
        # Grouping
        if hasattr(expr, 'expression'):
            return self.evaluate(expr.expression)
        # Function call
        if hasattr(expr, 'callee') and hasattr(expr, 'arguments'):
            callee = expr.callee
            if hasattr(callee, 'lexeme') and callee.lexeme in self.functions:
                func = self.functions[callee.lexeme]
                args = [self.evaluate(arg) for arg in expr.arguments]
                if callable(func):  # Built-in function
                    return func(*args)
                env = Environment(self.globals)
                for param, arg in zip(func.params, args):
                    env.define(param.lexeme, arg)
                try:
                    self.execute_block(func.body, env)
                except ReturnException as ret:
                    return ret.value
                return None
            else:
                raise RuntimeError(f"Undefined function '{callee.lexeme if hasattr(callee, 'lexeme') else callee}'.")
        return expr
