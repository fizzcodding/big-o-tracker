
import ast
from typing import Dict, List, Optional, Set, Tuple
from .symbolic import (
    SymbolicComplexity, ComplexityType, RecurrenceSolver,
    DataStructureCosts, infer_input_size
)


class LoopInfo:
    def __init__(self):
        self.bound_var: Optional[str]
        self.bound_type: Optional[str] = None  
        self.is_nested: bool = False
        self.inner_complexity: Optional[SymbolicComplexity] = None


class RecursionInfo:
    """Information about recursion"""
    def __init__(self):
        self.branching_factor: int = 0  
        self.problem_reduction: Optional[str] = None  
        self.recurrence_type: Optional[str] = None  # "linear", "divide_conquer", "backtracking"
        self.has_backtracking_pattern: bool = False  # append/pop, mark/unmark
        self.work_per_level: Optional[SymbolicComplexity] = None


class EnhancedCodeVisitor(ast.NodeVisitor):
    """Enhanced visitor that collects detailed complexity information"""
    
    def __init__(self, func_name: str = None):
        self.func_name = func_name
        
        # Input size tracking
        self.input_vars: Dict[str, str] = {}  # param_name -> symbolic_var
        
        # Loop analysis
        self.loops: List[LoopInfo] = []
        self.current_loop_depth = 0
        self.sequential_loops: List[LoopInfo] = []  # Loops at same level
        
        # Recursion analysis
        self.recursion_info = RecursionInfo()
        self.recursive_calls: List[ast.Call] = []
        self.in_recursive_function = False
        
        # Operation costs
        self.operation_costs: List[SymbolicComplexity] = []
        
        # Space complexity
        self.auxiliary_space: List[SymbolicComplexity] = []
        self.recursion_depth: Optional[SymbolicComplexity] = None
        
        # Branch analysis
        self.branch_complexities: List[SymbolicComplexity] = []
        self.in_conditional = False
        
        # Backtracking detection
        self.has_mutable_state = False
        self.has_undo_operations = False
        
        # Binary search pattern detection
        self.has_binary_search_pattern = False
    
    def visit_FunctionDef(self, node):
        """Analyze function parameters for input size inference"""
        # Check if this is a nested function
        func_name_base = self.func_name.split('.')[-1] if self.func_name and '.' in self.func_name else (self.func_name if self.func_name else None)
        is_nested = self.func_name and node.name != func_name_base
        
        if is_nested:
            # Analyze nested function separately
            nested_name = f"{self.func_name}.{node.name}" if self.func_name else node.name
            nested_visitor = EnhancedCodeVisitor(nested_name)
            nested_visitor.visit(node)
            
            # Propagate nested function's characteristics
            if nested_visitor.recursion_info.branching_factor > 0:
                # If nested function has recursion, it contributes to complexity
                if nested_visitor.recursion_info.branching_factor > self.recursion_info.branching_factor:
                    self.recursion_info.branching_factor = nested_visitor.recursion_info.branching_factor
                if nested_visitor.recursion_info.problem_reduction:
                    self.recursion_info.problem_reduction = nested_visitor.recursion_info.problem_reduction
                if nested_visitor.recursion_info.recurrence_type:
                    self.recursion_info.recurrence_type = nested_visitor.recursion_info.recurrence_type
            if nested_visitor.has_mutable_state:
                self.has_mutable_state = True
            if nested_visitor.has_undo_operations:
                self.has_undo_operations = True
            # Don't visit nested function body again
            return
        
        # Infer input sizes from parameters
        for arg in node.args.args:
            param_name = arg.arg
            # Try to infer type from annotations or name
            symbolic_var = infer_input_size(param_name)
            self.input_vars[param_name] = symbolic_var
        
        self.in_recursive_function = (self.func_name and 
                                     node.name == self.func_name.split('.')[-1])
        
        # Don't reset recursion_info - we want to track it for this function
        # Only save/restore if we're in a nested context
        prev_loops = self.loops[:]
        prev_mutable = self.has_mutable_state
        prev_undo = self.has_undo_operations
        
        # Reset only mutable state tracking (not recursion - that's per function)
        self.has_mutable_state = False
        self.has_undo_operations = False
        
        self.generic_visit(node)
        
        # Don't restore loops - we want to keep them for complexity calculation
        # Only restore mutable state (for parent context)
        self.has_mutable_state = prev_mutable
        self.has_undo_operations = prev_undo
    
    def visit_For(self, node):
        """Analyze for loop bounds"""
        loop_info = LoopInfo()
        self.current_loop_depth += 1
        loop_info.is_nested = (self.current_loop_depth > 1)
        
        # Analyze loop bound
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                # range(n) → O(n)
                if len(node.iter.args) == 1:
                    arg = node.iter.args[0]
                    if isinstance(arg, ast.Name):
                        loop_info.bound_var = arg.id
                        loop_info.bound_type = "n"
                    elif isinstance(arg, ast.Constant):
                        loop_info.bound_type = "constant"
                    elif isinstance(arg, ast.Call):
                        # len(arr) or len(matrix[0])
                        if isinstance(arg.func, ast.Name) and arg.func.id == 'len':
                            if arg.args:
                                # Check if it's len(matrix[0]) - different dimension
                                if isinstance(arg.args[0], ast.Subscript):
                                    # len(matrix[0]) - this is 'm' dimension
                                    loop_info.bound_type = "m"
                                    loop_info.bound_var = "m"
                                else:
                                    loop_info.bound_type = "n"
                            else:
                                loop_info.bound_type = "n"
                        else:
                            loop_info.bound_type = "n"  # Default
                    else:
                        loop_info.bound_type = "n"  # Default
                # range(i, n) → O(n)
                elif len(node.iter.args) == 2:
                    # Check second arg for variable name
                    second_arg = node.iter.args[1]
                    if isinstance(second_arg, ast.Call):
                        # len(arr) or len(matrix[0])
                        if isinstance(second_arg.func, ast.Name) and second_arg.func.id == 'len':
                            if second_arg.args:
                                if isinstance(second_arg.args[0], ast.Subscript):
                                    # len(matrix[0]) - different dimension
                                    loop_info.bound_type = "m"  # Different variable
                                else:
                                    loop_info.bound_type = "n"
                    else:
                        loop_info.bound_type = "n"
                # range(0, n, step) → O(n/step) ≈ O(n)
                elif len(node.iter.args) == 3:
                    loop_info.bound_type = "n"
        elif isinstance(node.iter, ast.Name):
            # for x in arr: - iterate over collection
            loop_info.bound_type = "n"
        
        self.loops.append(loop_info)
        prev_depth = self.current_loop_depth
        
        self.generic_visit(node)
        
        self.current_loop_depth = prev_depth
        # Keep loop_info in list - don't remove it (needed for complexity calculation)
    
    def visit_While(self, node):
        """Analyze while loop - check for binary search pattern"""
        loop_info = LoopInfo()
        self.current_loop_depth += 1
        loop_info.is_nested = (self.current_loop_depth > 1)
        
        # Check for binary search pattern: while l <= r with mid calculation
        # Pattern: mid = (l + r) // 2, l = mid + 1, r = mid - 1
        has_mid = False
        has_left_update = False
        has_right_update = False
        
        def check_binary_search_pattern(body):
            """Recursively check for binary search pattern"""
            nonlocal has_mid, has_left_update, has_right_update
            for stmt in body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            if target.id == 'mid':
                                if isinstance(stmt.value, ast.BinOp):
                                    if isinstance(stmt.value.op, ast.FloorDiv):
                                        has_mid = True
                            elif target.id in ['l', 'left', 'low']:
                                if isinstance(stmt.value, ast.BinOp):
                                    if isinstance(stmt.value.op, ast.Add):
                                        # Check if it's mid + something
                                        if (isinstance(stmt.value.left, ast.Name) and
                                            stmt.value.left.id == 'mid'):
                                            has_left_update = True
                            elif target.id in ['r', 'right', 'high']:
                                if isinstance(stmt.value, ast.BinOp):
                                    if isinstance(stmt.value.op, ast.Sub):
                                        # Check if it's mid - something
                                        if (isinstance(stmt.value.left, ast.Name) and
                                            stmt.value.left.id == 'mid'):
                                            has_right_update = True
                elif isinstance(stmt, ast.If):
                    # Check if/else branches
                    check_binary_search_pattern(stmt.body)
                    if stmt.orelse:
                        check_binary_search_pattern(stmt.orelse)
        
        check_binary_search_pattern(node.body)
        
        if has_mid and (has_left_update or has_right_update):
            loop_info.bound_type = "log n"  # Binary search
            self.has_binary_search_pattern = True
        
        # Check for n //= k pattern
        for stmt in node.body:
            if isinstance(stmt, ast.AugAssign):
                if isinstance(stmt.op, (ast.FloorDiv, ast.Div)):
                    loop_info.bound_type = "log n"
        
        self.loops.append(loop_info)
        prev_depth = self.current_loop_depth
        
        self.generic_visit(node)
        
        self.current_loop_depth = prev_depth
        # Keep loop_info in list - don't remove it (needed for complexity calculation)
    
    def visit_Call(self, node):
        """Track function calls and data structure operations"""
        # Check for data structure operations
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                operation = f"{obj_name}.{attr_name}"
                cost = DataStructureCosts.get_cost(operation)
                if cost:
                    self.operation_costs.append(cost)
            
            # Check for .sort()
            if attr_name == 'sort':
                self.operation_costs.append(
                    SymbolicComplexity(ComplexityType.LINEARITHMIC)
                )
        
        # Check for built-in functions
        if isinstance(node.func, ast.Name):
            cost = DataStructureCosts.get_cost(node.func.id)
            if cost:
                self.operation_costs.append(cost)
        
        # Track recursive calls - MUST check before generic_visit
        if self.func_name:
            func_name_base = self.func_name.split('.')[-1] if '.' in self.func_name else self.func_name
            is_recursive = False
            
            if isinstance(node.func, ast.Name):
                if node.func.id == func_name_base:
                    is_recursive = True
            elif isinstance(node.func, ast.Attribute):
                if (isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == "self"):
                    method_name = func_name_base
                    if node.func.attr == method_name:
                        is_recursive = True
            
            if is_recursive:
                self.recursive_calls.append(node)
                self.recursion_info.branching_factor += 1
                
                # Analyze problem reduction from arguments
                self._analyze_problem_reduction(node)
        
        # Continue visiting to find nested calls
        self.generic_visit(node)
        
        self.generic_visit(node)
    
    def _analyze_problem_reduction(self, call_node: ast.Call):
        """Analyze how the problem size is reduced in recursive call"""
        for arg in call_node.args:
            # Check for n-1, n+1 patterns
            if isinstance(arg, ast.BinOp):
                if isinstance(arg.op, ast.Sub):
                    if isinstance(arg.left, ast.Name):
                        if isinstance(arg.right, ast.Constant) and arg.right.value == 1:
                            self.recursion_info.problem_reduction = "n-1"
                elif isinstance(arg.op, ast.Add):
                    if isinstance(arg.left, ast.Name):
                        if isinstance(arg.right, ast.Constant) and arg.right.value == 1:
                            self.recursion_info.problem_reduction = "index+1"
                elif isinstance(arg.op, (ast.FloorDiv, ast.Div)):
                    if isinstance(arg.right, ast.Constant):
                        if arg.right.value == 2:
                            self.recursion_info.problem_reduction = "n/2"
                        else:
                            self.recursion_info.problem_reduction = f"n/{arg.right.value}"
            
            # Check for array slicing (divide & conquer)
            elif isinstance(arg, ast.Subscript):
                self.recursion_info.problem_reduction = "n/2"  # Heuristic
                self.recursion_info.recurrence_type = "divide_conquer"
            
            # Check for list slicing with len() reduction
            elif isinstance(arg, ast.Call):
                # len(remaining) or similar - problem size reduction
                if isinstance(arg.func, ast.Name) and arg.func.id == 'len':
                    # This suggests the problem size is being reduced
                    if not self.recursion_info.problem_reduction:
                        self.recursion_info.problem_reduction = "n-1"
            
            # Check for list slicing operations (remaining[:i] + remaining[i+1:])
            elif isinstance(arg, ast.BinOp):
                if isinstance(arg.op, ast.Add):
                    # List concatenation with slices suggests permutation pattern
                    if (isinstance(arg.left, ast.Subscript) or 
                        isinstance(arg.right, ast.Subscript)):
                        # This is likely a permutation backtracking pattern
                        if not self.recursion_info.problem_reduction:
                            self.recursion_info.problem_reduction = "n-1"
    
    def visit_If(self, node):
        """Track conditional branches - take max complexity"""
        self.in_conditional = True
        prev_branches = self.branch_complexities[:]
        self.branch_complexities = []
        
        # Analyze if branch
        for stmt in node.body:
            self.visit(stmt)
        
        # Analyze elif/else branches
        if node.orelse:
            for stmt in node.orelse:
                self.visit(stmt)
        
        self.in_conditional = False
        self.branch_complexities = prev_branches
    
    def visit_AugAssign(self, node):
        """Track mutable state operations (for backtracking detection)"""
        if isinstance(node.target, ast.Attribute):
            if node.target.attr in ['append', 'pop', 'add', 'remove']:
                self.has_mutable_state = True
                if node.target.attr in ['pop', 'remove']:
                    self.has_undo_operations = True
    
    def visit_Assign(self, node):
        """Track list operations in assignments"""
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if target.attr in ['append', 'pop', 'add', 'remove']:
                    self.has_mutable_state = True
                    if target.attr in ['pop', 'remove']:
                        self.has_undo_operations = True
            # Check for list slicing/copying (backtracking pattern)
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Attribute):
                    if node.value.func.attr in ['copy', '__getitem__']:
                        self.has_mutable_state = True
            # Check for list concatenation (path + [x])
            if isinstance(node.value, ast.BinOp):
                if isinstance(node.value.op, ast.Add):
                    if isinstance(node.value.left, ast.List) or isinstance(node.value.right, ast.List):
                        self.has_mutable_state = True


