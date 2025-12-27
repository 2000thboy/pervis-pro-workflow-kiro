# 对话上下文管理规则

## 上下文存储

使用 SQLite MCP 存储对话上下文，数据库路径：`./Pervis PRO/data/workflow.db`

### 数据表结构

1. **conversation_context** - 详细上下文记录
   - session_id: 会话ID
   - context_type: 类型 (task/decision/issue/note)
   - title: 标题
   - content: 内容
   - tags: 标签（逗号分隔）
   - related_files: 相关文件路径

2. **conversation_summary** - 会话摘要
   - session_id: 会话ID
   - summary: 总结
   - key_decisions: 关键决策
   - pending_tasks: 待办任务
   - project_context: 项目上下文

## 使用方法

### 保存上下文
```sql
INSERT INTO conversation_context (session_id, context_type, title, content, tags, related_files)
VALUES ('session-id', 'task', '标题', '内容', 'tag1,tag2', 'file1.py,file2.ts');
```

### 读取上下文
```sql
-- 按 session_id 查询
SELECT * FROM conversation_summary WHERE session_id = 'xxx';

-- 查询最近记录
SELECT * FROM conversation_summary ORDER BY updated_at DESC LIMIT 5;

-- 按标签搜索
SELECT * FROM conversation_context WHERE tags LIKE '%keyword%';
```

## 自动行为

- 对话结束时：自动总结并保存到数据库
- 新对话开始时：检查并显示最近的工作进度
