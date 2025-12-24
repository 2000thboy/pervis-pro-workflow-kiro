# 演示素材最小需求清单

**目的**: 确保5分钟标准演示100%可复现  
**原则**: 最小化、确定性、可替换性  
**版本**: v1.0 FROZEN

---

## 📦 最小素材要求

### 核心要求
- **素材数量**: 最少3个视频文件
- **处理状态**: 全部processing_status='completed'
- **主题匹配**: 至少2个与剧本Beat相关
- **文件格式**: MP4（H.264编码优先）

---

## 🎬 推荐素材清单

### 素材1：城市夜景/追逐场景
**用途**: 匹配Beat 1"城市追逐"  
**关键词**: 城市、夜晚、霓虹灯、动态、速度感  
**技术要求**:
- 格式：MP4
- 分辨率：≥720p
- 时长：5-30秒
- 码率：≥2Mbps
- 帧率：≥24fps

**推荐素材来源**:
1. **Pexels**（免费）: 搜索"cyberpunk city night"
   - 链接示例：pexels.com/search/cyberpunk%20city/
   - 选择标签：Free to use, No attribution required

2. **Pixabay**（免费）: 搜索"neon city timelapse"
   - 链接示例：pixabay.com/videos/search/neon%20city/
   
3. **现有素材库**: 
   - 检查 `backend/assets/originals/` 中已有文件
   - 选择包含城市、运动、夜景元素的视频

**质量标准**:
- ✅ 画面清晰，无明显噪点
- ✅ 包含城市/建筑元素
- ✅ 有动态元素（车辆、人群、灯光）
- ✅ 色调偏蓝紫色调（赛博朋克风格）

---

### 素材2：科技/黑客场景
**用途**: 匹配Beat 2"黑客入侵"  
**关键词**: 代码、屏幕、数据流、科技感  
**技术要求**: 同素材1

**推荐素材来源**:
1. **Pexels**: 搜索"coding screen hacker"
2. **Pixabay**: 搜索"matrix code data"
3. **自制素材**: 
   - 录制终端/IDE界面
   - 使用CMatrix等工具生成代码雨效果
   - 录制数据可视化动画

**质量标准**:
- ✅ 显示代码或数据界面
- ✅ 有动态效果（文字滚动、闪烁）
- ✅ 色调偏绿色或蓝色（科技感）
- ✅ 背景昏暗（黑客氛围）

---

### 素材3：动作/对决场景  
**用途**: 匹配Beat 3"终极对决"  
**关键词**: 动作、火花、工业、冲突  
**技术要求**: 同素材1

**推荐素材来源**:
1. **Pexels**: 搜索"industrial sparks metal"
2. **Pixabay**: 搜索"factory warehouse action"
3. **替代素材**: 任何包含快速运动、冲击感的视频

**质量标准**:
- ✅ 快节奏、高动态
- ✅ 包含工业/金属元素
- ✅ 有视觉冲击力（火花、碰撞等）
- ✅ 色调暗沉或高对比度

---

## 🔧 素材准备步骤

### 步骤1：下载或选择素材
```bash
# 创建临时目录
mkdir -p temp_demo_assets

# 下载或复制素材到此目录
# 文件命名建议：
# - demo_asset_01_city_night.mp4
# - demo_asset_02_hacker_screen.mp4
# - demo_asset_03_action_sparks.mp4
```

### 步骤2：上传到系统
```bash
# 方法1：使用现有上传脚本
python mvp_demo_script.py  # 会自动上传temp_demo_assets中的文件

# 方法2：通过前端界面上传
# 1. 访问 http://localhost:3000
# 2. 进入"素材库"标签
# 3. 点击"上传素材"
# 4. 选择3个文件上传

# 方法3：直接复制到assets目录
cp temp_demo_assets/*.mp4 backend/assets/originals/
python backend/scripts/process_new_assets.py  # 如果有此脚本
```

