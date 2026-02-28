#!/usr/bin/env python3
"""
简单的阶乘计算程序
提供两种实现方式：递归和迭代
"""

from typing import Union


def factorial_recursive(n: int) -> int:
    """
    使用递归方式计算阶乘
    
    Args:
        n: 非负整数
        
    Returns:
        n的阶乘
        
    Raises:
        ValueError: 如果n为负数
    """
    if n < 0:
        raise ValueError("阶乘只能计算非负整数")
    if n == 0 or n == 1:
        return 1
    return n * factorial_recursive(n - 1)


def factorial_iterative(n: int) -> int:
    """
    使用迭代方式计算阶乘
    
    Args:
        n: 非负整数
        
    Returns:
        n的阶乘
        
    Raises:
        ValueError: 如果n为负数
    """
    if n < 0:
        raise ValueError("阶乘只能计算非负整数")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def main() -> None:
    """
    主函数：测试阶乘计算
    """
    test_cases = [0, 1, 5, 10, 15]
    
    print("=" * 50)
    print("阶乘计算测试")
    print("=" * 50)
    
    for n in test_cases:
        result_recursive = factorial_recursive(n)
        result_iterative = factorial_iterative(n)
        
        print(f"\n{n}! =")
        print(f"  递归方式: {result_recursive}")
        print(f"  迭代方式: {result_iterative}")
        
        # 验证两种方式结果一致
        assert result_recursive == result_iterative, "两种实现方式结果不一致！"
    
    print("\n" + "=" * 50)
    print("所有测试通过！✓")
    print("=" * 50)


if __name__ == "__main__":
    main()
