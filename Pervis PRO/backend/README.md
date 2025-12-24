# Pervis PRO 导演工作台 - 后端 API

## Phase 1: 最小可运行系统

这是导演工作台的后端 API，当前处于 Phase 1 阶段，提供基础的 mock 接口。

## 快速启动

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务：
```bash
python main.py
```

3. 访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 剧本处理
- `POST /api/script/analyze` - 剧本分析，生成 Beat 列表

### 素材管理  
- `POST /api/assets/upload` - 上传视频素材
- `GET /api/assets/{id}/status` - 查询处理状态

### 语义搜索
- `POST /api/search/semantic` - 根据 Beat 搜索匹配素材

### 反馈收集
- `POST /api/feedback/record` - 记录用户反馈

## Phase 1 限制

- 所有接口返回 mock 数据
- 不连接真实数据库
- 不调用真实 AI 服务
- 不处理真实文件上传

## 验收标准

- ✅ `uvicorn main:app` 可以启动
- ✅ `/docs` 可以正常访问
- ✅ 每个接口都能返回 JSON 数据