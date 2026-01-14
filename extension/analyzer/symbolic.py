"""
Symbolic complexity analysis system.
Handles symbolic expressions, recurrence relations, and proper Big-O calculation.
"""
from enum import Enum
from typing import Optional, Dict, Set, List, Tuple
import re


class ComplexityType(Enum):
    """Types of complexity expressions"""
    CONSTANT = "O(1)"
    LOGARITHMIC = "O(log n)"
    SQRT = "O(√n)"
    LINEAR = "O(n)"
    LINEARITHMIC = "O(n log n)"
    POLYNOMIAL = "O(n^k)"
    EXPONENTIAL = "O(2^n)"
    FACTORIAL = "O(n!)"
    MULTIVARIATE = "O(...)"


class SymbolicComplexity:
    """Represents a symbolic complexity expression"""
    
    def __init__(self, expr_type: ComplexityType, base_var: str = "n", 
                 degree: Optional[int] = None, vars: Optional[Dict[str, int]] = None,
                 description: str = ""):
        self.expr_type = expr_type
        self.base_var = base_var
        self.degree = degree  # For polynomial: n^k
        self.vars = vars or {}  # For multivariate: {var: degree}
        self.description = description
    
    def __str__(self) -> str:
        """Convert to Big-O notation string"""
        if self.expr_type == ComplexityType.CONSTANT:
            return "O(1)"
        elif self.expr_type == ComplexityType.LOGARITHMIC:
            return f"O(log {self.base_var})"
        elif self.expr_type == ComplexityType.SQRT:
            return f"O(√{self.base_var})"
        elif self.expr_type == ComplexityType.LINEAR:
            return f"O({self.base_var})"
        elif self.expr_type == ComplexityType.LINEARITHMIC:
            return f"O({self.base_var} log {self.base_var})"
        elif self.expr_type == ComplexityType.POLYNOMIAL:
            if self.degree == 2:
                return f"O({self.base_var}^2)"
            return f"O({self.base_var}^{self.degree})"
        elif self.expr_type == ComplexityType.EXPONENTIAL:
            return f"O(2^{self.base_var})"
        elif self.expr_type == ComplexityType.FACTORIAL:
            return f"O({self.base_var}!)"
        elif self.expr_type == ComplexityType.MULTIVARIATE:
            # Build expression like O(n*m) or O(V+E)
            terms = []
            for var, deg in sorted(self.vars.items()):
                if deg == 1:
                    terms.append(var)
                else:
                    terms.append(f"{var}^{deg}")
            if len(terms) == 1:
                return f"O({terms[0]})"
            # Check if multiplication or addition
            # For now, assume multiplication for different variables
            return f"O({' * '.join(terms)})"
        return "O(1)"
    
    def max(self, other: 'SymbolicComplexity') -> 'SymbolicComplexity':
        """Take maximum of two complexities (worst case)"""
        # Order: 1 < log n < √n < n < n log n < n^k < 2^n < n!
        order = {
            ComplexityType.CONSTANT: 0,
            ComplexityType.LOGARITHMIC: 1,
            ComplexityType.SQRT: 2,
            ComplexityType.LINEAR: 3,
            ComplexityType.LINEARITHMIC: 4,
            ComplexityType.POLYNOMIAL: 5,
            ComplexityType.EXPONENTIAL: 6,
            ComplexityType.FACTORIAL: 7,
            ComplexityType.MULTIVARIATE: 8,
        }
        
        if order.get(self.expr_type, 0) >= order.get(other.expr_type, 0):
            return self
        return other
    
    def multiply(self, other: 'SymbolicComplexity') -> 'SymbolicComplexity':
        """Multiply two complexities (nested execution)"""
        # O(1) * anything = anything
        if self.expr_type == ComplexityType.CONSTANT:
            return other
        if other.expr_type == ComplexityType.CONSTANT:
            return self
        
        # O(n) * O(n) = O(n^2)
        if (self.expr_type == ComplexityType.LINEAR and 
            other.expr_type == ComplexityType.LINEAR and
            self.base_var == other.base_var):
            return SymbolicComplexity(ComplexityType.POLYNOMIAL, self.base_var, 2)
        
        # O(n) * O(log n) = O(n log n)
        if (self.expr_type == ComplexityType.LINEAR and 
            other.expr_type == ComplexityType.LOGARITHMIC and
            self.base_var == other.base_var):
            return SymbolicComplexity(ComplexityType.LINEARITHMIC, self.base_var)
        
        # O(n) * O(m) = O(n*m)
        if (self.expr_type == ComplexityType.LINEAR and 
            other.expr_type == ComplexityType.LINEAR and
            self.base_var != other.base_var):
            return SymbolicComplexity(
                ComplexityType.MULTIVARIATE,
                vars={self.base_var: 1, other.base_var: 1}
            )
        
        # For polynomial, multiply degrees
        if self.expr_type == ComplexityType.POLYNOMIAL:
            if other.expr_type == ComplexityType.POLYNOMIAL:
                if self.base_var == other.base_var:
                    return SymbolicComplexity(
                        ComplexityType.POLYNOMIAL,
                        self.base_var,
                        (self.degree or 1) + (other.degree or 1)
                    )
        
        # Default: return the more complex one
        return self.max(other)
    
    def add(self, other: 'SymbolicComplexity') -> 'SymbolicComplexity':
        """Add two complexities (sequential execution)"""
        # O(f) + O(g) = O(max(f, g))
        return self.max(other)


