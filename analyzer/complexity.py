def estimate_time_complexity(loop_depth: int, recursive_calls: int) -> str:
    if recursive_calls >= 2:
        return "O(2^n)"
    if recursive_calls == 1:
        return "O(n)"

    if loop_depth == 0:
        return "O(1)"
    if loop_depth == 1:
        return "O(n)"
    if loop_depth == 2:
        return "O(n^2)"

    return f"O(n^{loop_depth})"


def estimate_space_complexity(recursive_calls: int, max_loop_depth: int) -> str:
    """Estimate space complexity based on recursion depth and auxiliary structures"""
    if recursive_calls >= 1:
        # Recursive calls use call stack space
        if recursive_calls >= 2:
            return "O(n)"  # Multiple recursive calls typically O(n) stack depth
        return "O(n)"  # Single recursion usually O(n) stack depth
    
    # No recursion, space complexity is usually O(1) unless there are data structures
    # For simplicity, we'll return O(1) for non-recursive functions
    return "O(1)"
