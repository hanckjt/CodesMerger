#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
代码合并模块

此模块包含合并源代码文件到Markdown的核心功能。
'''

import threading
import queue
import time
import sys
from pathlib import Path
from typing import List
from loguru import logger
from tqdm import tqdm
import fnmatch

from language_config import SUPPORTED_LANGUAGES
from utils import get_file_content, FileWriter, get_language_by_extension, matches_pattern

class CodesMerger:
    '''
    代码合并器类
    
    将指定目录下的源代码文件合并到一个或多个Markdown文件中
    '''
    
    def __init__(
            self, 
            source_dir: Path, 
            output_file: str, 
            languages: List[str] = None,
            file_patterns: List[str] = None,
            split_size: int = 0,
            n_threads: int = 4,
            ignore_patterns: List[str] = None,
            force_overwrite: bool = False
        ):
        '''
        初始化代码合并器
        
        :param source_dir: 源代码目录
        :type source_dir: Path
        :param output_file: 输出的Markdown文件名
        :type output_file: str
        :param languages: 语言类型列表
        :type languages: List[str]
        :param file_patterns: 文件匹配模式列表
        :type file_patterns: List[str]
        :param split_size: 分割大小(KB)
        :type split_size: int
        :param n_threads: 线程数量
        :type n_threads: int
        :param ignore_patterns: 要忽略的文件或目录模式
        :type ignore_patterns: List[str]
        :param force_overwrite: 是否强制覆盖已存在的输出文件
        :type force_overwrite: bool
        '''
        self.source_dir = Path(source_dir).absolute()
        self.output_file = Path(output_file)
        self.languages = languages or []
        self.file_patterns = file_patterns or []
        self.split_size = split_size  # 保持KB单位，在创建FileWriter时才转换为字节
        self.n_threads = max(1, min(n_threads, 16))  # 限制线程数在1-16之间
        self.ignore_patterns = ignore_patterns or []
        self.force_overwrite = force_overwrite
        
        # 检查源目录
        if not self.source_dir.exists() or not self.source_dir.is_dir():
            raise ValueError(f'源目录路径不存在或不是目录: {self.source_dir}')
        
        # 如果指定了语言，验证语言是否支持
        self.extensions = set()
        if self.languages:
            for lang in self.languages:
                if lang not in SUPPORTED_LANGUAGES:
                    raise ValueError(f'不支持的语言: {lang}。支持的语言: {", ".join(SUPPORTED_LANGUAGES.keys())}')
                self.extensions.update(SUPPORTED_LANGUAGES[lang])
        
        # 用于存储找到的文件列表
        self.files_queue = queue.Queue()
        
        # 用于文件写入的锁
        self.file_lock = threading.Lock()
        
        # 进度条
        self.progress_bar = None
        
        logger.info(f'初始化代码合并器完成，源目录: {self.source_dir}')
        if self.languages:
            logger.info(f'选择的语言: {", ".join(self.languages)}')
        if self.file_patterns:
            logger.info(f'选择的文件模式: {", ".join(self.file_patterns)}')
    
    def _should_ignore(self, path: Path) -> bool:
        '''
        检查路径是否应该被忽略
        
        :param path: 要检查的路径
        :type path: Path
        :return: 如果应该被忽略则返回True
        :rtype: bool
        '''
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(path_str, pattern):
                return True
        return False
    
    def _should_include(self, file_path: Path) -> bool:
        '''
        检查文件是否应该被包含
        
        :param file_path: 文件路径
        :type file_path: Path
        :return: 如果应该被包含则返回True
        :rtype: bool
        '''
        # 如果指定了语言和模式都为空，则不包含任何文件
        if not self.languages and not self.file_patterns:
            logger.warning('未指定语言或文件模式，请至少提供一种筛选条件')
            return False
            
        # 如果指定了文件模式，检查文件是否匹配
        if self.file_patterns and matches_pattern(file_path, self.file_patterns):
            return True
            
        # 如果指定了语言，检查文件扩展名是否匹配
        if self.languages and file_path.suffix in self.extensions:
            return True
            
        return False
    
    def find_files(self) -> List[Path]:
        '''
        在源目录中查找匹配条件的所有源代码文件
        
        :return: 找到的文件路径列表
        :rtype: List[Path]
        '''
        logger.info(f'开始在 {self.source_dir} 中查找符合条件的源代码文件')
        
        found_files = []
        
        try:
            # 使用pathlib递归查找所有文件
            for file_path in self.source_dir.rglob('*'):
                # 只处理文件
                if not file_path.is_file():
                    continue
                
                # 检查是否应该忽略此文件或其父目录
                if self._should_ignore(file_path) or any(self._should_ignore(parent) for parent in file_path.parents):
                    logger.debug(f'忽略文件: {file_path}')
                    continue
                
                # 检查是否应该包含此文件
                if self._should_include(file_path):
                    logger.debug(f'找到文件: {file_path}')
                    found_files.append(file_path)
        
        except Exception as e:
            logger.error(f'查找文件时发生错误: {e}')
            raise
        
        logger.info(f'共找到 {len(found_files)} 个文件')
        return found_files
    
    def process_file(self, file_path: Path, file_writer: FileWriter) -> None:
        '''
        处理单个文件并将其内容添加到Markdown文件
        
        :param file_path: 要处理的文件路径
        :type file_path: Path
        :param file_writer: 文件写入器
        :type file_writer: FileWriter
        '''
        try:
            # 获取相对路径，用于Markdown中显示
            relative_path = file_path.relative_to(self.source_dir)
            content = get_file_content(file_path)
            
            if not content:
                logger.warning(f'文件 {relative_path} 为空或无法读取')
                return
            
            # 根据文件扩展名确定语言
            lang_identifier = get_language_by_extension(file_path)
                
            # 创建Markdown内容
            markdown_content = f'## {relative_path}\n\n'
            markdown_content += f'```{lang_identifier}\n'
            markdown_content += content
            markdown_content += '\n```\n\n'
            
            # 安全地写入文件
            with self.file_lock:
                file_writer.write(markdown_content)
            
            logger.debug(f'已处理文件: {relative_path}')
        
        except Exception as e:
            logger.error(f'处理文件 {file_path} 时发生错误: {e}')
            raise
    
    def worker(self, file_writer: FileWriter):
        '''
        工作线程函数
        
        :param file_writer: 文件写入器
        :type file_writer: FileWriter
        '''
        while True:
            try:
                # 非阻塞方式获取队列中的文件
                file_path = self.files_queue.get(block=False)
                self.process_file(file_path, file_writer)
                # 更新进度条
                self.progress_bar.update(1)
                # 标记任务完成
                self.files_queue.task_done()
            except queue.Empty:
                # 队列为空，工作完成
                break
            except Exception as e:
                logger.error(f'工作线程发生错误: {e}')
                self.files_queue.task_done()
                raise
    
    def run(self) -> None:
        '''
        运行代码合并过程
        '''
        start_time = time.time()
        logger.info(f'开始代码合并过程，使用 {self.n_threads} 个线程')
        
        # 查找所有文件
        files = self.find_files()
        if not files:
            logger.warning('没有找到符合条件的源代码文件，程序结束')
            return
        
        # 初始化文件写入器
        try:
            file_writer = FileWriter(
                base_filename=self.output_file,
                split_size=self.split_size,  # 传入KB单位的大小
                force_overwrite=self.force_overwrite
            )
        except FileExistsError:
            logger.error(f'输出文件已存在: {self.output_file}')
            sys.exit(1)
        
        # 写入Markdown文件头部
        header = f'# {self.source_dir.name} 源代码合并文档\n\n'
        if self.languages:
            header += f'- **语言:** {", ".join(self.languages)}\n'
        if self.file_patterns:
            header += f'- **文件模式:** {", ".join(self.file_patterns)}\n'
        header += f'- **生成时间:** {time.strftime("%Y-%m-%d %H:%M:%S")}\n'
        header += f'- **文件总数:** {len(files)}\n\n'
        header += '---\n\n'
        
        file_writer.write(header)
        
        # 将所有文件加入队列
        for file_path in files:
            self.files_queue.put(file_path)
        
        # 创建固定在底部的进度条
        self.progress_bar = tqdm(
            total=len(files),
            desc='处理文件',
            unit='文件',
            position=0,
            leave=True
        )
        
        # 创建并启动工作线程
        threads = []
        for _ in range(self.n_threads):
            thread = threading.Thread(target=self.worker, args=(file_writer,))
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 关闭文件写入器
        file_writer.close()
        
        # 关闭进度条
        self.progress_bar.close()
        
        end_time = time.time()
        logger.info(f'代码合并完成，耗时: {end_time - start_time:.2f} 秒')
        logger.info(f'输出文件: {file_writer.get_generated_files()}')
