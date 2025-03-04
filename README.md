# Codes Merger - 代码合并工具

Codes Merger 是一个Python工具，用于将指定目录下的源代码文件合并到一个或多个Markdown文件中。该工具支持多种编程语言，可以通过命令行参数进行配置。

## 特性

- 支持多种常用编程语言的源代码文件
- 支持按文件名模式匹配文件
- 支持同时选择多种语言或多种文件模式
- 根据文件类型自动设置Markdown中的代码语言标识
- 多线程处理提高效率
- 文件大小限制，支持自动分割
- 详细的日志记录
- 实时进度显示
- 可配置的忽略模式
- 输出文件存在时提供覆盖确认

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

基本用法：

```bash
python main.py <源代码目录> [-l 语言1 语言2...] [-p 模式1 模式2...]
```

必须指定语言或文件模式中的至少一项。

### 命令行选项

- `source_dir`: 源代码所在目录路径
- `-o, --output`: 输出的Markdown文件名，默认为 `merged_code.md`
- `-l, --languages`: 指定语言类型，可指定多个
- `-p, --patterns`: 指定文件匹配模式，可指定多个，如 "*.cpp" "*test*.py"
- `-s, --split-size`: 文件分割大小(KB)，当文件超过指定大小时将创建新文件，默认为0（不分割）
- `-t, --threads`: 使用的线程数量，默认为4
- `--log-level`: 设置日志级别，默认为INFO
- `--ignore`: 要忽略的目录或文件模式，可以指定多个，如 "venv" "*.temp"
- `-f, --force`: 强制覆盖已存在的输出文件，不进行提示确认

### 示例

合并Python代码：

```bash
python main.py /path/to/project -l python
```

合并多种语言的代码：

```bash
python main.py /path/to/project -l python cpp javascript
```

使用文件模式匹配：

```bash
python main.py /path/to/project -p "*.cpp" "*test*.py"
```

同时使用语言和文件模式：

```bash
python main.py /path/to/project -l python -p "*test*.py" "*.h"
```

限制文件大小并使用8个线程：

```bash
python main.py /path/to/project -l cpp -s 5000 -t 8
```

忽略特定目录和文件：

```bash
python main.py /path/to/project -l python -p "*.py" --ignore "venv" "node_modules" "*.log"
```

强制覆盖已存在的文件：

```bash
python main.py /path/to/project -l python -f
```

## 支持的语言

目前支持以下常用编程语言：

- python
- java
- cpp (C/C++)
- c#
- javascript (包括TypeScript)
- go
- rust
- html (包括CSS)
- shell
- php
