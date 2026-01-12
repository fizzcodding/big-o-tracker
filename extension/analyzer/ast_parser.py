import ast
from .models import FunctionAnalysis
from .complexity import estimate_time_complexity, estimate_space_complexity


class CodeVisitor(ast.NodeVisitor):
    def __init__(self, func_name: str = None):
        self.func_name = func_name

        self.current_loop_depth = 0
        self.max_loop_depth = 0

        self.recursive_calls = 0
        self.current_recursive_calls = 0
        self.max_recursive_calls_in_scope = 0

    # -------- loops --------
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

    # -------- recursion detection --------
    def visit_FunctionDef(self, node):
        prev = self.current_recursive_calls
        self.current_recursive_calls = 0

        self.generic_visit(node)

        self.max_recursive_calls_in_scope = max(
            self.max_recursive_calls_in_scope,
            self.current_recursive_calls
        )

        self.current_recursive_calls = prev

    def visit_Call(self, node):
        if self.func_name:
            # direct recursion
            if isinstance(node.func, ast.Name):
                if node.func.id == self.func_name:
                    self.recursive_calls += 1
                    self.current_recursive_calls += 1

            # self.method() recursion
            elif isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                ):
                    method_name = self.func_name.split(".")[-1]
                    if node.func.attr == method_name:
                        self.recursive_calls += 1
                        self.current_recursive_calls += 1

        self.generic_visit(node)

class ASTAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.results = []
        self.current_class_name = None
        self.has_functions_or_classes = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.has_functions_or_classes = True
        full_name = f"{self.current_class_name}.{node.name}" if self.current_class_name else node.name

        visitor = CodeVisitor(full_name)
        visitor.visit(node)

        big_o = estimate_time_complexity(visitor.max_loop_depth, visitor.recursive_calls)
        space_o = estimate_space_complexity(visitor.recursive_calls, visitor.max_loop_depth)

        self.results.append(
            FunctionAnalysis(
                name=full_name,
                time_complexity=big_o,
                space_complexity=space_o,
                max_loop_depth=visitor.max_loop_depth,
                recursive_calls=visitor.recursive_calls,
            )
        )

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.has_functions_or_classes = True
        old_class_name = self.current_class_name
        self.current_class_name = node.name
        self.generic_visit(node)
        self.current_class_name = old_class_name

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.has_functions_or_classes = True
        full_name = f"{self.current_class_name}.{node.name}" if self.current_class_name else node.name

        visitor = CodeVisitor(full_name)
        visitor.visit(node)

        big_o = estimate_time_complexity(visitor.max_loop_depth, visitor.recursive_calls)
        space_o = estimate_space_complexity(visitor.recursive_calls, visitor.max_loop_depth)

        self.results.append(
            FunctionAnalysis(
                name=full_name,
                time_complexity=big_o,
                space_complexity=space_o,
                max_loop_depth=visitor.max_loop_depth,
                recursive_calls=visitor.recursive_calls,
            )
        )

        self.generic_visit(node)


def analyze_source(source: str) -> list[FunctionAnalysis]:
    tree = ast.parse(source)
    analyzer = ASTAnalyzer()
    analyzer.visit(tree)

    if not analyzer.has_functions_or_classes:
        visitor = CodeVisitor()
        visitor.visit(tree)

        big_o = estimate_time_complexity(visitor.max_loop_depth, visitor.recursive_calls)
        space_o = estimate_space_complexity(visitor.recursive_calls, visitor.max_loop_depth)

        analyzer.results.append(
            FunctionAnalysis(
                name="<main>",
                time_complexity=big_o,
                space_complexity=space_o,
                max_loop_depth=visitor.max_loop_depth,
                recursive_calls=visitor.recursive_calls,
            )
        )

    return analyzer.results


