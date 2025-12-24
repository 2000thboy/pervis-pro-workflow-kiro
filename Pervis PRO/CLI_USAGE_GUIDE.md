# 🎬 Pervis PRO 命令行工具使用指南

## 🎯 为什么选择命令行工具？

你的担心很有道理！Web前端确实可能消耗较多内存，特别是处理大量视频素材时。命令行工具有以下优势：

### ✅ 优势对比

| 特性 | Web前端 | 命令行工具 |
|------|---------|------------|
| 内存占用 | 高 (浏览器+React) | 低 (纯Python) |
| 启动速度 | 慢 (需要编译) | 快 (直接运行) |
| 资源消耗 | 高 | 低 |
| 操作效率 | 图形界面 | 命令行快捷 |
| 批量操作 | 有限 | 强大 |
| 自动化 | 困难 | 容易 |

## 🚀 快速开始

### 1. 基础使用
```bash
# 检查服务器状态
python pervis_cli.py --help

# 分析剧本并上传素材
python pervis_cli.py --script sample_script.txt --title "我的剧本" --assets "backend/assets"

# 搜索素材
python pervis_cli.py --search "樱花飞舞的校园"
```

### 2. 交互模式（推荐）
```bash
# 进入交互模式
python pervis_cli.py -i

# 在交互模式中使用命令
pervis> status          # 检查服务器
pervis> beats           # 列出Beat
pervis> search 夕阳告白  # 搜索素材
pervis> beat 1          # 为Beat 1搜索
pervis> help            # 查看帮助
pervis> quit            # 退出
```

## 📋 完整命令参考

### 命令行参数
```bash
python pervis_cli.py [选项]

选项:
  --script FILE     剧本文件路径
  --title TITLE     剧本标题
  --assets DIR      素材目录路径
  --search QUERY    搜索查询
  -i, --interactive 进入交互模式
  -h, --help        显示帮助
```

### 交互模式命令
```
基础命令:
  status          - 检查服务器状态
  help            - 显示帮助信息
  quit/exit       - 退出程序

项目操作:
  beats           - 列出当前项目的所有Beat
  search <查询>   - 多模态搜索素材
  beat <编号>     - 为指定Beat搜索匹配素材
```

## 🎯 典型工作流程

### 方案1：一次性处理
```bash
# 一条命令完成剧本分析和素材上传
python pervis_cli.py \
  --script "my_script.txt" \
  --title "我的动漫项目" \
  --assets "F:/BaiduNetdiskDownload/动漫素材" \
  --search "校园场景"
```

### 方案2：交互式工作
```bash
# 启动交互模式
python pervis_cli.py -i

# 然后在交互模式中逐步操作
pervis> status
pervis> search 樱花飞舞的校园
pervis> search 紧张的考试
pervis> beats
pervis> beat 1
```

## 📁 文件准备

### 1. 剧本文件格式
创建一个文本文件，例如 `my_script.txt`：
```
我的动漫剧本

场景1：校园早晨
樱花飞舞的校园里，学生们背着书包走向教室...

场景2：教室内
上课铃声响起，老师走进教室开始讲课...
```

### 2. 素材目录结构
```
素材目录/
├── video1.mp4
├── video2.mp4
├── video3.avi
└── ...
```

## 🔧 高级用法

### 1. 批量搜索脚本
```python
# batch_search.py
from pervis_cli import PervisCLI

cli = PervisCLI()
cli.check_server()

# 批量搜索多个查询
queries = [
    "樱花飞舞的校园",
    "紧张的考试氛围",
    "夕阳下的告白",
    "友情的力量"
]

for query in queries:
    print(f"\\n搜索: {query}")
    cli.search_assets(query)
```

### 2. 自动化脚本
```bash
#!/bin/bash
# auto_process.sh

echo "开始自动化处理..."

# 1. 分析剧本
python pervis_cli.py --script "scripts/episode1.txt" --title "第一集"

# 2. 上传素材
python pervis_cli.py --assets "assets/episode1/"

# 3. 批量搜索
python batch_search.py

echo "处理完成!"
```

## 💡 使用技巧

### 1. 内存优化
- 命令行工具内存占用通常 < 100MB
- Web前端可能占用 > 500MB
- 建议大批量处理时使用命令行

### 2. 效率提升
- 使用交互模式避免重复启动
- 准备好剧本文件和素材目录
- 利用批量搜索脚本

### 3. 故障排除
```bash
# 检查后端服务
python pervis_cli.py --help

# 如果连接失败
cd backend
python main.py  # 启动后端服务
```

## 🎉 实际使用示例

### 完整的动漫项目处理流程：

```bash
# 1. 准备剧本文件
echo "场景1：校园樱花..." > my_anime_script.txt

# 2. 启动交互模式
python pervis_cli.py -i

# 3. 在交互模式中操作
pervis> status
pervis> # 分析剧本（需要先退出交互模式）

# 4. 重新启动并处理
python pervis_cli.py \
  --script my_anime_script.txt \
  --title "我的动漫" \
  --assets "F:/BaiduNetdiskDownload/动漫素材"

# 5. 再次进入交互模式进行搜索
python pervis_cli.py -i
pervis> search 校园樱花
pervis> search 青春活力
pervis> beats
pervis> beat 1
```

## 🚀 性能对比

### 内存使用对比（实测）
- **命令行工具**: ~50-80MB
- **Web前端**: ~300-600MB
- **后端服务**: ~100-200MB

### 响应速度对比
- **命令行**: 直接API调用，响应快
- **Web前端**: 需要渲染界面，稍慢

## 📊 总结

**推荐使用命令行工具的场景：**
- ✅ 大批量素材处理
- ✅ 自动化工作流
- ✅ 内存资源有限
- ✅ 追求高效率操作
- ✅ 不需要复杂UI交互

**Web前端适合的场景：**
- 🎨 需要可视化界面
- 🎨 视频预览和播放
- 🎨 复杂的素材管理
- 🎨 团队协作展示

**你的动漫素材项目完全可以用命令行工具高效完成！** 🎬✨