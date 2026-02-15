# 春节九天 AI Agent 教程 - 配套代码

本目录是春节 9 课的配套代码，基于 **UV** 工程管理。

## 环境要求

- **Python**: >= 3.14
- **UV**: 最新版（[安装指南](https://github.com/astral-sh/uv)）

## 依赖

| 包 | 版本 | 说明 |
|---|------|------|
| openai | >=1.0.0 | OpenAI 兼容 API 客户端 |
| loguru | >=0.7.0 | 日志模块 |
| tavily | >=0.2.0 | 搜索 API |
| httpx | - | HTTP 客户端（MCP 用） |
| pydantic | - | 数据验证 |

## 安装

```bash
# 安装 UV（如果未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 进入项目目录
cd exercise

# 复制环境变量配置
cp .env.example .env

# 安装依赖
uv sync
```

## API 配置

在 `exercise/.env` 文件中配置：

```bash
# OpenAI 兼容 API（必需）
OPENAI_KEY='your-api-key'
OPENAI_MODEL='kimi-k2.5'
OPENAI_BASE_URL='https://api.moonshot.cn/v1'

# 搜索服务（可选，第2-4课需要）
TAVILY_KEY='your-tavily-key'

# MCP 服务（可选，第3-4课需要）
CONTEXT7_API_KEY='your-context7-key'
GITHUB_PERSONAL_ACCESS_TOKEN='your-github-token'
```

### API 说明

| 服务 | 用途 | 获取方式 |
|------|------|----------|
| **Moonshot (Kim)** | LLM 模型 | https://platform.moonshot.cn/ |
| **Tavily** | 搜索工具 | https://tavily.com/ |
| **Context7** | 文档查询 | https://context7.com/ |
| **GitHub** | 代码操作 | https://github.com/settings/tokens |

## 目录结构

```
exercise/
├── lib/                    # 公共库（各课复用）
│   ├── env.py              # 环境变量加载
│   ├── openai_compat.py    # OpenAI 兼容 API
│   └── log.py              # 日志模块
├── 01_mini_agent_loop/      # 第 1 课：最小 Agent Loop
│   ├── main.py
│   └── agent.py
├── 02_tool_use/            # 第 2 课：Tool Use
│   ├── main.py
│   ├── agent.py
│   └── tools/
│       ├── base.py
│       ├── registry.py
│       ├── search.py
│       ├── datetime.py
│       ├── calculator.py
│       └── terminate.py
├── 03_mcp/                 # 第 3 课：MCP 工具协议
│   ├── main.py
│   ├── agent.py
│   ├── mcp_servers.json
│   └── tools/
│       ├── base.py
│       ├── registry.py
│       ├── mcp_client.py
│       └── ...
├── 04_skills/              # 第 4 课：Skill 技能系统
│   ├── main.py
│   ├── agent.py
│   ├── mcp_servers.json
│   └── tools/
│       ├── base.py
│       ├── registry.py
│       ├── mcp_client.py
│       ├── skill.py
│       └── ...
├── .claude/
│   └── skills/            # 安装的 Skills（第4课）
│       ├── doc-writer/
│       └── python-expert/
├── pyproject.toml
├── uv.lock
└── .env
```

## 各课代码

| 课程 | 目录 | 工具 |
|------|------|------|
| 第 1 课 | `01_mini_agent_loop/` | `terminate` |
| 第 2 课 | `02_tool_use/` | search、datetime、calculator、terminate |
| 第 3 课 | `03_mcp/` | Tavily MCP、Context7 MCP |
| 第 4 课 | `04_skills/` | Skill + Context7 + GitHub MCP |

## 运行方式

```bash
cd exercise

# 第 1 课：最小 Agent Loop
uv run python 01_mini_agent_loop/main.py --task "用三句话解释什么是 Agent Loop"

# 第 2 课：Tool Use
uv run python 02_tool_use/main.py --task "现在几点了？"

# 第 3 课：MCP
uv run python 03_mcp/main.py --task "python 教程"

# 第 4 课：Skill
uv run python 04_skills/main.py --task "列出已安装的 skills"
uv run python 04_skills/main.py --task "列出所有可用的MCP工具"
```

## 进阶运行

```bash
# 自定义最大步数
uv run python 04_skills/main.py --task "..." --max-steps 20

# 指定日志目录
uv run python 04_skills/main.py --task "..." --log-dir ./logs
```

## 项目理念

- **最小可运行**：每课代码尽量精简，便于理解核心概念
- **渐进式增强**：每课在上节课基础上增加新功能
- **真实 API**：不使用 mock，调用真实服务
- **UV 管理**：使用现代 Python 包管理器

## 常见问题

### Q: 运行时提示 "No module named 'env'"
A: 确保在 `exercise` 目录下运行，且已执行 `uv sync`

### Q: API Key 无效
A: 检查 `.env` 文件配置是否正确，确保 Key 已生效

### Q: 如何查看日志？
A: 默认日志在各课的 `logs/` 目录下
