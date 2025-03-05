#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
工具函数测试模块

测试工具函数和FileWriter类
'''

import pytest
from pathlib import Path
from utils import (
    get_file_content,
    calculate_file_size,
    get_language_by_extension,
    matches_pattern,
    FileWriter
)

def test_get_file_content(python_files_dir):
    """测试文件内容读取功能"""
    test_file = python_files_dir / 'test1.py'
    content = get_file_content(test_file)
    
    # 验证内容是否正确读取
    assert 'def add' in content
    assert 'def subtract' in content
    
    # 测试非UTF-8编码文件
    with open(test_file, 'wb') as f:
        f.write('Hello World'.encode('utf-16'))
    content = get_file_content(test_file)
    assert content  # 应该能读取内容
    
    # 测试不存在的文件
    non_existent = python_files_dir / 'not_exists.py'
    content = get_file_content(non_existent)
    assert content == ''

def test_calculate_file_size(python_files_dir):
    """测试文件大小计算功能"""
    test_file = python_files_dir / 'test1.py'
    size = calculate_file_size(test_file)
    
    # 验证文件大小
    assert size > 0
    assert size == test_file.stat().st_size
    
    # 测试不存在的文件
    non_existent = python_files_dir / 'not_exists.py'
    size = calculate_file_size(non_existent)
    assert size == 0

def test_get_language_by_extension():
    """测试文件扩展名到语言的映射"""
    test_cases = [
        (Path('test.py'), 'python'),
        (Path('test.cpp'), 'cpp'),
        (Path('test.js'), 'javascript'),
        (Path('test.unknown'), 'plaintext'),
        (Path('test'), 'plaintext')
    ]
    
    for file_path, expected_lang in test_cases:
        assert get_language_by_extension(file_path) == expected_lang

def test_matches_pattern():
    """测试文件模式匹配功能"""
    test_cases = [
        # (文件路径, 模式列表, 预期结果)
        (Path('test.py'), ['*.py'], True),
        (Path('test.cpp'), ['*.py'], False),
        (Path('test.py'), ['*.cpp', '*.py'], True),
        (Path('test_file.py'), ['test_*.py'], True),
        (Path('file.txt'), ['*.py', '*.cpp'], False),
        (Path('test.py'), [], False)
    ]
    
    for file_path, patterns, expected in test_cases:
        assert matches_pattern(file_path, patterns) == expected

class TestFileWriter:
    """FileWriter类的测试用例"""
    
    def test_basic_write(self, temp_dir):
        """测试基本的文件写入功能"""
        output_file = temp_dir / 'test.md'
        writer = FileWriter(output_file)
        
        test_content = '# Test Content\n\nThis is a test.'
        writer.write(test_content)
        writer.close()
        
        # 验证文件内容
        assert output_file.exists()
        assert output_file.read_text(encoding='utf-8') == test_content
    
    def test_file_splitting(self, temp_dir):
        """测试文件分割功能"""
        output_file = temp_dir / 'split.md'
        # 设置1KB的分割大小
        writer = FileWriter(output_file, split_size=1)
        
        # 写入超过1KB的内容
        content = 'x' * 512  # 每块512字节
        for i in range(4):  # 总共写入2KB
            writer.write(f'# Block {i}\n{content}\n')
        
        writer.close()
        
        # 验证生成了多个文件
        md_files = sorted(list(temp_dir.glob('split*.md')))
        assert len(md_files) > 1
        
        # 验证每个文件的大小
        for md_file in md_files:
            size = md_file.stat().st_size
            assert size <= 1024 * 1.1  # 允许10%的误差
    
    def test_force_overwrite(self, temp_dir):
        """测试强制覆盖功能"""
        output_file = temp_dir / 'overwrite.md'
        
        # 创建初始文件
        output_file.write_text('Original content', encoding='utf-8')
        
        # 不使用强制覆盖时应该抛出异常
        with pytest.raises(FileExistsError):
            writer = FileWriter(output_file, force_overwrite=False)
            writer.write('New content')
        
        # 验证原始内容未被修改
        assert output_file.read_text(encoding='utf-8') == 'Original content'
        
        # 使用强制覆盖
        writer = FileWriter(output_file, force_overwrite=True)
        writer.write('New content')
        writer.close()
        
        # 验证内容被覆盖
        assert output_file.read_text(encoding='utf-8') == 'New content'
    
    def test_unicode_content(self, temp_dir):
        """测试Unicode内容写入"""
        output_file = temp_dir / 'unicode.md'
        writer = FileWriter(output_file)
        
        # 包含中文和特殊字符的内容
        test_content = '# 测试文档\n\n特殊字符: ☺★♠♣\n'
        writer.write(test_content)
        writer.close()
        
        # 验证内容正确写入
        assert output_file.read_text(encoding='utf-8') == test_content
    
    def test_multiple_writes(self, temp_dir):
        """测试多次写入"""
        output_file = temp_dir / 'multiple.md'
        writer = FileWriter(output_file)
        
        contents = [
            '# Header\n\n',
            'First paragraph.\n\n',
            'Second paragraph.\n\n',
            'Final line.'
        ]
        
        for content in contents:
            writer.write(content)
        
        writer.close()
        
        # 验证所有内容都正确写入
        final_content = output_file.read_text(encoding='utf-8')
        for content in contents:
            assert content in final_content
        
        # 验证内容顺序正确
        assert final_content.index('Header') < final_content.index('First')
        assert final_content.index('First') < final_content.index('Second')
        assert final_content.index('Second') < final_content.index('Final')
    
    def test_small_size_splitting(self, temp_dir):
        """测试非常小的分割大小"""
        output_file = temp_dir / 'tiny_split.md'
        writer = FileWriter(output_file, split_size=1)  # 1KB的分割大小
        
        # 写入超过2KB的内容
        content = 'x' * 600  # 600字节
        for i in range(4):  # 总共2400字节
            writer.write(f'Block {i}: {content}\n')
        
        writer.close()
        
        # 验证生成了多个文件
        md_files = sorted(list(temp_dir.glob('tiny_split*.md')))
        assert len(md_files) > 1
        
        # 验证每个文件的大小
        for md_file in md_files:
            size = md_file.stat().st_size
            assert size <= 1024 * 1.1  # 确保每个文件不超过1KB(允许10%误差)