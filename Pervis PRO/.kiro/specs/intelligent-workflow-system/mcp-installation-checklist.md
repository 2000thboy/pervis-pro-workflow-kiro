## MCP 安装清单（Installation Checklist）

### 目标

- 以 `.mcp.json` 作为项目唯一 MCP 声明入口
- 固化 MCP Server 版本，避免 `@latest` 带来的不可重复构建

### 适配版本（与项目技术栈匹配）

- Node.js：`v24.12.0`
- npm：`11.6.2`

### MCP Server 组件与版本

- `chrome-devtools-mcp@0.12.1`
- `@hapins/figma-mcp@0.1.2`
- `@upstash/context7-mcp@1.0.33`
- `mcp-server-semgrep@1.0.0`
- `shadcn@3.6.2`（以 `mcp` 子命令启动）

### 配置文件与目录

- MCP 声明文件：`/.mcp.json`
- 日志目录（规范）：`/logs/mcp/`

```
Pervis PRO/
├── .mcp.json
├── backend/
├── frontend/
└── logs/
    └── mcp/
```

### 环境变量准备（按启用的 Server 配置）

- `FIGMA_ACCESS_TOKEN`
- `CONTEXT7_API_KEY`
- `SEMGREP_APP_TOKEN`

### 启动前检查

- `node -v` 输出为 `v24.12.0`
- `npm -v` 输出为 `11.6.2`
- `.mcp.json` 中的包版本已固定（非 `@latest`）

### 运行与集成参数

- MCP Server 的启动命令与参数由 `.mcp.json` 提供
- MCP Client（IDE/Agent）应从项目根目录读取 `.mcp.json` 并拉起相应 Server

### 监控与告警（最小规则）

- 进程存活监控：任一 MCP Server 进程退出即告警
- 启动失败熔断：5 分钟内连续失败 ≥ 3 次触发告警
- 日志采集：标准输出与错误输出汇聚至 `logs/mcp/` 并保留最近 7 天
