def foo(arr):
    for i in arr:
        for j in arr:
            print(i, j)

def bar(n):
    if n <= 1:
        return 1
    return bar(n - 1)
