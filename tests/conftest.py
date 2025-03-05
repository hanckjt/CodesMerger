#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Pytest配置文件

提供共享的测试fixture
'''

import pytest
from pathlib import Path
import shutil
import tempfile

@pytest.fixture(scope="session")
def setup_test_env(request):
    """设置测试环境，运行数据准备脚本"""
    from setup_test_data import setup_test_data
    setup_test_data()

@pytest.fixture
def temp_dir():
    """提供临时目录，并在测试后清理"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def test_data_dir(setup_test_env):
    """提供测试数据目录路径"""
    return Path(__file__).parent / 'test_data'

@pytest.fixture
def python_files_dir(test_data_dir):
    """提供Python文件测试目录"""
    return test_data_dir / 'python_files'

@pytest.fixture
def cpp_files_dir(test_data_dir):
    """提供C++文件测试目录"""
    return test_data_dir / 'cpp_files'

@pytest.fixture
def mixed_files_dir(test_data_dir):
    """提供混合文件测试目录"""
    return test_data_dir / 'mixed_files'

@pytest.fixture
def output_file(temp_dir):
    """提供输出文件路径"""
    return temp_dir / 'output.md'

@pytest.fixture(autouse=True)
def clean_temp_files():
    """测试前后清理临时文件"""
    # 测试前清理
    temp_patterns = ['*.md', '*.log']
    for pattern in temp_patterns:
        for file in Path('.').glob(pattern):
            file.unlink()
    
    yield
    
    # 测试后清理
    for pattern in temp_patterns:
        for file in Path('.').glob(pattern):
            file.unlink()