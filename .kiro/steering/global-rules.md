# 全局开发规则

## 语言偏好

- 所有回复和文档使用中文
- 代码注释可以使用中文或英文

## 命令行环境

- 本项目运行在 Windows 系统上
- 使用 `py` 命令代替 `python` 执行 Python 脚本
- 测试命令从 `Pervis PRO/backend` 目录执行

## 命令执行注意事项

- **避免使用需要交互式输入的命令**，防止终端卡住等待用户输入
- npm/yarn 命令加 `-y` 或 `--yes` 跳过确认提示
- git commit 必须用 `-m "message"` 指定提交信息
- 安装脚本优先使用静默模式 (silent/quiet mode)
- pip 安装使用 `--yes` 或避免需要确认的操作
- 如果必须执行可能需要输入的命令，先告知用户可能需要手动干预

## 测试规范

### 属性测试 (Property-Based Testing)

- 使用 Hypothesis 库进行属性测试
- 每个属性测试配置 `@settings(max_examples=100, deadline=None)`
- 测试文件命名格式: `test_<模块名>_properties.py`

### Hypothesis 策略注意事项

- **重要**: 当使用 `st.text()` 生成需要匹配正则表达式的字符串时，必须使用显式字符集
- 避免使用 `whitelist_categories` 参数，因为它会包含非 ASCII Unicode 字符
- 例如，生成匹配 `^[a-z0-9_-]+$` 的标签时：
  ```python
  # ❌ 错误 - 会生成 Unicode 字符如 'µ'
  st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Nd')))
  
  # ✅ 正确 - 只生成 ASCII 字符
  st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_-')
  ```

### 测试执行

- 运行测试: `py -m pytest tests/<测试文件>.py -v --tb=short`
- 从 `Pervis PRO/backend` 目录执行测试命令

## 项目结构

```
Pervis PRO/
├── backend/
│   ├── core/            # 核心组件 (消息总线、通信协议、BaseAgent)
│   ├── services/
│   │   └── agents/      # Agent 实现
│   ├── routers/         # API 路由
│   ├── models/          # 数据模型
│   └── tests/           # 测试文件
├── frontend/            # React 前端
└── launcher/            # 桌面启动器
```

## Agent 开发规范

- 所有 Agent 继承自 `core.BaseAgent` 基类
- 使用 `core.MessageBus` 进行 Agent 间通信
- Agent 类型定义在 `core.agent_types.py` 的 `AgentType` 枚举中
- Agent 实现放在 `services/agents/` 目录
