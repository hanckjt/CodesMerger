#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
测试数据准备脚本

此脚本用于创建测试所需的目录结构和示例文件
'''

import os
import shutil
from pathlib import Path

# 测试数据目录结构
TEST_DATA_STRUCTURE = {
    'python_files': {
        'test1.py': '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b
''',
        'test2.py': '''
class Calculator:
    """A simple calculator class."""
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a: int, b: int) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
'''
    },
    'cpp_files': {
        'main.cpp': '''
#include <iostream>
#include "helper.h"

int main() {
    std::cout << "Hello, World!" << std::endl;
    Helper helper;
    helper.printMessage();
    return 0;
}
''',
        'helper.h': '''
#ifndef HELPER_H
#define HELPER_H

class Helper {
public:
    void printMessage() {
        std::cout << "Helper message" << std::endl;
    }
};

#endif // HELPER_H
'''
    },
    'mixed_files': {
        'script.py': '''
print("Hello from Python!")
''',
        'style.css': '''
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 800px;
    margin: 0 auto;
}
''',
        'index.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Test Page</h1>
        <p>This is a test page.</p>
    </div>
</body>
</html>
'''
    }
}

def setup_test_data():
    """创建测试数据目录和文件"""
    # 获取测试数据根目录
    test_data_dir = Path(__file__).parent / 'test_data'
    
    # 如果目录已存在，先删除
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
    
    # 创建测试数据根目录
    test_data_dir.mkdir(parents=True)
    
    # 创建目录结构和文件
    for category, files in TEST_DATA_STRUCTURE.items():
        category_dir = test_data_dir / category
        category_dir.mkdir(parents=True)
        
        for filename, content in files.items():
            file_path = category_dir / filename
            file_path.write_text(content.lstrip('\n'), encoding='utf-8')
    
    print(f"测试数据已创建在: {test_data_dir}")

if __name__ == '__main__':
    setup_test_data()