### 步骤3：等待处理完成
```bash
# 检查处理状态
python -c "
import sqlite3
import time

conn = sqlite3.connect('backend/pervis_director.db')

while True:
    cursor = conn.execute('''
        SELECT filename, processing_status, processing_progress 
        FROM assets 
        ORDER BY created_at DESC 
        LIMIT 3
    ''')
    
    print('\\n最新素材处理状态:')
    all_completed = True
    for row in cursor.fetchall():
        filename, status, progress = row
        print(f'  {filename}: {status} ({progress}%)')
        if status != 'completed':
            all_completed = False
    
    if all_completed:
        print('\\n✅ 所有素材处理完成！')
        break
    else:
        print('\\n⏳ 继续等待...')
        time.sleep(10)

conn.close()
"
```

### 步骤4：验证素材可用性
```bash
# 检查数据库记录
sqlite3 backend/pervis_director.db << EOF
SELECT 
    id,
    filename,
    processing_status,
    proxy_path IS NOT NULL as has_proxy,
    thumbnail_path IS NOT NULL as has_thumbnail
FROM assets
WHERE processing_status = 'completed'
LIMIT 10;
EOF

# 检查物理文件
ls -lh backend/assets/proxies/
ls -lh backend/assets/thumbnails/
```

---

## 📋 素材验收标准

### 技术验收
- [ ] 3个素材文件存在于 `backend/assets/originals/`
- [ ] 3个代理文件存在于 `backend/assets/proxies/`
- [ ] 3个缩略图存在于 `backend/assets/thumbnails/`
- [ ] 数据库中3条记录 processing_status='completed'
- [ ] 所有素材可通过API查询到

### 功能验收
- [ ] 在前端"素材库"可看到3个素材
- [ ] 点击缩略图可预览视频
- [ ] 视频播放流畅（代理文件）
- [ ] 搜索功能可返回至少1个结果

### 演示验收
- [ ] 使用标准演示脚本完整走完流程
- [ ] Beat搜索返回≥1个结果
- [ ] 预览播放无卡顿、无报错
- [ ] 5分钟内完成所有步骤

---

## 🚀 快速素材准备（15分钟）

### 快捷方案1：使用现有素材
```bash
# 检查现有素材库
ls backend/assets/originals/ | wc -l

# 如果已有≥3个文件，检查处理状态
python -c "
import sqlite3
conn = sqlite3.connect('backend/pervis_director.db')
cursor = conn.execute('SELECT COUNT(*) FROM assets WHERE processing_status=\"completed\"')
count = cursor.fetchone()[0]
print(f'已完成处理的素材: {count} 个')
if count >= 3:
    print('✅ 素材充足，无需准备')
else:
    print('❌ 需要准备更多素材')
"
```

### 快捷方案2：批量下载推荐素材
```python
# quick_download_demo_assets.py
import requests
from pathlib import Path

# 推荐的免费素材直链（示例，需替换为实际链接）
ASSET_URLS = [
    "https://example.com/cyberpunk_city.mp4",  # 替换为实际URL
    "https://example.com/hacker_screen.mp4",   # 替换为实际URL
    "https://example.com/action_scene.mp4",    # 替换为实际URL
]

output_dir = Path("temp_demo_assets")
output_dir.mkdir(exist_ok=True)

for i, url in enumerate(ASSET_URLS, 1):
    filename = f"demo_asset_{i:02d}.mp4"
    filepath = output_dir / filename
    
    print(f"下载素材 {i}/{len(ASSET_URLS)}: {filename}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ 完成: {filename} ({filepath.stat().st_size / 1024 / 1024:.1f} MB)")
    except Exception as e:
        print(f"❌ 失败: {e}")

print(f"\n📦 素材已保存到: {output_dir.absolute()}")
```