def compute_time_complexity(visitor: EnhancedCodeVisitor) -> SymbolicComplexity:
    """
    Compute time complexity from collected information.
    Follows the specification rules.
    """
    complexity = SymbolicComplexity(ComplexityType.CONSTANT)
    
    # 1. Check for built-in operations first (highest priority for operations like sort)
    for op_cost in visitor.operation_costs:
        # For operations like sort(), they dominate
        if op_cost.expr_type == ComplexityType.LINEARITHMIC:
            return op_cost
        complexity = complexity.add(op_cost)
    
    # 1.5. Check for binary search pattern in while loops (before recursion/loops)
    # Binary search: while loop with mid = (l+r)//2, l = mid+1, r = mid-1
    if hasattr(visitor, 'has_binary_search_pattern') and visitor.has_binary_search_pattern:
        if visitor.recursion_info.branching_factor == 0:
            return SymbolicComplexity(ComplexityType.LOGARITHMIC)
    
    # 2. Handle recursion (highest priority for recursive algorithms)
    if visitor.recursion_info.branching_factor > 0:
        recurrence_type = visitor.recursion_info.recurrence_type or "linear"
        
        # Check for backtracking pattern FIRST (permutations, subsets)
        # Permutations: loop inside recursion that iterates over remaining elements
        # Subsets: two recursive calls (take/not take)
        has_loop_in_recursion = len(visitor.loops) > 0
        
        if visitor.recursion_info.branching_factor >= 2:
            # Check for backtracking pattern
            # Permutations have: recursion + loop over remaining elements + mutable state
            # Subsets have: 2 recursive calls + mutable state with undo
            if visitor.has_mutable_state:
                recurrence_type = "backtracking"
                # If there's a loop iterating over remaining elements, it's permutations
                # Permutations: loop iterates len(remaining) times, recursively calls with n-1
                if has_loop_in_recursion:
                    # Permutations: T(n) = n * T(n-1) → O(n!)
                    complexity = SymbolicComplexity(ComplexityType.FACTORIAL)
                elif visitor.has_undo_operations:
                    # Subsets: T(n) = 2 * T(n-1) → O(2^n)
                    complexity = RecurrenceSolver.solve(
                        "backtracking", 2, "n-1"
                    )
                else:
                    # Other backtracking with 2+ calls
                    complexity = RecurrenceSolver.solve(
                        "backtracking", visitor.recursion_info.branching_factor, "n-1"
                    )
            else:
                # Divide & conquer
                if visitor.recursion_info.problem_reduction == "n/2":
                    recurrence_type = "divide_conquer"
                    work = SymbolicComplexity(ComplexityType.LINEAR)
                    complexity = RecurrenceSolver.solve(
                        recurrence_type,
                        visitor.recursion_info.branching_factor,
                        visitor.recursion_info.problem_reduction or "n-1",
                        work
                    )
                else:
                    # Exponential recursion
                    complexity = RecurrenceSolver.solve(
                        recurrence_type,
                        visitor.recursion_info.branching_factor,
                        visitor.recursion_info.problem_reduction or "n-1"
                    )
        elif visitor.recursion_info.branching_factor == 1:
            # Single recursive call - check if there's a loop (permutations)
            # Permutations pattern: for loop inside recursive function
            if has_loop_in_recursion and visitor.has_mutable_state:
                # Permutations with loop: T(n) = n * T(n-1) → O(n!)
                complexity = SymbolicComplexity(ComplexityType.FACTORIAL)
            else:
                # Single recursive call
                complexity = RecurrenceSolver.solve(
                    recurrence_type,
                    1,
                    visitor.recursion_info.problem_reduction or "n-1"
                )
        else:
            # No recursion detected but branching_factor is 0 - shouldn't happen
            pass
        
        # Add work per level if specified
        if visitor.recursion_info.work_per_level:
            complexity = complexity.add(visitor.recursion_info.work_per_level)
    
    # 3. Handle loops (if no recursion dominates or recursion is constant)
    # Only analyze loops if recursion didn't produce a meaningful complexity
    recursion_dominates = (visitor.recursion_info.branching_factor > 0 and 
                          complexity.expr_type != ComplexityType.CONSTANT)
    
    if not recursion_dominates:
        if visitor.loops:
            # Separate nested and sequential loops
            nested_loops = [l for l in visitor.loops if l.is_nested]
            sequential_loops = [l for l in visitor.loops if not l.is_nested]
            
            # Sequential loops: O(max(f, g)) - worst case
            seq_complexity = SymbolicComplexity(ComplexityType.CONSTANT)
            for loop in sequential_loops:
                if loop.bound_type == "n":
                    seq_complexity = seq_complexity.max(
                        SymbolicComplexity(ComplexityType.LINEAR)
                    )
                elif loop.bound_type == "log n":
                    seq_complexity = seq_complexity.max(
                        SymbolicComplexity(ComplexityType.LOGARITHMIC)
                    )
                elif loop.bound_type == "constant":
                    pass  # O(1) doesn't affect max
                else:
                    seq_complexity = seq_complexity.max(
                        SymbolicComplexity(ComplexityType.LINEAR)
                    )
            
            # Nested loops: O(f * g) - multiply complexities
            # If we have nested loops, multiply all loops together
            if nested_loops:
                nested_complexity = SymbolicComplexity(ComplexityType.CONSTANT)
                bound_vars = set()
                has_m = False
                # Multiply all loops (both sequential and nested)
                for loop in visitor.loops:
                    if loop.bound_type == "m":
                        has_m = True
                        bound_vars.add("m")
                    if loop.bound_type == "n" or loop.bound_type is None or loop.bound_type == "m":
                        # Default to linear if not specified
                        nested_complexity = nested_complexity.multiply(
                            SymbolicComplexity(ComplexityType.LINEAR)
                        )
                    elif loop.bound_type == "log n":
                        nested_complexity = nested_complexity.multiply(
                            SymbolicComplexity(ComplexityType.LOGARITHMIC)
                        )
                    # constant bounds don't multiply
                
                # If we have different variables (n and m), create multivariate
                if has_m:
                    vars_dict = {"n": 1, "m": 1}
                    nested_complexity = SymbolicComplexity(
                        ComplexityType.MULTIVARIATE,
                        vars=vars_dict
                    )
                
                # Nested complexity dominates
                complexity = complexity.max(nested_complexity)
            else:
                # Only sequential loops
                complexity = complexity.max(seq_complexity)
    
    # 4. Take max of branches (worst case)
    for branch_comp in visitor.branch_complexities:
        complexity = complexity.max(branch_comp)
    
    return complexity


def compute_space_complexity(visitor: EnhancedCodeVisitor) -> SymbolicComplexity:
    """
    Compute space complexity.
    Includes: recursion stack, auxiliary structures, output space.
    """
    space = SymbolicComplexity(ComplexityType.CONSTANT)
    
    # 1. Recursion stack depth
    if visitor.recursion_info.branching_factor > 0:
        if visitor.recursion_info.problem_reduction == "n-1":
            space = SymbolicComplexity(ComplexityType.LINEAR)
        elif visitor.recursion_info.problem_reduction == "n/2":
            space = SymbolicComplexity(ComplexityType.LOGARITHMIC)
        else:
            space = SymbolicComplexity(ComplexityType.LINEAR)
    
    # 2. Auxiliary data structures
    for aux in visitor.auxiliary_space:
        space = space.max(aux)
    
    # 3. Output space (if generating results)
    # This would need more analysis to detect
    
    return space
