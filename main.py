#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
代码合并器入口模块

此模块提供命令行界面，用于将源代码文件合并到Markdown文件中。
'''

import argparse
import sys
import os
from pathlib import Path
from loguru import logger

from merger import CodesMerger
from language_config import SUPPORTED_LANGUAGES
from config_loader import load_config, merge_config_with_args, get_default_config_path
from git_handler import GitRepoHandler


def setup_logger(log_level='INFO'):
    '''
    配置日志记录器

    :param log_level: 日志级别
    :type log_level: str
    '''
    logger.remove()
    logger.add(
        sys.stderr,
        format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>(<cyan>{file}</cyan>:<cyan>{line}</cyan>) - <level>{message}</level>',
        level=log_level,
    )
    # 添加日志文件
    logger.add('logs/codes_merger_{time}.log', rotation='10 MB', level='DEBUG', compression='zip')


def main():
    '''
    主函数，处理命令行参数并启动代码合并器
    '''
    parser = argparse.ArgumentParser(description='将源代码文件合并到Markdown文件中', formatter_class=argparse.RawTextHelpFormatter)

    # 将source_dir改为可选参数
    parser.add_argument('source_dir', type=str, nargs='?', 
                      help='源代码所在目录路径或Git仓库URL（如果提供了配置文件，可以从配置文件中读取）')

    parser.add_argument('-o', '--output', type=str, help='输出的Markdown文件名，如果可能分割文件则会自动添加后缀')

    parser.add_argument(
        '-l',
        '--languages',
        type=str,
        nargs='+',
        help=f'指定语言类型，可指定多个，支持的语言：{", ".join(SUPPORTED_LANGUAGES.keys())}',
    )

    parser.add_argument('-p', '--patterns', type=str, nargs='+', help='指定文件匹配模式，可指定多个，如 "*.cpp" "*test*.py"')

    parser.add_argument('-s', '--split-size', type=int, default=0, help='文件分割大小(KB)，当文件超过指定大小时将创建新文件，默认为0（不分割）')

    parser.add_argument('-t', '--threads', type=int, default=4, help='使用的线程数量，默认为4')

    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='设置日志级别，默认为INFO')

    parser.add_argument('--ignore', type=str, nargs='+', default=[], help='要忽略的目录或文件模式，可以指定多个，如 "venv" "*.temp"')

    parser.add_argument('-f', '--force', action='store_true', help='强制覆盖已存在的输出文件，不进行提示确认')

    # 新增配置文件相关参数
    parser.add_argument('-c', '--config', type=str, help='指定配置文件路径，默认查找当前目录下的codes_merger_config.yaml')
    
    # 新增Git相关参数
    parser.add_argument('-b', '--branch', type=str, help='指定Git仓库分支名称，只有当源是Git仓库时才有效')
    parser.add_argument('--keep-git-cache', action='store_true', help='保留克隆的Git仓库缓存，不自动清理')

    args = parser.parse_args()
    
    # 转换命令行参数为字典
    args_dict = vars(args)

    # 处理配置文件
    config = {}
    config_path = None
    
    # 如果指定了配置文件，尝试加载
    if args.config:
        config_path = Path(args.config)
    else:
        # 尝试加载默认配置文件
        default_config = get_default_config_path()
        if default_config.exists():
            config_path = default_config
    
    # 加载配置文件
    if config_path:
        try:
            config = load_config(config_path)
        except Exception as e:
            logger.error(f'加载配置文件失败: {e}')
            if args.config:  # 如果用户明确指定了配置文件但加载失败，退出程序
                sys.exit(1)
    print(f'config: {config}')
    print(f'args_dict: {args_dict}')
    # 合并配置文件和命令行参数
    merged_config = merge_config_with_args(config, args_dict)
    print(f'merged_config: {merged_config}')
    
    # 检查是否提供了source_dir（命令行或配置文件）
    if 'source_dir' not in merged_config or not merged_config['source_dir']:
        logger.error('必须提供源代码目录或Git仓库URL，可以通过命令行参数或配置文件指定')
        parser.print_help()
        sys.exit(1)

    # 设置日志级别
    setup_logger(merged_config.get('log_level', 'INFO'))
    
    # 处理源路径（目录或Git URL）
    source = merged_config['source_dir']
    # 创建Git处理器
    git_handler = GitRepoHandler(keep_git_cache=merged_config.get('keep_git_cache', False))
    source_dir = None

    try:
        # 检查是否是Git URL
        if git_handler.is_git_url(source):
            logger.info(f'检测到Git仓库URL: {source}')
                        
            # 克隆仓库
            branch = merged_config.get('branch')
            source_dir = git_handler.clone_repository(source, branch)
        else:
            # 普通目录路径
            source_dir = Path(source)
            if not source_dir.exists() or not source_dir.is_dir():
                logger.error(f'源目录路径不存在或不是目录: {source}')
                sys.exit(1)
    
        # 验证至少指定了语言或文件模式
        if not merged_config.get('languages') and not merged_config.get('patterns'):
            logger.error('至少需要指定语言(-l/--languages)或文件模式(-p/--patterns)中的一个')
            sys.exit(1)

        # 检查输出文件是否存在（考虑可能的切分文件）
        output_path = Path(merged_config.get('output', 'merged_code.md'))
        if not merged_config.get('force', False):
            should_prompt = False
            existing_files = []
            
            # 检查主输出文件
            if output_path.exists():
                should_prompt = True
                existing_files.append(output_path)
            
            # 检查可能的切分文件
            stem = output_path.stem
            suffix = output_path.suffix
            
            for split_file in Path(output_path.parent).glob(f'{stem}_*{suffix}'):
                should_prompt = True
                existing_files.append(split_file)
            
            if should_prompt:
                file_list = ', '.join(str(f) for f in existing_files)
                response = input(f'以下输出文件已存在: {file_list}\n是否覆盖? (y/n): ')
                if response.lower() not in ['y', 'yes']:
                    logger.info('操作已取消')
                    sys.exit(0)
                
                # 删除已存在的文件
                for file_path in existing_files:
                    if file_path.is_file():
                        logger.warning(f'删除已存在的文件: {file_path}')
                        file_path.unlink()
                    elif file_path.is_dir():
                        logger.error(f'{file_path} 是一个目录，无法覆盖')
                        sys.exit(1)

        # 创建并运行合并器
        merger = CodesMerger(
            source_dir=source_dir,
            output_file=merged_config.get('output', 'merged_code.md'),
            languages=merged_config.get('languages'),
            file_patterns=merged_config.get('patterns'),
            split_size=merged_config.get('split_size', 0),
            n_threads=merged_config.get('threads', 4),
            ignore_patterns=merged_config.get('ignore', []),
            force_overwrite=merged_config.get('force', False),
        )

        try:
            merger.run()
            logger.success('代码合并完成！')
        except Exception as e:
            logger.error(f'代码合并过程中发生错误: {e}')
            sys.exit(1)
            
    finally:
        # 如果使用了Git仓库，清理临时文件
        if git_handler:
            git_handler.cleanup()


if __name__ == '__main__':
    main()
