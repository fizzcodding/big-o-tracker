import ast
from .models import FunctionAnalysis
from .complexity import estimate_time_complexity, estimate_space_complexity


class FunctionVisitor(ast.NodeVisitor):
    def __init__(self, func_name: str):
        self.func_name = func_name
        self.current_loop_depth = 0
        self.max_loop_depth = 0
        self.recursive_calls = 0

    def visit_For(self, node):
        self._enter_loop()
        self.generic_visit(node)
        self._exit_loop()

    def visit_While(self, node):
        self._enter_loop()
        self.generic_visit(node)
        self._exit_loop()

    def _enter_loop(self):
        self.current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_loop_depth)

    def _exit_loop(self):
        self.current_loop_depth -= 1

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id == self.func_name:
                self.recursive_calls += 1
        self.generic_visit(node)


def analyze_source(source: str) -> list[FunctionAnalysis]:
    tree = ast.parse(source)
    results: list[FunctionAnalysis] = []

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            visitor = FunctionVisitor(node.name)
            visitor.visit(node)

            big_o = estimate_time_complexity(
                visitor.max_loop_depth,
                visitor.recursive_calls
            )

            space_o = estimate_space_complexity(
                visitor.recursive_calls,
                visitor.max_loop_depth
            )

            results.append(
                FunctionAnalysis(
                    name=node.name,
                    time_complexity=big_o,
                    space_complexity=space_o,
                    max_loop_depth=visitor.max_loop_depth,
                    recursive_calls=visitor.recursive_calls,
                )
            )

    return results
