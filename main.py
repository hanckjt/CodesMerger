#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
代码合并器入口模块

此模块提供命令行界面，用于将源代码文件合并到Markdown文件中。
'''

import argparse
import sys
from pathlib import Path
from loguru import logger

from merger import CodesMerger
from language_config import SUPPORTED_LANGUAGES


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

    parser.add_argument('source_dir', type=str, help='源代码所在目录路径')

    parser.add_argument('-o', '--output', type=str, default='merged_code.md', help='输出的Markdown文件名，默认为 merged_code.md')

    parser.add_argument(
        '-l',
        '--languages',
        type=str,
        nargs='+',
        choices=SUPPORTED_LANGUAGES.keys(),
        help=f'指定语言类型，可指定多个，支持的语言：{", ".join(SUPPORTED_LANGUAGES.keys())}',
    )

    parser.add_argument('-p', '--patterns', type=str, nargs='+', help='指定文件匹配模式，可指定多个，如 "*.cpp" "*test*.py"')

    parser.add_argument('-s', '--split-size', type=int, default=0, help='文件分割大小(KB)，当文件超过指定大小时将创建新文件，默认为0（不分割）')

    parser.add_argument('-t', '--threads', type=int, default=4, help='使用的线程数量，默认为4')

    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='设置日志级别，默认为INFO')

    parser.add_argument('--ignore', type=str, nargs='+', default=[], help='要忽略的目录或文件模式，可以指定多个，如 "venv" "*.temp"')

    parser.add_argument('-f', '--force', action='store_true', help='强制覆盖已存在的输出文件，不进行提示确认')

    args = parser.parse_args()

    # 设置日志级别
    setup_logger(args.log_level)

    # 验证输入目录路径
    source_dir = Path(args.source_dir)
    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(f'源目录路径不存在或不是目录: {args.source_dir}')
        sys.exit(1)

    # 验证至少指定了语言或文件模式
    if not args.languages and not args.patterns:
        logger.error('至少需要指定语言(-l/--languages)或文件模式(-p/--patterns)中的一个')
        sys.exit(1)

    # 检查输出文件是否存在（考虑可能的切分文件）
    output_path = Path(args.output)
    if not args.force:
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
        output_file=args.output,
        languages=args.languages,
        file_patterns=args.patterns,
        split_size=args.split_size,
        n_threads=args.threads,
        ignore_patterns=args.ignore,
        force_overwrite=args.force,
    )

    try:
        merger.run()
        logger.success('代码合并完成！')
    except Exception as e:
        logger.error(f'代码合并过程中发生错误: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
