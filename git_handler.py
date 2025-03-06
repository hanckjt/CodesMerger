#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Git仓库处理模块

此模块用于处理Git仓库的克隆和管理。
'''

import re
import shutil
import tempfile
import time
import os
from pathlib import Path
from typing import Optional, Tuple, List
from loguru import logger
import git


class GitRepoHandler:
    '''
    Git仓库处理类
    
    用于克隆远程Git仓库并管理临时目录
    '''
    
    def __init__(self, keep_git_cache: bool = False):
        '''
        初始化Git仓库处理器
        
        :param keep_git_cache: 是否保留Git缓存目录
        :type keep_git_cache: bool
        '''
        self.keep_git_cache = keep_git_cache
        self.git_cache_dir = Path('.git_cache')
        self.cloned_repo_path = None
    
    def is_git_url(self, source: str) -> bool:
        '''
        检查源是否为Git仓库URL
        
        :param source: 源路径或URL
        :type source: str
        :return: 如果是Git URL则返回True
        :rtype: bool
        '''
        # 匹配常见的Git URL格式
        git_url_patterns = [
            # HTTP/HTTPS格式
            r'^https?://.*\.git$',
            # SSH格式
            r'^git@.*:.*\.git$',
            # 简短格式
            r'^[^/]+/[^/]+\.git$'
        ]
        
        return any(re.match(pattern, source) for pattern in git_url_patterns)
    
    def clone_repository(self, git_url: str, branch: Optional[str] = None) -> Path:
        '''
        克隆Git仓库到临时目录
        
        :param git_url: Git仓库URL
        :type git_url: str
        :param branch: 要检出的分支名称，默认为None（检出默认分支）
        :type branch: Optional[str]
        :return: 克隆的仓库路径
        :rtype: Path
        :raises git.GitCommandError: 当Git命令执行失败时抛出
        '''
        # 确保缓存目录存在
        self.git_cache_dir.mkdir(exist_ok=True)
        
        # 生成唯一的目录名
        repo_name = git_url.split('/')[-1].replace('.git', '')
        unique_dir = tempfile.mkdtemp(prefix=f'{repo_name}_', dir=str(self.git_cache_dir))
        repo_path = Path(unique_dir)
        
        try:
            logger.info(f'正在克隆仓库 {git_url} 到 {repo_path}')
            
            # 克隆仓库
            if branch:
                logger.info(f'指定分支: {branch}')
                git.Repo.clone_from(git_url, repo_path, branch=branch)
            else:
                git.Repo.clone_from(git_url, repo_path)
            
            logger.success(f'仓库克隆成功: {repo_path}')
            self.cloned_repo_path = repo_path
            return repo_path
            
        except git.GitCommandError as e:
            logger.error(f'克隆仓库失败: {e}')
            # 清理失败的克隆目录
            self._cleanup_directory(repo_path)
            raise
    
    def cleanup(self) -> None:
        '''
        清理克隆的Git仓库目录
        '''
        if not self.keep_git_cache and self.cloned_repo_path is not None:
            self._cleanup_directory(self.cloned_repo_path)
            self.cloned_repo_path = None
            
            # 如果.git_cache目录为空，也删除它
            try:
                if self.git_cache_dir.exists() and not any(self.git_cache_dir.iterdir()):
                    self.git_cache_dir.rmdir()
                    logger.info('已删除空的.git_cache目录')
            except Exception as e:
                logger.warning(f'尝试删除.git_cache目录时出错: {e}')
    
    def _cleanup_directory(self, directory: Path) -> None:
        '''
        删除指定目录，处理文件锁定和权限问题
        
        :param directory: 要删除的目录路径
        :type directory: Path
        '''
        if not directory.exists():
            return
            
        logger.info(f'正在删除目录: {directory}')
        
        # 首先尝试使用shutil.rmtree删除
        try:
            shutil.rmtree(directory)
            logger.info(f'已成功删除目录: {directory}')
            return
        except PermissionError as e:
            logger.warning(f'删除目录时遇到权限错误: {e}，尝试其他方法')
        except OSError as e:
            logger.warning(f'删除目录时遇到OS错误: {e}，尝试其他方法')
            
        # 如果直接删除失败，尝试逐个删除文件
        failed_paths = []
        try:
            self._remove_directory_contents(directory, failed_paths)
            
            # 如果有失败的文件，记录并报告
            if failed_paths:
                paths_str = '\n  '.join(str(p) for p in failed_paths[:10])
                if len(failed_paths) > 10:
                    paths_str += f'\n  ...以及其他 {len(failed_paths) - 10} 个文件'
                logger.error(f'无法删除以下文件/目录:\n  {paths_str}')
                logger.info(f'这些文件可能被其他程序锁定，将在下次运行时再次尝试删除')
            else:
                # 如果所有内容都删除了，尝试删除空目录
                try:
                    directory.rmdir()
                    logger.info(f'已成功删除目录: {directory}')
                except OSError as e:
                    logger.warning(f'无法删除空目录 {directory}: {e}')
        except Exception as e:
            logger.error(f'删除目录内容时发生未知错误: {e}')
    
    def _remove_directory_contents(self, directory: Path, failed_paths: List[Path]) -> None:
        '''
        递归删除目录内容，记录无法删除的文件
        
        :param directory: 要清空的目录
        :type directory: Path
        :param failed_paths: 存储无法删除的文件路径列表
        :type failed_paths: List[Path]
        '''
        # 如果是符号链接，直接删除链接
        if directory.is_symlink():
            try:
                directory.unlink()
            except OSError:
                failed_paths.append(directory)
            return
                
        # 确保目录仍然存在
        if not directory.exists():
            return
            
        # 首先遍历并删除文件和子目录
        for path in list(directory.iterdir()):
            if path.is_dir():
                self._remove_directory_contents(path, failed_paths)
                # 尝试删除现在应该为空的目录
                try:
                    path.rmdir()
                except OSError:
                    failed_paths.append(path)
            else:
                # 删除文件
                try:
                    path.chmod(0o666)  # 尝试修改权限
                    path.unlink()
                except OSError:
                    # 在Windows上，有时需要等待一下再删除
                    try:
                        time.sleep(0.1)
                        path.unlink()
                    except OSError:
                        failed_paths.append(path)


def parse_git_source(source: str) -> Tuple[str, Optional[str]]:
    '''
    解析Git源，提取URL和可能的分支名

    :param source: Git源字符串，格式可能为 "url" 或 "url@branch"
    :type source: str
    :return: 包含URL和分支名的元组（如果没有指定分支，则分支名为None）
    :rtype: Tuple[str, Optional[str]]
    '''
    if '@' in source and not source.startswith('git@'):
        # 处理 url@branch 格式
        parts = source.split('@')
        if len(parts) == 2:
            return parts[0], parts[1]
    
    # 没有指定分支或使用其他格式
    return source, None
