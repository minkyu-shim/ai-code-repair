"""
I will write 10-20 small cases that contains python bugs in this file
Run test cases at ./test_buggy.py then
The meta datas will be saved in ./meta.json
"""

def add(x: int, y: int) -> int:
    return x - y

def subtract(x: int, y: int) -> int:
    return x + y

def count(nums: list[int])-> int:
    res: int = 0
    for num in range(len(nums) + 1):
        res += 1
    return res

def count_2(nums):
    res = 0
    i = 0
    while i < len(nums):
        res+=1
    return res