class RecurrenceSolver:
    """Solves recurrence relations to determine complexity"""
    
    @staticmethod
    def solve(recurrence_type: str, branching_factor: int, 
              problem_reduction: str, work_per_level: Optional[SymbolicComplexity] = None) -> SymbolicComplexity:
        """
        Solve recurrence relations.
        
        recurrence_type: "linear", "divide_conquer", "backtracking"
        branching_factor: number of recursive calls per frame
        problem_reduction: "n-1", "n/2", "n/k", "index+1"
        work_per_level: work done at each level (for divide & conquer)
        """
        work = work_per_level or SymbolicComplexity(ComplexityType.CONSTANT)
        
        if recurrence_type == "linear":
            # T(n) = T(n-1) + O(1) → O(n) (single call)
            if problem_reduction == "n-1":
                if branching_factor == 1:
                    return SymbolicComplexity(ComplexityType.LINEAR)
                # T(n) = 2T(n-1) → O(2^n) (multiple calls)
                elif branching_factor >= 2:
                    return SymbolicComplexity(ComplexityType.EXPONENTIAL)
            # T(n) = T(n/k) + O(1) → O(log n)
            if problem_reduction.startswith("n/"):
                return SymbolicComplexity(ComplexityType.LOGARITHMIC)
        
        elif recurrence_type == "divide_conquer":
            # T(n) = 2T(n/2) + O(n) → O(n log n)
            if branching_factor == 2 and problem_reduction == "n/2":
                if work.expr_type == ComplexityType.LINEAR:
                    return SymbolicComplexity(ComplexityType.LINEARITHMIC)
                if work.expr_type == ComplexityType.CONSTANT:
                    return SymbolicComplexity(ComplexityType.LINEAR)
            
            # T(n) = T(n/2) + O(1) → O(log n)
            if branching_factor == 1 and problem_reduction == "n/2":
                return SymbolicComplexity(ComplexityType.LOGARITHMIC)
        
        elif recurrence_type == "backtracking":
            # T(n) = kT(n-1) → O(k^n)
            if problem_reduction == "n-1":
                if branching_factor == 2:
                    return SymbolicComplexity(ComplexityType.EXPONENTIAL)
                if branching_factor > 2:
                    return SymbolicComplexity(ComplexityType.EXPONENTIAL)  # O(k^n)
            
            # T(n) = nT(n-1) → O(n!)
            if problem_reduction == "n-1" and branching_factor > 10:  # Heuristic for n!
                return SymbolicComplexity(ComplexityType.FACTORIAL)
        
        # For linear recurrence with 2+ branches and n-1 reduction → exponential
        if recurrence_type == "linear" and branching_factor >= 2:
            if problem_reduction == "n-1":
                # T(n) = 2T(n-1) → O(2^n)
                return SymbolicComplexity(ComplexityType.EXPONENTIAL)
        
        # Default fallback
        if branching_factor >= 2:
            return SymbolicComplexity(ComplexityType.EXPONENTIAL)
        return SymbolicComplexity(ComplexityType.LINEAR)


class DataStructureCosts:
    """Built-in cost table for data structure operations"""
    
    COSTS = {
        # List operations
        'list.append': SymbolicComplexity(ComplexityType.CONSTANT),
        'list.pop': SymbolicComplexity(ComplexityType.CONSTANT),  # end
        'list.pop(0)': SymbolicComplexity(ComplexityType.LINEAR),  # beginning
        'list.insert(0)': SymbolicComplexity(ComplexityType.LINEAR),
        'list.sort': SymbolicComplexity(ComplexityType.LINEARITHMIC),
        'list.index': SymbolicComplexity(ComplexityType.LINEAR),
        'list.count': SymbolicComplexity(ComplexityType.LINEAR),
        
        # Dict/Set operations
        'dict.get': SymbolicComplexity(ComplexityType.CONSTANT),
        'dict.set': SymbolicComplexity(ComplexityType.CONSTANT),
        'dict.__getitem__': SymbolicComplexity(ComplexityType.CONSTANT),
        'dict.__setitem__': SymbolicComplexity(ComplexityType.CONSTANT),
        'set.add': SymbolicComplexity(ComplexityType.CONSTANT),
        'set.remove': SymbolicComplexity(ComplexityType.CONSTANT),
        'set.intersection': SymbolicComplexity(ComplexityType.LINEAR),
        
        # String operations
        'str.find': SymbolicComplexity(ComplexityType.LINEAR),
        'str.replace': SymbolicComplexity(ComplexityType.LINEAR),
        'str.split': SymbolicComplexity(ComplexityType.LINEAR),
        
        # Built-in functions
        'sorted': SymbolicComplexity(ComplexityType.LINEARITHMIC),
        'max': SymbolicComplexity(ComplexityType.LINEAR),
        'min': SymbolicComplexity(ComplexityType.LINEAR),
        'sum': SymbolicComplexity(ComplexityType.LINEAR),
        'len': SymbolicComplexity(ComplexityType.CONSTANT),
    }
    
    @staticmethod
    def get_cost(operation: str) -> Optional[SymbolicComplexity]:
        """Get cost for a data structure operation"""
        return DataStructureCosts.COSTS.get(operation)


def infer_input_size(param_name: str, param_type: Optional[str] = None) -> str:
    """
    Infer symbolic input size variable from parameter name/type.
    Returns: 'n', 'm', 'V', 'E', etc.
    """
    name_lower = param_name.lower()
    
    # Common conventions
    if 'graph' in name_lower or 'g' == name_lower:
        return 'V'  # vertices
    if 'edge' in name_lower or 'edges' in name_lower:
        return 'E'
    if 'matrix' in name_lower or 'grid' in name_lower:
        return 'n'  # Could be n*m, but start with n
    if 'm' == name_lower or name_lower.endswith('_m'):
        return 'm'
    if 'k' == name_lower or name_lower.endswith('_k'):
        return 'k'
    
    # Default: n for arrays, lists, strings
    return 'n'
