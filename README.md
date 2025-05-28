# Toy Programming Language Interpreter

This project implements a toy programming language with a custom lexer, parser, and interpreter in Python. It supports variable declarations, arithmetic, control flow, functions (including recursion), and error handling. The codebase is modular, with each component responsible for a distinct phase of language processing.

---

## Table of Contents
- [Project Structure](#project-structure)
- [Language Features](#language-features)
- [How It Works](#how-it-works)
- [Testing](#testing)
- [Extending the Language](#extending-the-language)
- [Troubleshooting](#troubleshooting)

---

## Project Structure

```
package_manager/
├── interpreter.py      # Interpreter and runtime environment
├── parser.py           # Parser and AST node definitions
├── lexer.py            # Lexer (tokenizer)
├── tokens.py           # Token and TokenType definitions
├── tests/              # Test suite
├── README.md           # This documentation
```

### Main Components
- **lexer.py:** Converts source code into a stream of tokens.
- **tokens.py:** Defines the `Token` class and `TokenType` enum for all language symbols.
- **parser.py:** Converts tokens into an Abstract Syntax Tree (AST). Defines all AST node classes (e.g., `VarDecl`, `Assignment`, `PrintStmt`, `IfStmt`, `WhileStmt`, `FunctionDecl`, `Call`, `ReturnStmt`, `ExpressionStmt`, `Block`, `StatementList`, `Variable`, `Literal`, `Binary`, `Unary`, `Grouping`).
- **interpreter.py:** Walks the AST and executes code. Handles variable scope, function calls, control flow, and built-in functions.
- **test_interpreter.py:** Runs a battery of tests to validate interpreter correctness and language features.
- **test_parser_features.py:** Tests parser's AST output and error handling.

---

## Language Features

### 1. **Variables**
- Declaration: `var x = 10;`
- Assignment: `x = x + 5;`
- Scoping: Block-local variables with `{ ... }`.

### 2. **Expressions**
- Arithmetic: `+`, `-`, `*`, `/`
- Grouping: `( ... )`
- Literals: numbers, strings, booleans (`true`, `false`), `nil`

### 3. **Statements**
- Print: `print(x);`
- Blocks: `{ ... }`
- If/Else: `if (x > 0) print(x); else print(-x);`
- While: `while (x < 5) x = x + 1;`
- Function declaration: `fun add(a, b) { return a + b; }`
- Function call: `add(1, 2);`
- Return: `return expr;`

### 4. **Functions**
- First-class, support for parameters and return values.
- Recursion supported (e.g., factorial).

### 5. **Error Handling**
- Parse errors (e.g., missing semicolons, invalid assignment targets)
- Runtime errors (e.g., undefined variables, invalid operations)

---

## How It Works

### 1. **Lexing**
- The lexer (`lexer.py`) scans the source string and emits a list of tokens (instances of `Token`).
- Supported tokens include identifiers, literals, operators, delimiters, and keywords.

### 2. **Parsing**
- The parser (`parser.py`) consumes the token list and builds an AST using recursive descent.
- Each language construct has a corresponding AST node class.
- Assignment parsing ensures only valid targets (variables) are accepted.

### 3. **Interpreting**
- The interpreter (`interpreter.py`) walks the AST and executes statements and expressions.
- Maintains an `Environment` for variable scope (supports nested scopes for blocks and functions).
- Handles:
  - Variable declaration and assignment
  - Expression evaluation
  - Control flow (if/else, while)
  - Function definition and invocation (with support for recursion)
  - Built-in `print` function
  - Error reporting for undefined variables and invalid assignments

### 4. **Testing**
- `test_interpreter.py` runs a suite of programs covering all features. Output is printed for each test.
- `test_parser_features.py` checks parser output and error handling.

---

## Testing

Run all interpreter tests:
```bash
python3 test_interpreter.py
```

Expected output includes correct results for arithmetic, control flow, and function tests, plus error messages for invalid code.

Example:
```
--- Interpreter Test 2 ---
0.0
5.0
```

---

## Extending the Language

- **Add new statements or expressions:**
  - Define a new AST node in `parser.py`.
  - Update the parser to recognize the new syntax.
  - Add evaluation logic to the interpreter.
- **Add built-in functions:**
  - Register new functions in `Interpreter.__init__` in `interpreter.py`.
- **Improve error messages:**
  - Update error handling in the parser and interpreter.

---

## Troubleshooting

- **Assignment not updating variable:**
  - Ensure assignments are parsed as `Assignment` nodes and handled in `Interpreter.evaluate()`.
- **Undefined variable errors:**
  - Variables must be declared with `var` before use.
- **Parse errors (e.g., missing semicolon):**
  - Check syntax and ensure all statements are properly terminated.

---

## Authors & License

- Developed by Harry Leung
