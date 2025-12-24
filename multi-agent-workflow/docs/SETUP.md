# 多Agent协作工作流系统安装指南

## 系统要求

- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd multi-agent-workflow
```

### 2. 自动环境设置

```bash
python scripts/setup.py
```

### 3. 配置数据库

编辑 `backend/.env` 文件，设置数据库连接信息：

```env
DATABASE_URL=postgresql://username:password@localhost:5432/multi_agent_workflow
REDIS_URL=redis://localhost:6379/0
```

### 4. 初始化数据库

```bash
python scripts/init_db.py
```

### 5. 启动服务

#### 使用Docker Compose（推荐）

```bash
docker-compose up -d
```

#### 手动启动

启动后端服务：
```bash
cd backend
python main.py
```

启动前端界面：
```bash
cd frontend
npm start
```

启动桌面启动器：
```bash
cd launcher
python src/main.py
```

## 访问系统

- Web界面: http://localhost:3000
- API文档: http://localhost:8000/docs
- 桌面启动器: 运行 `launcher/src/main.py`

## 开发指南

### 后端开发

1. 激活虚拟环境：
   ```bash
   cd backend
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   ```

2. 安装开发依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 运行测试：
   ```bash
   pytest
   ```

### 前端开发

1. 安装依赖：
   ```bash
   cd frontend
   npm install
   ```

2. 启动开发服务器：
   ```bash
   npm start
   ```

3. 运行测试：
   ```bash
   npm test
   ```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务是否运行
   - 验证数据库连接配置
   - 确认数据库用户权限

2. **Redis连接失败**
   - 检查Redis服务是否运行
   - 验证Redis连接配置

3. **前端无法连接后端**
   - 检查后端服务是否运行在8000端口
   - 验证CORS配置

### 日志查看

- 后端日志: `backend/data/logs/app.log`
- 前端日志: 浏览器开发者工具
- 启动器日志: 启动器界面日志窗口

## 更多信息

- [API文档](http://localhost:8000/docs)
- [架构设计](../design.md)
- [需求文档](../requirements.md)