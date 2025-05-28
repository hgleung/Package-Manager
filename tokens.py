# Token types for the toy language lexer
from enum import Enum, auto

class TokenType(Enum):
    # Single-character tokens
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()
    EQUAL = auto()
    BANG = auto()
    LESS = auto()
    GREATER = auto()

    # One or two character tokens
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords
    VAR = auto()
    FUN = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()
    NIL = auto()
    WHILE = auto()
    FOR = auto()
    PRINT = auto()

    EOF = auto()

class Token:
    def __init__(self, type: TokenType, lexeme: str, literal: str, line: int):
        self.type = type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __repr__(self, verbose: bool = False):
        if verbose:
            return f"{self.type.name} {self.lexeme} {self.literal} (line: {self.line})"
        return f"{self.type.name} {self.lexeme} {self.literal}"
