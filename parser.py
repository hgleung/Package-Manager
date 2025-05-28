# Parser for the toy language
from tokens import Token, TokenType

class ParseError(Exception):
    pass

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Expr:
    pass

class Statement:
    pass

class Variable(Expr):
    def __init__(self, name):
        self.name = name

class VarDecl(Statement):
    def __init__(self, name, initializer):
        self.name = name  # Token
        self.initializer = initializer  # Expr

class Assignment(Expr):
    def __init__(self, name, value):
        self.name = name  # Token
        self.value = value  # Expr

class ExpressionStmt(Statement):
    def __init__(self, expression):
        self.expression = expression

class StatementList(Statement):
    def __init__(self, statements):
        self.statements = statements

class PrintStmt(Statement):
    def __init__(self, expression):
        self.expression = expression

class Block(Statement):
    def __init__(self, statements):
        self.statements = statements

class IfStmt(Statement):
    def __init__(self, condition, then_branch, else_branch):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class WhileStmt(Statement):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ReturnStmt(Statement):
    def __init__(self, keyword, value):
        self.keyword = keyword  # Token
        self.value = value  # Expr or None

class FunctionDecl(Statement):
    def __init__(self, name, params, body):
        self.name = name  # Token
        self.params = params  # list of Token
        self.body = body  # Block or StatementList

class Call(Expr):
    def __init__(self, callee, paren, arguments):
        self.callee = callee  # Expr
        self.paren = paren  # Token (for error reporting)
        self.arguments = arguments  # list of Expr

class Binary(Expr):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class Literal(Expr):
    def __init__(self, value):
        self.value = value

class Grouping(Expr):
    def __init__(self, expression):
        self.expression = expression

class Unary(Expr):
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        statements = []
        while not self.is_at_end():
            stmt = self.declaration()
            if stmt is not None:
                statements.append(stmt)
        return StatementList(statements)

    def expression(self):
        return self.assignment()

    def equality(self):
        expr = self.comparison()
        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)
        return expr

    def comparison(self):
        expr = self.term()
        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)
        return expr

    def term(self):
        expr = self.factor()
        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)
        return expr

    def factor(self):
        expr = self.unary()
        while self.match(TokenType.SLASH, TokenType.STAR):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)
        return expr

    def unary(self):
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)
        return self.primary()

    def assignment(self):
        expr = self.equality()
        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()
            if isinstance(expr, Variable):
                return Assignment(expr.name, value)
            raise ParseError("Invalid assignment target.")
        return expr

    def primary(self):
        if self.match(TokenType.FALSE): 
            return Literal(False)
        if self.match(TokenType.TRUE): 
            return Literal(True)
        if self.match(TokenType.NIL): 
            return Literal(None)
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)
        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN)
            return Grouping(expr)
        if self.match(TokenType.IDENTIFIER):
            name = self.previous()
            # If next token is LEFT_PAREN, it's a call, otherwise it's a variable
            if self.check(TokenType.LEFT_PAREN):
                return self.finish_call(name)
            else:
                return Variable(name)
        raise ParseError("Expected expression.")

    def finish_call(self, callee):
        if not self.match(TokenType.LEFT_PAREN):
            return callee
        arguments = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                arguments.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break
        paren = self.consume(TokenType.RIGHT_PAREN)
        return Call(callee, paren, arguments)

    def match(self, *types):
        for type_ in types:
            if self.check(type_):
                self.advance()
                return True
        return False

    def declaration(self):
        if self.match(TokenType.FUN):
            return self.function_declaration()
        if self.match(TokenType.VAR):
            return self.var_declaration()
        return self.statement()

    def function_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expected function name.")
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after function name.")
        params = []
        if not self.check(TokenType.RIGHT_PAREN):
            while True:
                params.append(self.consume(TokenType.IDENTIFIER, "Expected parameter name."))
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters.")
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before function body.")
        body = self.block()
        return FunctionDecl(name, params, body)

    def var_declaration(self):
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name.")
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return VarDecl(name, initializer)

    def statement(self):
        if self.match(TokenType.PRINT):
            expr = self.expression()
            self.consume(TokenType.SEMICOLON)
            return PrintStmt(expr)
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.block())
        if self.match(TokenType.IF):
            self.consume(TokenType.LEFT_PAREN)
            condition = self.expression()
            self.consume(TokenType.RIGHT_PAREN)
            then_branch = self.statement()
            else_branch = None
            if self.match(TokenType.ELSE):
                else_branch = self.statement()
            return IfStmt(condition, then_branch, else_branch)
        if self.match(TokenType.WHILE):
            self.consume(TokenType.LEFT_PAREN)
            condition = self.expression()
            self.consume(TokenType.RIGHT_PAREN)
            body = self.statement()
            return WhileStmt(condition, body)
        if self.match(TokenType.RETURN):
            keyword = self.previous()
            value = None
            if not self.check(TokenType.SEMICOLON):
                value = self.expression()
            self.consume(TokenType.SEMICOLON, "Expected ';' after return value.")
            return ReturnStmt(keyword, value)
        expr = self.expression()
        self.consume(TokenType.SEMICOLON)
        return ExpressionStmt(expr)

    def block(self):
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            try:
                stmt = self.declaration()
                if stmt is not None:
                    statements.append(stmt)
            except ParseError as e:
                # Attempt to synchronize or skip bad input
                self.advance()
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after block.")
        return statements

    def consume(self, type_, error_msg=None):
        if self.check(type_):
            return self.advance()
        token = self.peek()
        msg = error_msg or f"Expected token {type_} at line {token.line}"
        raise ParseError(msg)

    def check(self, type_):
        if self.is_at_end(): return False
        return self.peek().type == type_

    def advance(self):
        if not self.is_at_end(): self.current += 1
        return self.previous()

    def is_at_end(self):
        return self.peek().type == TokenType.EOF

    def peek(self):
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]
