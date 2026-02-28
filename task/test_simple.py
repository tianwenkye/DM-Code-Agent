#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试文件
用于测试基本的Python功能和测试框架
"""

import unittest


class TestBasicOperations(unittest.TestCase):
    """基本运算测试类"""
    
    def test_addition(self):
        """测试加法运算"""
        self.assertEqual(2 + 2, 4)
        self.assertEqual(5 + 3, 8)
    
    def test_subtraction(self):
        """测试减法运算"""
        self.assertEqual(10 - 5, 5)
        self.assertEqual(7 - 3, 4)
    
    def test_multiplication(self):
        """测试乘法运算"""
        self.assertEqual(3 * 4, 12)
        self.assertEqual(6 * 7, 42)
    
    def test_string_operations(self):
        """测试字符串操作"""
        self.assertEqual("hello" + " world", "hello world")
        self.assertTrue("python" in "awesome python code")


class TestListOperations(unittest.TestCase):
    """列表操作测试类"""
    
    def test_list_length(self):
        """测试列表长度"""
        self.assertEqual(len([1, 2, 3]), 3)
        self.assertEqual(len([]), 0)
    
    def test_list_append(self):
        """测试列表追加元素"""
        my_list = [1, 2]
        my_list.append(3)
        self.assertEqual(my_list, [1, 2, 3])
    
    def test_list_contains(self):
        """测试列表包含元素"""
        self.assertIn(2, [1, 2, 3])
        self.assertNotIn(5, [1, 2, 3])


class TestEdgeCases(unittest.TestCase):
    """边界情况测试类"""
    
    def test_empty_string(self):
        """测试空字符串"""
        self.assertEqual(len(""), 0)
        self.assertTrue("" == "")
    
    def test_boolean_values(self):
        """测试布尔值"""
        self.assertTrue(True)
        self.assertFalse(False)
        self.assertTrue(not False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
