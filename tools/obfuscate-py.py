#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 src/emos_sign.py 混淆成 python/emos_sign.py。

做法（全部基于标准库 ast，产物仍是普通 Python，任何 3.8+ 都能跑）：
  1. 去掉全部注释与文档字符串
  2. 模块级函数名、参数名、局部变量名统一改成 a / b / c ... 这类无意义短名
  3. 常量字符串（接口路径、提示语）保留 —— 它们必须原样发给服务端
  4. 输出压成少行，读起来就是一坨

不采用 base64+exec 那种打包方式：虽然更"像加密"，但 Actions 日志里会很难看，
而且出了事完全没法排查。

    python3 tools/obfuscate-py.py
"""

import ast
import io
import keyword
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "emos_sign.py")
OUT = os.path.join(ROOT, "python", "emos_sign.py")

# 绝不改名的东西：内置函数、模块别名、特殊名
KEEP = set(keyword.kwlist) | {
    "self", "cls", "__name__", "__main__", "__file__", "__doc__",
    "print", "len", "range", "int", "str", "float", "bool", "list", "dict",
    "set", "tuple", "open", "super", "object", "Exception", "ValueError",
    "RuntimeError", "True", "False", "None", "enumerate", "sorted", "max",
    "min", "abs", "round", "isinstance", "getattr", "setattr", "hasattr",
    "zip", "map", "filter", "any", "all", "sum", "repr", "bytes", "type",
    "re", "json", "os", "sys", "time", "random", "urllib",
}


def short_name(n):
    """0,1,2... → a,b,...,z,aa,ab..."""
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(97 + r) + s
    return "_" + s


class Obfuscator(ast.NodeTransformer):
    def __init__(self):
        self.map = {}
        self.used = set()
        self.counter = 0

    def name_for(self, old):
        if old in self.map:
            return self.map[old]
        if old in KEEP or old.startswith("__"):
            return old
        while True:
            cand = short_name(self.counter)
            self.counter += 1
            if cand not in self.used and cand not in KEEP:
                self.used.add(cand)
                break
        self.map[old] = cand
        return cand

    # 收集定义
    def visit_FunctionDef(self, node):
        node.name = self.name_for(node.name)
        for a in list(node.args.args) + list(node.args.kwonlyargs):
            a.arg = self.name_for(a.arg)
        if node.args.vararg:
            node.args.vararg.arg = self.name_for(node.args.vararg.arg)
        if node.args.kwarg:
            node.args.kwarg.arg = self.name_for(node.args.kwarg.arg)
        self.generic_visit(node)
        # 去掉函数文档字符串
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body = node.body[1:] or [ast.Pass()]
        return node

    def visit_ClassDef(self, node):
        node.name = self.name_for(node.name)
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        if node.id in KEEP or node.id.startswith("__"):
            return node
        # 只改我们自己定义的（Store 出现过的）或者已知映射里的
        if node.id in self.map:
            node.id = self.map[node.id]
        elif isinstance(node.ctx, ast.Store):
            node.id = self.name_for(node.id)
        return node

    def visit_arg(self, node):
        node.arg = self.name_for(node.arg)
        return node


def precollect(tree):
    """先把所有赋值目标/函数名登记进映射，避免先读后写时漏改"""
    ob = Obfuscator()

    class Collector(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            ob.name_for(node.name)
            for a in list(node.args.args) + list(node.args.kwonlyargs):
                ob.name_for(a.arg)
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store):
                ob.name_for(node.id)

        def visit_ExceptHandler(self, node):
            if node.name:
                ob.name_for(node.name)
            self.generic_visit(node)

    Collector().visit(tree)
    return ob


def main():
    if not os.path.exists(SRC):
        print("找不到源码：" + SRC, file=sys.stderr)
        return 1

    src = open(SRC, encoding="utf-8").read()
    tree = ast.parse(src)
    ob = precollect(tree)

    # 复用同一个映射表做替换
    class Replacer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            node.name = ob.map.get(node.name, node.name)
            for a in list(node.args.args) + list(node.args.kwonlyargs):
                a.arg = ob.map.get(a.arg, a.arg)
            if node.args.vararg:
                node.args.vararg.arg = ob.map.get(node.args.vararg.arg, node.args.vararg.arg)
            if node.args.kwarg:
                node.args.kwarg.arg = ob.map.get(node.args.kwarg.arg, node.args.kwarg.arg)
            self.generic_visit(node)
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
            return node

        def visit_Name(self, node):
            node.id = ob.map.get(node.id, node.id)
            return node

        def visit_ExceptHandler(self, node):
            if node.name:
                node.name = ob.map.get(node.name, node.name)
            self.generic_visit(node)
            return node

    tree = ast.fix_missing_locations(Replacer().visit(tree))

    # 去掉模块级文档字符串
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
        tree.body = tree.body[1:]

    out = ast.unparse(tree)

    header = "# -*- coding: utf-8 -*-\n# 混淆产物 · 源码不在本仓库，请勿手改\n"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(header + out + "\n")

    # 自检：语法必须通过
    compile(open(OUT, encoding="utf-8").read(), OUT, "exec")
    print("  src/emos_sign.py %dB → python/emos_sign.py %dB，改名 %d 个"
          % (len(src), os.path.getsize(OUT), len(ob.map)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
