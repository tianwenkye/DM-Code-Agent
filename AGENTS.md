# DM-Code-Agent 开发指南

本文件为 AI 编码代理提供项目特定的代码规范、工具和最佳实践。

## 构建和测试命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用
```bash
# 交互模式
python main.py

# 命令行模式
python main.py "任务描述"

# 指定提供商
python main.py "任务" --provider openai --model gpt-4
```

### 环境配置
- 复制 `.env.example` 到 `.env` 并配置 API 密钥
- 支持的提供商：deepseek, openai, claude, gemini
- 配置文件：`config.json`（可选，用于持久化设置）

### RAG功能配置
- **Elasticsearch配置**：
  - `ES_HOST`: Elasticsearch地址（如 http://localhost:9200）
- **向量API配置**：
  - `DASHSCOPE_API_KEY`: DashScope API密钥（用于向量生成）
  - `DASHSCOPE_BASE_URL`: DashScope API地址（默认：https://dashscope.aliyuncs.com/compatible-mode/v1）

### RAG功能使用
1. **导入文档到ES**：
   ```bash
   # 导入单个文件
   python scripts/import_documents.py --file document.pdf --index my_knowledge_base

   # 导入整个目录
   python scripts/import_documents.py --directory ./docs --index my_knowledge_base

   # 递归导入目录
   python scripts/import_documents.py --directory ./docs --index my_knowledge_base --recursive
   ```

2. **测试RAG功能**：
   ```bash
   python scripts/test_rag.py
   ```

3. **在Agent中使用RAG**：
   - 创建session时指定ES索引：
     ```python
     session_id = await agent_service.create_session(
         provider="deepseek",
         model="deepseek-chat",
         es_index_names=["my_knowledge_base"]  # 指定ES索引
     )
     ```
   - Agent执行任务时会自动进行RAG检索
   - 检索结果会增强任务描述，提供给Planner使用

### 测试
- 本项目当前没有自动化测试套件
- 手动测试：使用 `python main.py` 进入交互模式
- 验证工具：选择"查看可用工具列表"检查工具可用性

## 代码风格规范

### 导入顺序
1. 标准库导入
2. 第三方库导入
3. 本地模块导入（相对导入）
4. 每组之间用空行分隔

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from .base import BaseClass
```

### 类型注解
- 使用 `from __future__ import annotations` 启用延迟求值
- 使用 `typing` 模块：`Any`, `Dict`, `List`, `Optional`, `Callable`
- 联合类型使用 `|` 语法（Python 3.10+）或 `Union`

```python
def function_name(param: str, optional: Optional[int] = None) -> Dict[str, Any]:
    return {"key": param}
```

### 命名约定
- **类名**: `PascalCase`（如 `ReactAgent`, `BaseLLMClient`）
- **函数/方法**: `snake_case`（如 `create_file`, `run_tests`）
- **常量**: `UPPER_SNAKE_CASE`（如 `MAX_STEPS`, `DEFAULT_MODEL`）
- **私有成员**: 前缀下划线 `_private_var`
- **数据类字段**: `snake_case`

### 数据结构
- 优先使用 `@dataclass` 定义简单数据容器
- 使用 `field(default_factory=list)` 处理可变默认值

```python
from dataclasses import dataclass, field

@dataclass
class Step:
    thought: str
    action: str
    observation: str = ""
    raw: str = ""
