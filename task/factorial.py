from typing import Union


def factorial(n: int) -> int:
    """
    计算给定非负整数的阶乘。
    
    Args:
        n: 非负整数
        
    Returns:
        n的阶乘值
        
    Raises:
        ValueError: 如果n是负数
        TypeError: 如果n不是整数
    """
    # 输入验证
    if not isinstance(n, int):
        raise TypeError(f"阶乘函数只接受整数，得到的是 {type(n).__name__}")
    
    if n < 0:
        raise ValueError("阶乘函数只接受非负整数")
    
    # 基本情况
    if n == 0 or n == 1:
        return 1
    
    # 使用循环计算阶乘
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result


# 递归实现（可选）
def factorial_recursive(n: int) -> int:
    """
    使用递归方式计算阶乘。
    
    Args:
        n: 非负整数
        
    Returns:
        n的阶乘值
    """
    if not isinstance(n, int):
        raise TypeError(f"阶乘函数只接受整数，得到的是 {type(n).__name__}")
    
    if n < 0:
        raise ValueError("阶乘函数只接受非负整数")
    
    if n == 0 or n == 1:
        return 1
    
    return n * factorial_recursive(n - 1)


if __name__ == "__main__":
    # 测试代码
    print("测试阶乘函数：")
    print(f"0! = {factorial(0)}")
    print(f"1! = {factorial(1)}")
    print(f"5! = {factorial(5)}")
    print(f"10! = {factorial(10)}")
    
    # 测试递归版本
    print("\n测试递归阶乘函数：")
    print(f"5! = {factorial_recursive(5)}")
    print(f"10! = {factorial_recursive(10)}")