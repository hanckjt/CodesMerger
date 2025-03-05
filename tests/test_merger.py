#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
合并器测试模块

测试代码合并器的核心功能
'''

import pytest
from pathlib import Path
from merger import CodesMerger
import tempfile
import shutil
import time
import sys

def test_basic_merge(python_files_dir, output_file):
    """测试基本的文件合并功能"""
    merger = CodesMerger(
        source_dir=python_files_dir,
        output_file=str(output_file),
        languages=['python']
    )
    
    merger.run()
    
    # 验证输出文件存在
    assert output_file.exists()
    
    # 验证输出文件内容
    content = output_file.read_text(encoding='utf-8')
    assert '```python' in content
    assert 'def add' in content
    assert 'class Calculator' in content
    assert content.count('```') >= 4  # 至少有两对代码块标记

def test_file_pattern_filter(mixed_files_dir, output_file):
    """测试文件模式过滤功能"""
    merger = CodesMerger(
        source_dir=mixed_files_dir,
        output_file=str(output_file),
        file_patterns=['*.py']
    )
    
    merger.run()
    
    # 保证输出文件存在
    assert output_file.exists()
    content = output_file.read_text(encoding='utf-8')
    # 应该包含Python文件
    assert 'Hello from Python!' in content
    # 不应该包含HTML和CSS文件
    assert '<html>' not in content
    assert 'font-family' not in content

def test_language_filter(mixed_files_dir, output_file):
    """测试语言过滤功能"""
    merger = CodesMerger(
        source_dir=mixed_files_dir,
        output_file=str(output_file),
        languages=['python', 'html']
    )
    
    merger.run()
    
    # 保证输出文件存在
    assert output_file.exists()
    content = output_file.read_text(encoding='utf-8')
    # 应该包含Python和HTML文件
    assert 'Hello from Python!' in content
    assert '<html>' in content
    # 不应该包含CSS代码块
    assert '```css' not in content

def test_multithreading(mixed_files_dir, output_file):
    """测试多线程处理功能"""
    # 创建大量测试文件
    test_files = []
    for i in range(100):  # 创建足够多的文件以测试多线程效果
        file_path = mixed_files_dir / f'test_{i}.py'
        file_path.write_text(f'print("Test file {i}")\n' * 100)  # 增加文件大小
        test_files.append(file_path)
    
    try:
        # 单线程执行
        start_time = time.time()
        merger_single = CodesMerger(
            source_dir=mixed_files_dir,
            output_file=str(output_file),
            languages=['python'],
            n_threads=1
        )
        merger_single.run()
        single_thread_time = time.time() - start_time
        
        # 清理输出文件
        if output_file.exists():
            output_file.unlink()
        
        # 多线程执行
        start_time = time.time()
        merger_multi = CodesMerger(
            source_dir=mixed_files_dir,
            output_file=str(output_file),
            languages=['python'],
            n_threads=4
        )
        merger_multi.run()
        multi_thread_time = time.time() - start_time
        
        # 多线程应该不慢于单线程
        assert multi_thread_time <= single_thread_time * 2.0  # 增加误差容忍度
    
    finally:
        # 清理测试文件
        for file_path in test_files:
            try:
                file_path.unlink()
            except:
                pass

def test_file_splitting(python_files_dir, temp_dir):
    """测试文件分割功能"""
    output_file = temp_dir / 'split_output.md'
    
    # 先生成大量测试内容
    test_content = 'x' * 1000 + '\n'  # 1KB左右的内容
    source_file = python_files_dir / 'large_test.py'
    with open(source_file, 'w', encoding='utf-8') as f:
        for i in range(5):  # 写入约5KB的内容
            f.write(f'def test_{i}():\n    """\n    Test function {i}\n    """\n')
            f.write(test_content)
    
    try:
        # 设置1KB的分割大小
        merger = CodesMerger(
            source_dir=python_files_dir,
            output_file=str(output_file),
            languages=['python'],
            split_size=1  # 1KB分割大小
        )
        
        merger.run()
        
        # 检查是否生成了多个文件
        md_files = sorted(list(temp_dir.glob('split_output*.md')))
        assert len(md_files) > 1
        
        # 检查每个文件的大小
        for md_file in md_files:
            size = md_file.stat().st_size
            max_size = 1024 * 1.1  # 1KB加上10%的误差
            assert size <= max_size, f"文件 {md_file} 大小({size})超过限制({max_size})"
            
    finally:
        # 清理测试文件
        try:
            source_file.unlink()
        except:
            pass

def test_error_handling(temp_dir):
    """测试错误处理"""
    non_existent_dir = temp_dir / 'non_existent'
    output_file = temp_dir / 'error_output.md'
    
    # 测试不存在的目录
    with pytest.raises(SystemExit):
        merger = CodesMerger(
            source_dir=non_existent_dir,
            output_file=str(output_file)
        )
    
    # 测试无效的语言
    with pytest.raises(ValueError):
        merger = CodesMerger(
            source_dir=temp_dir,
            output_file=str(output_file),
            languages=['invalid_language']
        )

def test_ignore_patterns(mixed_files_dir, output_file):
    """测试忽略模式功能"""
    merger = CodesMerger(
        source_dir=mixed_files_dir,
        output_file=str(output_file),
        languages=['python'],  # 指定语言以确保python文件被包含
        ignore_patterns=['*.css', '*.html']
    )
    
    merger.run()
    
    # 保证输出文件存在
    assert output_file.exists()
    content = output_file.read_text(encoding='utf-8')
    # 应该包含Python文件
    assert 'Hello from Python!' in content
    # 不应该包含被忽略的文件
    assert '<html>' not in content
    assert 'font-family' not in content

def test_force_overwrite(python_files_dir, output_file):
    """测试强制覆盖功能"""
    # 创建一个已存在的输出文件
    output_file.write_text('Original content')
    
    # 不使用force_overwrite
    with pytest.raises(SystemExit):
        merger = CodesMerger(
            source_dir=python_files_dir,
            output_file=str(output_file),
            languages=['python']
        )
    
    # 确认原始内容未被修改
    assert output_file.read_text(encoding='utf-8') == 'Original content'
    
    # 使用force_overwrite
    merger = CodesMerger(
        source_dir=python_files_dir,
        output_file=str(output_file),
        languages=['python'],
        force_overwrite=True
    )
    
    merger.run()
    
    # 验证文件被覆盖
    content = output_file.read_text(encoding='utf-8')
    assert 'Original content' not in content
    assert '```python' in content