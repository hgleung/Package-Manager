from llvmlite import ir
import subprocess

def get_host_triple():
    try:
        triple = subprocess.check_output(['llvm-config', '--host-target']).decode().strip()
        return triple
    except Exception:
        # Fallback for most Intel Macs
        return "x86_64-apple-macosx10.15.0"

class CodeGenerator:
    def __init__(self):
        self.module = ir.Module(name="main")
        self.module.triple = get_host_triple()
        self.builder = None
        self.func = None
        self.variables = {}

    def generate(self, node):
        if isinstance(node, list):
            result = None
            for stmt in node:
                result = self.generate(stmt)
            return result
        method = 'gen_' + type(node).__name__
        if hasattr(self, method):
            return getattr(self, method)(node)
        else:
            raise NotImplementedError(f"No codegen for node type: {type(node).__name__}")

    def gen_StatementList(self, node):
        # Entry point for top-level code
        func_type = ir.FunctionType(ir.VoidType(), [])
        self.func = ir.Function(self.module, func_type, name="main")
        block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        for stmt in node.statements:
            self.generate(stmt)
        self.builder.ret_void()
        return self.module

    def gen_Literal(self, node):
        # Only handle numbers for now
        return ir.Constant(ir.DoubleType(), float(node.value))

    def gen_Binary(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        op = node.operator.lexeme
        if op == '+':
            return self.builder.fadd(left, right, name="addtmp")
        elif op == '-':
            return self.builder.fsub(left, right, name="subtmp")
        elif op == '*':
            return self.builder.fmul(left, right, name="multmp")
        elif op == '/':
            return self.builder.fdiv(left, right, name="divtmp")
        elif op == '>':
            cmp = self.builder.fcmp_ordered('>', left, right, name="gttmp")
            return self.builder.uitofp(cmp, ir.DoubleType(), name="gttmpf")
        elif op == '<':
            cmp = self.builder.fcmp_ordered('<', left, right, name="lttmp")
            return self.builder.uitofp(cmp, ir.DoubleType(), name="lttmpf")
        elif op == '>=':
            cmp = self.builder.fcmp_ordered('>=', left, right, name="getmp")
            return self.builder.uitofp(cmp, ir.DoubleType(), name="getmpf")
        elif op == '<=':
            cmp = self.builder.fcmp_ordered('<=', left, right, name="letmp")
            return self.builder.uitofp(cmp, ir.DoubleType(), name="letmpf")
        elif op == '==':
            cmp = self.builder.fcmp_ordered('==', left, right, name="eqtmp")
            return self.builder.uitofp(cmp, ir.DoubleType(), name="eqtmpf")
        elif op == '!=':
            cmp = self.builder.fcmp_ordered('!=', left, right, name="netmp")
            return self.builder.uitofp(cmp, ir.DoubleType(), name="netmpf")
        else:
            raise NotImplementedError(f"Unknown operator {op}")

    def gen_VarDecl(self, node):
        var_addr = self.builder.alloca(ir.DoubleType(), name=node.name.lexeme)
        if node.initializer:
            value = self.generate(node.initializer)
            self.builder.store(value, var_addr)
        self.variables[node.name.lexeme] = var_addr
        return var_addr

    def gen_Assignment(self, node):
        value = self.generate(node.value)
        var_addr = self.variables[node.name.lexeme]
        self.builder.store(value, var_addr)
        return value

    def gen_Variable(self, node):
        var_addr = self.variables[node.name.lexeme]
        return self.builder.load(var_addr, name=node.name.lexeme)

    def gen_ExpressionStmt(self, node):
        return self.generate(node.expression)

    def gen_PrintStmt(self, node):
        # Use printf to print a double
        value = self.generate(node.expression)
        printf = self.declare_printf()
        global_fmt = self.get_or_create_format_string()
        fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
        self.builder.call(printf, [fmt_ptr, value])
        return value

    def get_or_create_format_string(self):
        if hasattr(self, '_global_fmt'):
            return self._global_fmt
        fmt_str = "%f\n\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_str)), bytearray(fmt_str.encode('utf8')))
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name="fstr")
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt
        self._global_fmt = global_fmt
        return global_fmt

    def gen_IfStmt(self, node):
        cond_val = self.generate(node.condition)
        zero = ir.Constant(ir.DoubleType(), 0.0)
        cond = self.builder.fcmp_ordered('!=', cond_val, zero, 'ifcond')
        then_bb = self.func.append_basic_block('then')
        else_bb = self.func.append_basic_block('else') if node.else_branch else None
        merge_bb = self.func.append_basic_block('ifcont')
        if else_bb:
            self.builder.cbranch(cond, then_bb, else_bb)
        else:
            self.builder.cbranch(cond, then_bb, merge_bb)
        # Then block
        self.builder.position_at_start(then_bb)
        self.generate(node.then_branch)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        # Else block
        if node.else_branch:
            self.builder.position_at_start(else_bb)
            self.generate(node.else_branch)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)
        # Merge block
        self.builder.position_at_start(merge_bb)

    def gen_WhileStmt(self, node):
        loop_bb = self.func.append_basic_block('loop')
        after_bb = self.func.append_basic_block('afterloop')
        self.builder.branch(loop_bb)
        self.builder.position_at_start(loop_bb)
        cond_val = self.generate(node.condition)
        zero = ir.Constant(ir.DoubleType(), 0.0)
        cond = self.builder.fcmp_ordered('!=', cond_val, zero, 'loopcond')
        body_bb = self.func.append_basic_block('loopbody')
        self.builder.cbranch(cond, body_bb, after_bb)
        # Body
        self.builder.position_at_start(body_bb)
        self.generate(node.body)
        if not self.builder.block.is_terminated:
            self.builder.branch(loop_bb)
        # After loop
        self.builder.position_at_start(after_bb)

    def gen_FunctionDecl(self, node):
        func_name = node.name.lexeme
        arg_types = [ir.DoubleType()] * len(node.params)
        func_ty = ir.FunctionType(ir.DoubleType(), arg_types)
        func = ir.Function(self.module, func_ty, name=func_name)
        block = func.append_basic_block('entry')
        saved_func = self.func
        saved_builder = self.builder
        saved_vars = self.variables.copy()
        self.func = func
        self.builder = ir.IRBuilder(block)
        self.variables = {}
        for i, arg in enumerate(func.args):
            arg.name = node.params[i].lexeme
            var_addr = self.builder.alloca(ir.DoubleType(), name=arg.name)
            self.builder.store(arg, var_addr)
            self.variables[arg.name] = var_addr
        ret_val = self.generate(node.body)
        # Emit a return 0.0 if function body didn't already return
        if not self.builder.block.is_terminated:
            self.builder.ret(ir.Constant(ir.DoubleType(), 0.0))
        self.func = saved_func
        self.builder = saved_builder
        self.variables = saved_vars
        return func

    def gen_Call(self, node):
        # node.callee may be a Variable node or a Token
        if hasattr(node.callee, 'name') and hasattr(node.callee.name, 'lexeme'):
            callee_name = node.callee.name.lexeme
        elif hasattr(node.callee, 'lexeme'):
            callee_name = node.callee.lexeme
        else:
            raise TypeError(f"Unknown callee node type: {type(node.callee)}")
        callee = self.module.get_global(callee_name)
        args = [self.generate(arg) for arg in node.arguments]
        return self.builder.call(callee, args, name="calltmp")

    def gen_ReturnStmt(self, node):
        if node.value:
            ret_val = self.generate(node.value)
            self.builder.ret(ret_val)
        else:
            self.builder.ret(ir.Constant(ir.DoubleType(), 0.0))
        return None

    def gen_Block(self, node):
        # Handle a block of statements
        result = None
        for stmt in node.statements:
            if self.builder.block.is_terminated:
                break
            result = self.generate(stmt)
        return result

    def declare_printf(self):
        if hasattr(self, '_printf'):
            return self._printf
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        self._printf = printf
        return printf