### 快捷方案3：创建测试素材（无版权问题）
```python
# create_synthetic_demo_assets.py
# 使用OpenCV创建简单的测试视频

import cv2
import numpy as np
from pathlib import Path

def create_test_video(filename, duration=10, fps=24):
    """创建简单的测试视频"""
    output_dir = Path("temp_demo_assets")
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / filename
    
    width, height = 1280, 720
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    for frame_num in range(total_frames):
        # 创建渐变背景
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加动态效果
        color_shift = int((frame_num / total_frames) * 255)
        frame[:, :] = [color_shift, 100, 255 - color_shift]
        
        # 添加文字
        text = f"Demo Asset Frame {frame_num}"
        cv2.putText(frame, text, (50, height//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        video.write(frame)
    
    video.release()
    print(f"✅ 创建: {filename}")

# 创建3个测试视频
create_test_video("demo_asset_01_synthetic.mp4", duration=8)
create_test_video("demo_asset_02_synthetic.mp4", duration=10)
create_test_video("demo_asset_03_synthetic.mp4", duration=12)

print("📦 合成素材已创建完成")
```

---

## 🔍 故障排查

### 问题1：素材上传失败
**症状**: API返回错误或超时  
**检查**:
```bash
# 检查文件格式
file temp_demo_assets/*.mp4

# 检查文件大小
ls -lh temp_demo_assets/*.mp4

# 检查磁盘空间
df -h backend/assets/
```

**解决**:
- 文件过大(>500MB) → 使用FFmpeg压缩
- 格式不支持 → 转换为MP4(H.264)
- 磁盘空间不足 → 清理临时文件

### 问题2：素材处理卡住
**症状**: processing_status 一直是 'processing'  
**检查**:
```bash
# 查看后端日志
tail -f backend/logs/app.log  # 如果有日志文件

# 检查FFmpeg进程
ps aux | grep ffmpeg
```

**解决**:
```python
# 重置处理状态
import sqlite3
conn = sqlite3.connect('backend/pervis_director.db')
conn.execute('''
    UPDATE assets 
    SET processing_status='pending', processing_progress=0 
    WHERE processing_status='processing'
''')
conn.commit()
conn.close()

# 重启后端服务以触发重新处理
```

### 问题3：搜索无结果
**症状**: Beat搜索返回空列表  
**检查**:
```bash
# 检查向量数据
sqlite3 backend/pervis_director.db << EOF
SELECT COUNT(*) FROM asset_vectors;
EOF
```

**解决**:
- 向量记录=0 → 素材未完成AI分析
- 向量记录>0但搜索无结果 → 语义差异太大
- 建议：上传更多主题匹配的素材

---

## ✅ 最终检查清单

演示前1小时完成此检查：

### 素材文件检查
- [ ] originals目录有≥3个.mp4文件
- [ ] proxies目录有≥3个代理文件
- [ ] thumbnails目录有≥3个.jpg缩略图
- [ ] audio目录有≥3个.wav音频（如果启用转录）

### 数据库检查
```bash
sqlite3 backend/pervis_director.db << EOF
-- 检查素材记录
SELECT 
    COUNT(*) as total_assets,
    SUM(CASE WHEN processing_status='completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN proxy_path IS NOT NULL THEN 1 ELSE 0 END) as has_proxy
FROM assets;

-- 检查向量数据
SELECT COUNT(*) as total_vectors FROM asset_vectors;

-- 检查Beat记录
SELECT COUNT(*) as total_beats FROM beats;
EOF
```

**期望输出**:
```
total_assets | completed | has_proxy
      3      |     3     |     3

total_vectors
     3+

total_beats
     3
```

### 功能检查
- [ ] 运行 `python sanity_check.py` → PASS
- [ ] 访问 http://localhost:3000 → 正常加载
- [ ] 测试剧本分析 → 返回3个Beat
- [ ] 测试素材搜索 → 返回≥1个结果
- [ ] 测试视频预览 → 正常播放

---

**完成标志**: 上述所有检查项打勾 ✅  
**时间要求**: 从零开始15分钟内完成素材准备  
**质量标准**: 演示脚本可100%走通无阻塞

---

**创建时间**: 2025-12-18  
**审核状态**: 待审核  
**维护者**: 技术团队
