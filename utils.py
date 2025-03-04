#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
工具函数模块

此模块包含各种辅助函数和类，用于代码合并器的功能实现。
'''

import fnmatch
from pathlib import Path
from typing import List
from loguru import logger

from language_config import FILE_EXTENSION_LANGUAGE_MAP

def get_file_content(file_path: Path) -> str:
    '''
    从文件读取内容
    
    :param file_path: 文件路径
    :type file_path: Path
    :return: 文件内容
    :rtype: str
    '''
    try:
        return file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # 如果UTF-8解码失败，尝试使用其他编码
        encodings = ['utf-16', 'latin1', 'gb18030']
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        logger.error(f'无法读取文件 {file_path}: 不支持的编码格式')
        return ''
    except Exception as e:
        logger.error(f'读取文件 {file_path} 时发生错误: {e}')
        return ''

def calculate_file_size(file_path: Path) -> int:
    '''
    计算文件大小
    
    :param file_path: 文件路径
    :type file_path: Path
    :return: 文件大小（字节）
    :rtype: int
    '''
    try:
        return file_path.stat().st_size
    except Exception as e:
        logger.error(f'获取文件 {file_path} 大小时发生错误: {e}')
        return 0

def get_language_by_extension(file_path: Path) -> str:
    '''
    根据文件扩展名获取对应的语言标识
    
    :param file_path: 文件路径
    :type file_path: Path
    :return: 语言标识
    :rtype: str
    '''
    extension = file_path.suffix.lower()
    return FILE_EXTENSION_LANGUAGE_MAP.get(extension, 'plaintext')

def matches_pattern(file_path: Path, patterns: List[str]) -> bool:
    '''
    检查文件路径是否匹配任一模式
    
    :param file_path: 文件路径
    :type file_path: Path
    :param patterns: 匹配模式列表
    :type patterns: List[str]
    :return: 如果匹配则返回True
    :rtype: bool
    '''
    if not patterns:
        return False
    
    file_str = str(file_path)
    file_name = file_path.name
    
    for pattern in patterns:
        if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(file_str, pattern):
            return True
    return False

class FileWriter:
    '''
    文件写入器类
    
    处理文件写入，支持文件大小限制和文件分割
    '''
    
    def __init__(self, base_filename: Path, split_size: int = 0, force_overwrite: bool = False):
        '''
        初始化文件写入器
        
        :param base_filename: 基础文件名
        :type base_filename: Path
        :param split_size: 分割大小（KB）
        :type split_size: int
        :param force_overwrite: 是否强制覆盖已存在的文件
        :type force_overwrite: bool
        '''
        self.base_filename = Path(base_filename)
        self.split_size = split_size * 1024 if split_size > 0 else 0  # 将KB转换为字节
        self.force_overwrite = force_overwrite
        self.current_file_index = 1
        self.current_file = None
        self.current_size = 0
        self.header = None
        self.generated_files: List[Path] = []
        
        logger.debug(f'初始化FileWriter，分割大小: {self.split_size} bytes')
        
        # 创建父目录
        self.base_filename.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化第一个文件
        self._init_new_file()
    
    def _get_filename(self) -> Path:
        '''
        获取当前文件名
        
        :return: 文件路径
        :rtype: Path
        '''
        stem = self.base_filename.stem
        suffix = self.base_filename.suffix
        if self.split_size == 0:
            return self.base_filename
        return self.base_filename.with_name(f'{stem}_{self.current_file_index}{suffix}')
    
    def _init_new_file(self) -> None:
        '''
        初始化新文件
        '''
        self.current_file = self._get_filename()
        logger.debug(f'创建新文件: {self.current_file}')
        
        # 检查文件是否已存在
        if self.current_file.exists() and not self.force_overwrite:
            # 在main.py中已经处理了文件存在的情况，这里如果到达这一步,
            # 要么文件不存在，要么force_overwrite为True
            # 但为了安全，还是加上这个检查
            logger.warning(f'文件已存在但将被覆盖: {self.current_file}')
        
        # 创建新文件并写入头部
        if self.header and self.current_file_index > 1:
            self.current_file.write_text(self.header, encoding='utf-8')
            self.current_size = len(self.header.encode('utf-8'))
        else:
            self.current_file.write_text('', encoding='utf-8')
            self.current_size = 0
        
        self.generated_files.append(self.current_file)
        logger.debug(f'初始化文件完成: {self.current_file}, 当前大小: {self.current_size} bytes')
    
    def _write_chunk(self, chunk: str) -> None:
        '''
        写入一个内容块到当前文件
        
        :param chunk: 要写入的内容块
        :type chunk: str
        '''
        with open(self.current_file, 'a', encoding='utf-8') as f:
            f.write(chunk)
        self.current_size += len(chunk.encode('utf-8'))
        logger.debug(f'写入内容块，当前文件大小: {self.current_size} bytes')
    
    def write(self, content: str) -> None:
        '''
        写入内容到文件，如果需要会自动分割
        
        :param content: 要写入的内容
        :type content: str
        '''
        # 保存头部内容
        if not self.header and content.startswith('# '):
            self.header = content
            logger.debug(f'设置头部内容，大小: {len(self.header.encode("utf-8"))} bytes')
        
        if self.split_size == 0:
            # 不需要分割，直接写入
            self._write_chunk(content)
            return
        
        # 将内容分块处理
        remaining = content
        while remaining:
            # 计算当前文件还能写入多少内容
            available_size = max(0, self.split_size - self.current_size)
            if available_size == 0:
                # 当前文件已满，创建新文件
                self.current_file_index += 1
                self._init_new_file()
                available_size = self.split_size - self.current_size
            
            # 将内容编码为字节以准确计算大小
            remaining_bytes = remaining.encode('utf-8')
            if len(remaining_bytes) <= available_size:
                # 剩余内容可以完全写入当前文件
                self._write_chunk(remaining)
                break
            
            # 找到合适的分割点
            chunk_size = available_size
            while chunk_size > 0:
                try:
                    chunk = remaining_bytes[:chunk_size].decode('utf-8')
                    # 在行尾或段落尾分割
                    last_newline = chunk.rfind('\n')
                    if last_newline > 0:
                        chunk = chunk[:last_newline + 1]
                    self._write_chunk(chunk)
                    remaining = remaining[len(chunk):]
                    
                    # 创建新文件继续处理
                    self.current_file_index += 1
                    self._init_new_file()
                    break
                except UnicodeDecodeError:
                    # 如果在多字节字符中间分割，减少大小重试
                    chunk_size -= 1
            
            if chunk_size == 0:
                # 如果找不到合适的分割点，强制分割
                chunk = remaining[:100]  # 取固定大小
                self._write_chunk(chunk)
                remaining = remaining[100:]
                self.current_file_index += 1
                self._init_new_file()
    
    def close(self) -> None:
        '''
        关闭文件写入器
        '''
        logger.debug(f'关闭文件写入器，共生成 {len(self.generated_files)} 个文件')
        logger.debug(f'生成的文件列表: {", ".join(str(f) for f in self.generated_files)}')
    
    def get_generated_files(self) -> List[Path]:
        '''
        获取生成的文件列表
        
        :return: 生成的文件路径列表
        :rtype: List[Path]
        '''
        return self.generated_files
