#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
配置加载器模块

此模块用于从YAML文件加载应用配置。
'''

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


def load_config(config_file: Path) -> Dict[str, Any]:
    '''
    从YAML文件加载配置

    :param config_file: 配置文件路径
    :type config_file: Path
    :return: 配置字典
    :rtype: Dict[str, Any]
    :raises FileNotFoundError: 当配置文件不存在时抛出
    :raises yaml.YAMLError: 当YAML解析错误时抛出
    '''
    if not config_file.exists():
        logger.error(f'配置文件不存在: {config_file}')
        raise FileNotFoundError(f'配置文件不存在: {config_file}')
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            logger.info(f'已成功加载配置文件: {config_file}')
            return config or {}
    except yaml.YAMLError as e:
        logger.error(f'解析配置文件时出错: {e}')
        raise
    except Exception as e:
        logger.error(f'读取配置文件时出错: {e}')
        raise


def merge_config_with_args(config: Dict[str, Any], args_dict: Dict[str, Any]) -> Dict[str, Any]:
    '''
    合并配置文件和命令行参数，命令行参数优先级更高

    :param config: 从配置文件加载的配置
    :type config: Dict[str, Any]
    :param args_dict: 命令行参数字典
    :type args_dict: Dict[str, Any]
    :return: 合并后的配置
    :rtype: Dict[str, Any]
    '''
    # 创建配置文件的副本
    merged = config.copy()
    
    # 遍历命令行参数
    for key, value in args_dict.items():
        # None值表示参数未提供
        if value is not None:
            # 处理特殊情况：默认值等于[]的列表类型参数
            if isinstance(value, list) and key in merged and not value:
                # 保留配置文件中的值
                continue
                
            # 命令行参数覆盖配置文件
            merged[key] = value
            
    logger.debug(f'合并后的配置: {merged}')
    return merged


def get_default_config_path() -> Path:
    '''
    获取默认配置文件路径

    :return: 默认配置文件路径
    :rtype: Path
    '''
    return Path('codes_merger_config.yaml')
