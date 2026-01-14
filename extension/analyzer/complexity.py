def estimate_time_complexity(
    loop_depth: int, 
    recursive_calls: int,
    max_recursive_calls_in_single_path: int = 0,
    has_dividing_recursion: bool = False,
    has_dividing_loop: bool = False,
    has_loop_with_recursion: bool = False,
    has_mutually_exclusive_recursion: bool = False,
    has_builtin_sort: bool = False,
    has_binary_search_pattern: bool = False,
    enhanced_visitor=None  # Optional enhanced visitor for symbolic analysis
) -> str:
    # If enhanced visitor is provided, use symbolic analysis
    if enhanced_visitor is not None:
        try:
            from .enhanced_analyzer import compute_time_complexity
            symbolic_comp = compute_time_complexity(enhanced_visitor)
            return str(symbolic_comp)
        except Exception:
            pass  # Fall back to heuristic analysis
    # O(n log n) - built-in sort methods (check FIRST)
    if has_builtin_sort:
        return "O(n log n)"
    
    # O(log n) - binary search pattern in while loop (check early)
    if has_binary_search_pattern and loop_depth == 1 and recursive_calls == 0:
        return "O(log n)"
    # O(log n) - logarithmic: MUST check before O(n log n) and O(2^n)
    # If we have dividing recursion and recursive calls are in mutually exclusive branches (if/else)
    # This is O(log n) - only one branch executes per call
    if has_dividing_recursion and recursive_calls > 0:
        # If we have mutually exclusive recursion (if/else branches), it's O(log n)
        # OR if max_recursive_calls_in_single_path is 1 (single recursive call per path)
        if has_mutually_exclusive_recursion:
            return "O(log n)"
        if max_recursive_calls_in_single_path <= 1:
            return "O(log n)"
    
    # O(n log n) - linearithmic: MUST check before O(2^n) if dividing
    # If we have 2+ recursive calls AND dividing, it's likely O(n log n) (merge sort, quicksort)
    # BUT only if calls are sequential (not in mutually exclusive branches)
    if max_recursive_calls_in_single_path >= 2 and has_dividing_recursion:
        return "O(n log n)"
    
    # O(2^n) - exponential recursion: 2+ recursive calls in same path without dividing problem size
    # This happens when recursion branches without reducing problem size (e.g., Fibonacci, subsets)
    if max_recursive_calls_in_single_path >= 2:
        if not has_dividing_recursion:
            return "O(2^n)"
    
    # O(n log n) - linearithmic: loop with recursive calls that divide problem size
    # Common in merge sort, quick sort, etc.
    if has_loop_with_recursion and has_dividing_recursion:
        return "O(n log n)"
    # Also: loop with nested divide-and-conquer recursion
    if loop_depth >= 1 and recursive_calls > 0 and has_dividing_recursion:
        return "O(n log n)"
    
    # O(log n) - logarithmic: recursion that divides problem size (binary search, etc.)
    # Single recursive call that divides problem
    if has_dividing_recursion and recursive_calls > 0 and max_recursive_calls_in_single_path <= 1:
        return "O(log n)"
    # While loop that divides (binary search pattern or division in loop)
    if has_dividing_loop and loop_depth == 1 and recursive_calls == 0:
        return "O(log n)"
    # Binary search pattern in while loop
    if has_binary_search_pattern and loop_depth == 1 and recursive_calls == 0:
        return "O(log n)"
    
    # O(2^n) - check again if we have 2+ calls (even if we checked dividing above)
    if max_recursive_calls_in_single_path >= 2:
        return "O(2^n)"
    
    # O(n) - linear recursion (single recursive call without division)
    if recursive_calls == 1 and not has_dividing_recursion and loop_depth == 0:
        return "O(n)"
    
    # Standard loop complexities (check these after recursion patterns)
    if loop_depth == 0:
        return "O(1)"
    if loop_depth == 1:
        return "O(n)"
    if loop_depth == 2:
        return "O(n^2)"

    return f"O(n^{loop_depth})"


def estimate_space_complexity(recursive_calls: int, max_loop_depth: int, enhanced_visitor=None) -> str:
    # If enhanced visitor is provided, use symbolic analysis
    if enhanced_visitor is not None:
        try:
            from .enhanced_analyzer import compute_space_complexity
            symbolic_comp = compute_space_complexity(enhanced_visitor)
            return str(symbolic_comp)
        except Exception:
            pass  # Fall back to heuristic analysis
    
    # Fallback heuristic
    if recursive_calls >= 1:
        if recursive_calls >= 2:
            return "O(n)"
        return "O(n)"
    
    return "O(1)"