```

### 抽象基类
- 使用 `abc.ABC` 和 `@abstractmethod` 定义接口
- 所有抽象方法必须在子类中实现

```python
from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    @abstractmethod
    def complete(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        pass
```

### 文件操作
- 使用 `pathlib.Path`` 而非 `os.path`
- 路径操作：`Path("path/to/file")`
- 创建目录：`path.parent.mkdir(parents=True, exist_ok=True)`
- 读写文件：`path.read_text(encoding="utf-8")`, `path.write_text(content, encoding="utf-8")`

### 错误处理
- 使用自定义异常类继承 `RuntimeError`
- 工具参数验证使用 `ValueError`
- API 错误使用 `LLMError`
- 始终提供有意义的错误消息

```python
if not api_key:
    raise ValueError("LLM 客户端需要 API 密钥。")

try:
    result = operation()
except LLMError as e:
    print(f"API 错误：{e}")
```

### 文档字符串
- 所有公共类和函数必须有 docstring
- 使用中文编写文档和注释
- Google 风格或简洁风格

```python
def create_file(arguments: Dict[str, Any]) -> str:
    """创建或覆盖文本文件"""
    path_value = _require_str(arguments, "path")
    # ...
```

### 工具定义
- 继承或使用 `Tool` 数据类
- 工具函数签名：`def tool_name(arguments: Dict[str, Any]) -> str`
- 使用 `_require_str` 验证必需的字符串参数

```python
def my_tool(arguments: Dict[str, Any]) -> str:
    """工具描述"""
    path = _require_str(arguments, "path")
    optional = arguments.get("optional_param", default_value)
    # ...
    return "执行结果"
```

### CLI 输出
- 使用 `colorama` 进行彩色输出
- 前景色：`Fore.GREEN`, `Fore.YELLOW`, `Fore.RED`, `Fore.CYAN`, `Fore.MAGENTA`
- 样式：`Style.BRIGHT`, `Style.RESET_ALL`
- 错误输出到 `sys.stderr`

### 配置管理
- 环境变量：使用 `python-dotenv` 加载 `.env`
- JSON 配置：使用 `json.dump/load`，设置 `ensure_ascii=False`
- 配置文件路径：`os.path.join(os.path.dirname(__file__), "config.json")`

## 项目架构

### 核心模块
- `dm_agent/core/`: ReactAgent 和任务规划器
- `dm_agent/clients/`: LLM 客户端（deepseek, openai, claude, gemini）
- `dm_agent/tools/`: 工具集（文件、代码分析、执行）
- `dm_agent/skills/`: 专家技能系统
- `dm_agent/mcp/`: MCP 协议集成
- `dm_agent/memory/`: 上下文压缩器
- `dm_agent/prompts/`: 提示词管理

### 扩展指南
- **新工具**: 在 `dm_agent/tools/` 中创建函数，使用 `Tool` 数据类包装
- **新 LLM 客户端**: 继承 `BaseLLMClient`，实现 `complete` 和 `extract_text`
- **新技能**: 继承 `BaseSkill` 或使用 `ConfigSkill` JSON 配置
- **自定义技能**: 在 `dm_agent/skills/custom/` 创建 JSON 文件

## 重要规则（来自 .clinerules）
- 始终使用中文与用户交流
- 代码变量名、函数名可以使用英文
- 注释和文档说明必须是中文

## 开发注意事项
- 不添加任何注释，除非明确要求
- 优先编辑现有文件而非创建新文件
- 遵循现有代码风格和模式
- 使用已安装的库（requests, python-dotenv, colorama, openai, anthropic, google-genai）

## RAG集成架构

### 核心组件
1. **文档服务** (`backend/app/service/core/document_service.py`)
   - 文档解析（支持PDF、DOCX、Excel、TXT、HTML、JSON、Markdown、PPT等）
   - 向量生成（使用DashScope API）
   - ES存储（批量插入文档块）

2. **检索服务** (`backend/app/service/core/retrieval_service.py`)
   - 混合检索（向量+关键词）
   - 结果格式化
   - 任务增强

3. **RAG模块** (`backend/app/service/core/rag/`)
   - 文档解析器（naive.py）
   - NLP处理（分词、查询、重排序）
   - ES连接管理
   - 向量模型接口

4. **DeepDoc模块** (`backend/app/service/core/deepdoc/`)
   - PDF解析（OCR+布局识别）
   - 文档解析器集合
   - 视觉识别组件

### 工作流程
1. **文档导入流程**：
   ```
   文件 → 解析 → 分块 → 向量化 → ES存储
   ```

2. **RAG检索流程**：
   ```
   任务 → 检索ES → 格式化结果 → 增强任务 → Planner
   ```

3. **Agent执行流程**：
   ```
   创建session（指定ES索引）→ 执行任务 → RAG检索 → 增强任务 → 生成计划 → 执行步骤
   ```

### 关键特性
- **自动检索**：Agent执行任务前自动进行RAG检索
- **任务增强**：检索结果自动拼接上原始任务
- **默认启用**：RAG功能默认启用，无需额外配置
- **错误容错**：RAG失败时不影响Agent正常运行
- **批量处理**：支持批量导入文档和向量生成
