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
        self.max_recursive_calls_in_single_path = 0
        
        # Track nested function names for recursion detection
        self.nested_function_names = set()
        
        # Track if recursion/loops divide problem size (for O(log n))
        self.has_dividing_recursion = False
        self.has_dividing_loop = False
        self.has_loop_with_recursion = False
        # Track if recursive calls are in mutually exclusive branches (if/else)
        self.has_mutually_exclusive_recursion = False
        # Track if we're currently processing an if/else structure
        self.processing_if_else = False
        # Track built-in method calls with known complexities
        self.has_builtin_sort = False
        # Track binary search pattern in while loops (l = mid + 1, r = mid - 1)
        self.has_binary_search_pattern = False
        
        # Track recursive calls in current statement block (for O(2^n) detection)
        self.recursive_calls_in_current_block = 0
        # Track recursive calls in current function body (for better O(2^n) detection)
        self.recursive_calls_in_function_body = []
        # Track if we're in an if/else branch (mutually exclusive recursive calls)
        self.in_if_branch = False
        self.recursive_calls_in_if = 0
        self.recursive_calls_in_else = 0

    # -------- loops --------
    def visit_For(self, node):
        self._enter_loop()
        # Check if loop divides iteration space (e.g., range(0, n, 2) or similar patterns)
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                # Check for step parameter that divides
                if len(node.iter.args) >= 3:
                    self.has_dividing_loop = True
        self.generic_visit(node)
        self._exit_loop()

    def visit_While(self, node):
        self._enter_loop()
        # Check if while loop divides problem (e.g., n //= 2)
        self._check_dividing_condition(node.test)
        # Check loop body for division operations and binary search patterns
        self._check_loop_body_for_division(node.body)
        self._check_binary_search_pattern(node.body)
        self.generic_visit(node)
        self._exit_loop()

    def _check_dividing_condition(self, node):
        """Check if condition involves division (for O(log n) detection)"""
        if isinstance(node, ast.Compare):
            # Check for patterns like n > 0, n != 0 with division in body
            pass
        elif isinstance(node, ast.BoolOp):
            for val in node.values:
                self._check_dividing_condition(val)
    
    def _check_loop_body_for_division(self, body):
        """Check if loop body contains division operations (e.g., n //= 2, n /= 2)"""
        for stmt in body:
            if isinstance(stmt, ast.AugAssign):
                # Check for //= or /= operations
                if isinstance(stmt.op, (ast.FloorDiv, ast.Div)):
                    self.has_dividing_loop = True
            elif isinstance(stmt, ast.Assign):
                # Check for assignments like n = n // 2
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(stmt.value, ast.BinOp):
                            if isinstance(stmt.value.op, (ast.FloorDiv, ast.Div)):
                                # Check if left side is same variable
                                if isinstance(stmt.value.left, ast.Name) and stmt.value.left.id == target.id:
                                    self.has_dividing_loop = True
    
    def _check_binary_search_pattern(self, body):
        """Check if while loop has binary search pattern (l = mid + 1, r = mid - 1)"""
        has_mid_calculation = False
        has_left_update = False
        has_right_update = False
        
        def check_assignments(stmts):
            """Helper to check assignments in statements"""
            nonlocal has_left_update, has_right_update
            for stmt in stmts:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            # Check for mid calculation: mid = (l + r) // 2
                            if target.id == 'mid':
                                if isinstance(stmt.value, ast.BinOp):
                                    if isinstance(stmt.value.op, ast.FloorDiv):
                                        return True  # Found mid calculation
                            # Check for l = mid + 1 or l = mid + k
                            elif target.id in ['l', 'left', 'low']:
                                if isinstance(stmt.value, ast.BinOp):
                                    if isinstance(stmt.value.op, ast.Add):
                                        if (isinstance(stmt.value.left, ast.Name) and 
                                            stmt.value.left.id == 'mid'):
                                            has_left_update = True
                            # Check for r = mid - 1 or r = mid - k
                            elif target.id in ['r', 'right', 'high']:
                                if isinstance(stmt.value, ast.BinOp):
                                    if isinstance(stmt.value.op, ast.Sub):
                                        if (isinstance(stmt.value.left, ast.Name) and 
                                            stmt.value.left.id == 'mid'):
                                            has_right_update = True
                elif isinstance(stmt, ast.If):
                    # Check if/elif/else branches
                    if check_assignments(stmt.body):
                        has_mid_calculation = True
                    if stmt.orelse:
                        for orelse_stmt in stmt.orelse:
                            if isinstance(orelse_stmt, ast.If):
                                # Recursively check elif
                                if check_assignments(orelse_stmt.body):
                                    has_mid_calculation = True
                                if orelse_stmt.orelse:
                                    check_assignments(orelse_stmt.orelse)
                            elif isinstance(orelse_stmt, ast.Assign):
                                check_assignments([orelse_stmt])
            return False
        
        # Check all statements in the loop body
        for stmt in body:
            if isinstance(stmt, ast.Assign):
                if check_assignments([stmt]):
                    has_mid_calculation = True
            elif isinstance(stmt, ast.If):
                if check_assignments(stmt.body):
                    has_mid_calculation = True
                if stmt.orelse:
                    for orelse_stmt in stmt.orelse:
                        if isinstance(orelse_stmt, ast.If):
                            if check_assignments(orelse_stmt.body):
                                has_mid_calculation = True
                            if orelse_stmt.orelse:
                                check_assignments(orelse_stmt.orelse)
                        else:
                            check_assignments([orelse_stmt])
        
        # If we have mid calculation and updates to l or r based on mid, it's binary search
        if has_mid_calculation and (has_left_update or has_right_update):
            self.has_binary_search_pattern = True
            self.has_dividing_loop = True
    
    def _check_function_body_for_division(self, body):
        """Check if function body contains division operations (e.g., mid = n // 2)"""
        for stmt in body:
            if isinstance(stmt, ast.Assign):
                # Check for mid = (left + right) // 2 or similar patterns
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # Check if target is 'mid' or similar
                        if target.id in ['mid', 'middle']:
                            self.has_dividing_recursion = True
                        # Check if assignment involves division
                        if isinstance(stmt.value, ast.BinOp):
                            if isinstance(stmt.value.op, (ast.FloorDiv, ast.Div)):
                                self.has_dividing_recursion = True
            elif isinstance(stmt, ast.If):
                # Recursively check if/else bodies
                self._check_function_body_for_division(stmt.body)
                if stmt.orelse:
                    self._check_function_body_for_division(stmt.orelse)

    def _enter_loop(self):
        self.current_loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.current_loop_depth)

    def _exit_loop(self):
        self.current_loop_depth -= 1
    
    def visit_If(self, node):
        # Track recursive calls in if branch
        prev_if = self.recursive_calls_in_if
        prev_else = self.recursive_calls_in_else
        prev_block = self.recursive_calls_in_current_block
        prev_max = self.max_recursive_calls_in_single_path
        prev_processing = self.processing_if_else
        self.processing_if_else = True
        self.in_if_branch = True
        self.recursive_calls_in_if = 0
        self.recursive_calls_in_current_block = 0
        
        # Visit if body
        for stmt in node.body:
            self.visit(stmt)
        if_calls = self.recursive_calls_in_current_block
        
        # Track recursive calls in else/elif branches
        # Handle elif chains (elif is represented as nested If in orelse)
        # IMPORTANT: elif and else are mutually exclusive, so we need to count them separately
        # and take the max, not the sum
        self.in_if_branch = False
        self.recursive_calls_in_else = 0
        else_calls = 0
        branch_counts = []  # Track counts for each mutually exclusive branch
        
        if node.orelse:
            # Count recursive calls in each mutually exclusive branch (elif or else)
            for stmt in node.orelse:
                if isinstance(stmt, ast.If):
                    # This is an elif - count recursive calls in it
                    prev_block_elif = self.recursive_calls_in_current_block
                    self.recursive_calls_in_current_block = 0
                    # Visit elif body
                    for elif_stmt in stmt.body:
                        self.visit(elif_stmt)
                    elif_calls = self.recursive_calls_in_current_block
                    branch_counts.append(elif_calls)
                    # Visit elif orelse (could be another elif or else)
                    if stmt.orelse:
                        self.recursive_calls_in_current_block = 0
                        for elif_else_stmt in stmt.orelse:
                            self.visit(elif_else_stmt)
                        branch_counts.append(self.recursive_calls_in_current_block)
                    self.recursive_calls_in_current_block = prev_block_elif
                else:
                    # Regular else statement
                    prev_block_else = self.recursive_calls_in_current_block
                    self.recursive_calls_in_current_block = 0
                    self.visit(stmt)
                    branch_counts.append(self.recursive_calls_in_current_block)
                    self.recursive_calls_in_current_block = prev_block_else
            
            # else_calls is the max of all mutually exclusive branches
            else_calls = max(branch_counts) if branch_counts else 0
        
        # If recursive calls are in mutually exclusive branches, 
        # only one path executes, so max is max(if, else), not sum
        # This helps distinguish O(log n) from O(2^n) or O(n log n)
        max_in_branches = max(if_calls, else_calls)
        total_in_branches = if_calls + else_calls
        # Check if we have calls in multiple mutually exclusive branches
        # This happens if:
        # 1. We have calls in both if and else/elif branches, OR
        # 2. We have calls in multiple elif/else branches (len(branch_counts) > 1 with calls)
        has_multiple_branches_with_calls = (
            (if_calls > 0 and else_calls > 0) or  # Calls in both if and else/elif
            (len(branch_counts) > 1 and sum(1 for c in branch_counts if c > 0) > 1)  # Multiple elif/else with calls
        )
        
        if total_in_branches > 0:
            # Mutually exclusive branches - only one executes per call
            if has_multiple_branches_with_calls:
                # We have calls in multiple mutually exclusive branches
                self.has_mutually_exclusive_recursion = True
                # For mutually exclusive branches, only one path executes
                # So the max recursive calls in a single path is max_in_branches (not total)
                # Since we prevented max from being updated during processing_if_else,
                # we need to update it now with the correct value (max of branches, not total)
                self.max_recursive_calls_in_single_path = max(
                    prev_max,  # Keep any max from before this if/else
                    max_in_branches  # Max from this if/else structure
                )
            else:
                # All calls are in one branch, or no calls
                # Update max normally
                self.max_recursive_calls_in_single_path = max(
                    self.max_recursive_calls_in_single_path,
                    max_in_branches
                )
            # Reset the block counter to reflect that only one branch executes
            self.recursive_calls_in_current_block = max_in_branches
        
        self.recursive_calls_in_if = prev_if
        self.recursive_calls_in_else = prev_else
        self.recursive_calls_in_current_block = prev_block
        self.processing_if_else = prev_processing

    # -------- recursion detection --------
    def visit_FunctionDef(self, node):
        # Check if this is a nested function (different from the function we're analyzing)
        func_name_base = self.func_name.split('.')[-1] if self.func_name and '.' in self.func_name else (self.func_name if self.func_name else None)
        is_nested = self.func_name and node.name != func_name_base
        
        if is_nested:
            # This is a nested function - analyze it separately
            nested_name = f"{self.func_name}.{node.name}" if self.func_name else node.name
            self.nested_function_names.add(node.name)
            
            # Analyze nested function for its own recursion
            nested_visitor = CodeVisitor(nested_name)
            nested_visitor.visit(node)
            
            # Propagate nested function's recursion pattern to parent
            if nested_visitor.max_recursive_calls_in_single_path >= 2:
                # Nested function has 2+ recursive calls in single path
                self.max_recursive_calls_in_single_path = max(
                    self.max_recursive_calls_in_single_path,
                    nested_visitor.max_recursive_calls_in_single_path
                )
            # If nested function divides problem, parent also divides (for O(n log n) detection)
            if nested_visitor.has_dividing_recursion:
                self.has_dividing_recursion = True
            if nested_visitor.has_loop_with_recursion:
                self.has_loop_with_recursion = True
            # Also check if nested function body has division operations (like mid calculation)
            self._check_function_body_for_division(node.body)
            # Don't visit the nested function's body again in generic_visit
            return
        
        # This is the function we're analyzing (or no func_name set)
        prev = self.current_recursive_calls
        self.current_recursive_calls = 0
        prev_block_calls = self.recursive_calls_in_current_block
        self.recursive_calls_in_current_block = 0
        prev_body_calls = self.recursive_calls_in_function_body
        self.recursive_calls_in_function_body = []

        self.generic_visit(node)
        
        # Count recursive calls in function body (all calls that can happen in one execution)
        # This helps detect O(2^n) when multiple recursive calls are in the same path
        # Count total recursive calls in body (heuristic: if 2+ calls exist, they can happen in same path)
        body_recursive_count = sum(1 for c in self.recursive_calls_in_function_body if c)

        self.max_recursive_calls_in_scope = max(
            self.max_recursive_calls_in_scope,
            self.current_recursive_calls
        )
        # Update max recursive calls in single path
        # Consider both block-level and function body level
        self.max_recursive_calls_in_single_path = max(
            self.max_recursive_calls_in_single_path,
            self.current_recursive_calls,
            self.recursive_calls_in_current_block,
            body_recursive_count
        )

        self.current_recursive_calls = prev
        self.recursive_calls_in_current_block = prev_block_calls
        self.recursive_calls_in_function_body = prev_body_calls

    def visit_Call(self, node):
        # Check for built-in method calls with known complexities
        if isinstance(node.func, ast.Attribute):
            # Check for .sort(), .sorted() etc. - these are O(n log n)
            if node.func.attr in ['sort']:
                self.has_builtin_sort = True
        
        if self.func_name:
            is_recursive = False
            func_name_to_check = self.func_name.split(".")[-1] if "." in self.func_name else self.func_name
            
            # direct recursion
            if isinstance(node.func, ast.Name):
                if node.func.id == func_name_to_check:
                    is_recursive = True

            # self.method() recursion
            elif isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                ):
                    method_name = func_name_to_check
                    if node.func.attr == method_name:
                        is_recursive = True
            
            if is_recursive:
                self.recursive_calls += 1
                self.current_recursive_calls += 1
                self.recursive_calls_in_current_block += 1
                # Track this recursive call in function body
                self.recursive_calls_in_function_body.append(True)
                
                # Track calls in if/else branches
                if self.in_if_branch:
                    self.recursive_calls_in_if += 1
                else:
                    self.recursive_calls_in_else += 1
                
                # Update max recursive calls in single path (count calls in same block)
                # But don't count mutually exclusive branches together
                # If we're processing an if/else structure, don't update max yet
                # visit_If will handle it after seeing the full structure
                if not self.processing_if_else:
                    # Not in if/else structure - update max directly
                    self.max_recursive_calls_in_single_path = max(
                        self.max_recursive_calls_in_single_path,
                        self.recursive_calls_in_current_block
                    )
                # If processing if/else, don't update max yet - let visit_If handle it
                
                # Check if recursion happens inside a loop (for O(n log n))
                if self.current_loop_depth > 0:
                    self.has_loop_with_recursion = True
                # Check if recursion divides problem size (for O(log n))
                # Look for patterns like func(n//2), func(mid), func(left), func(right)
                self._check_dividing_recursion(node)
            else:
                # Track non-recursive calls too to reset block counter at appropriate points
                self.recursive_calls_in_function_body.append(False)

        self.generic_visit(node)
    
    def _check_dividing_recursion(self, node):
        """Check if recursive call divides problem size (e.g., n//2, mid, left/right)"""
        # Check arguments for division patterns
        for arg in node.args:
            if isinstance(arg, ast.BinOp):
                # Check for division operations: n // 2, n / 2, etc.
                if isinstance(arg.op, (ast.FloorDiv, ast.Div)):
                    self.has_dividing_recursion = True
                # Check for subtraction/addition with mid (mid - 1, mid + 1) - these indicate binary search
                elif isinstance(arg.op, (ast.Sub, ast.Add)):
                    # If one operand is 'mid', it's likely dividing the search space
                    if (isinstance(arg.left, ast.Name) and arg.left.id == 'mid') or \
                       (isinstance(arg.right, ast.Name) and arg.right.id == 'mid'):
                        self.has_dividing_recursion = True
            elif isinstance(arg, ast.Name):
                # Could be mid, left, right - heuristic: if it's a common divide pattern
                if arg.id in ['mid', 'left', 'right', 'middle']:
                    self.has_dividing_recursion = True
            elif isinstance(arg, ast.Subscript):
                # Array slicing often divides problem (e.g., arr[:mid], arr[mid:])
                self.has_dividing_recursion = True
            elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                # Check for i + 1, i + k patterns (incrementing, not dividing)
                # This is NOT dividing, so don't set has_dividing_recursion
                pass

class ASTAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.results = []
        self.current_class_name = None
        self.has_functions_or_classes = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.has_functions_or_classes = True
        full_name = f"{self.current_class_name}.{node.name}" if self.current_class_name else node.name

        # Use enhanced analyzer (primary method)
        try:
            from .enhanced_analyzer import EnhancedCodeVisitor, compute_time_complexity, compute_space_complexity
            enhanced_visitor = EnhancedCodeVisitor(full_name)
            enhanced_visitor.visit(node)
            big_o = str(compute_time_complexity(enhanced_visitor))
            space_o = str(compute_space_complexity(enhanced_visitor))
            max_loop_depth = len(enhanced_visitor.loops)
            recursive_calls = enhanced_visitor.recursion_info.branching_factor
        except Exception:
            # Fallback to original heuristic analyzer
            visitor = CodeVisitor(full_name)
            visitor.visit(node)
            big_o = estimate_time_complexity(
                visitor.max_loop_depth, 
                visitor.recursive_calls,
                visitor.max_recursive_calls_in_single_path,
                visitor.has_dividing_recursion,
                visitor.has_dividing_loop,
                visitor.has_loop_with_recursion,
                visitor.has_mutually_exclusive_recursion,
                visitor.has_builtin_sort,
                visitor.has_binary_search_pattern
            )
            space_o = estimate_space_complexity(visitor.recursive_calls, visitor.max_loop_depth)
            max_loop_depth = visitor.max_loop_depth
            recursive_calls = visitor.recursive_calls

        self.results.append(
            FunctionAnalysis(
                name=full_name,
                time_complexity=big_o,
                space_complexity=space_o,
                max_loop_depth=max_loop_depth,
                recursive_calls=recursive_calls,
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

        # Use enhanced analyzer (primary method)
        try:
            from .enhanced_analyzer import EnhancedCodeVisitor, compute_time_complexity, compute_space_complexity
            enhanced_visitor = EnhancedCodeVisitor(full_name)
            enhanced_visitor.visit(node)
            big_o = str(compute_time_complexity(enhanced_visitor))
            space_o = str(compute_space_complexity(enhanced_visitor))
            max_loop_depth = len(enhanced_visitor.loops)
            recursive_calls = enhanced_visitor.recursion_info.branching_factor
        except Exception:
            # Fallback to original heuristic analyzer
            visitor = CodeVisitor(full_name)
            visitor.visit(node)
            big_o = estimate_time_complexity(
                visitor.max_loop_depth, 
                visitor.recursive_calls,
                visitor.max_recursive_calls_in_single_path,
                visitor.has_dividing_recursion,
                visitor.has_dividing_loop,
                visitor.has_loop_with_recursion,
                visitor.has_mutually_exclusive_recursion,
                visitor.has_builtin_sort,
                visitor.has_binary_search_pattern
            )
            space_o = estimate_space_complexity(visitor.recursive_calls, visitor.max_loop_depth)
            max_loop_depth = visitor.max_loop_depth
            recursive_calls = visitor.recursive_calls

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
        # Try enhanced analyzer first
        try:
            from .enhanced_analyzer import EnhancedCodeVisitor, compute_time_complexity, compute_space_complexity
            enhanced_visitor = EnhancedCodeVisitor()
            enhanced_visitor.visit(tree)
            big_o = str(compute_time_complexity(enhanced_visitor))
            space_o = str(compute_space_complexity(enhanced_visitor))
            max_loop_depth = 0
            recursive_calls = 0
        except Exception:
            # Fallback to original heuristic analyzer
            visitor = CodeVisitor()
            visitor.visit(tree)
            big_o = estimate_time_complexity(
                visitor.max_loop_depth, 
                visitor.recursive_calls,
                visitor.max_recursive_calls_in_single_path,
                visitor.has_dividing_recursion,
                visitor.has_dividing_loop,
                visitor.has_loop_with_recursion,
                visitor.has_mutually_exclusive_recursion,
                visitor.has_builtin_sort,
                visitor.has_binary_search_pattern
            )
            space_o = estimate_space_complexity(visitor.recursive_calls, visitor.max_loop_depth)
            max_loop_depth = visitor.max_loop_depth
            recursive_calls = visitor.recursive_calls

        analyzer.results.append(
            FunctionAnalysis(
                name="<main>",
                time_complexity=big_o,
                space_complexity=space_o,
                max_loop_depth=max_loop_depth,
                recursive_calls=recursive_calls,
            )
        )

    return analyzer.results


