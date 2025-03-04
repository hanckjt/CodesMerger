#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
语言配置模块

此模块定义了支持的编程语言及其文件扩展名。
'''

# 支持的语言及其文件后缀
SUPPORTED_LANGUAGES = {
    'python': {'.py', '.pyw', '.pyx'},
    'java': {'.java'},
    'cpp': {'.cpp', '.cc', '.cxx', '.hpp', '.hh', '.hxx', '.h'},
    'javascript': {'.js', '.jsx', '.ts', '.tsx'},
    'go': {'.go'},
    'rust': {'.rs'},
    'c': {'.c', '.h'},
    'html': {'.html', '.htm', '.css'},
    'shell': {'.sh', '.bash', '.zsh'},
    'csharp': {'.cs'},
    'php': {'.php', '.phtml', '.php3', '.php4', '.php5', '.phps'},
}

# 文件扩展名与语言映射
FILE_EXTENSION_LANGUAGE_MAP = {
    '.py': 'python',
    '.pyw': 'python',
    '.pyx': 'python',
    '.java': 'java',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.hpp': 'cpp',
    '.hh': 'cpp',
    '.hxx': 'cpp',
    '.h': 'cpp',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.go': 'go',
    '.rs': 'rust',
    '.c': 'c',
    '.html': 'html',
    '.htm': 'html',
    '.css': 'html',
    '.sh': 'shell',
    '.bash': 'shell',
    '.zsh': 'shell',
    '.cs': 'csharp',
    '.php': 'php',
    '.phtml': 'php',
    '.php3': 'php',
    '.php4': 'php',
    '.php5': 'php',
    '.phps': 'php',
}