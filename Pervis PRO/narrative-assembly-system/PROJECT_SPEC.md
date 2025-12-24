# 叙事装配系统 - 项目规范

## 核心定位
这不是游戏引擎，而是一个"叙事装配编译器"，专门解决：
- AI生成内容的规范化
- 多工具切换的混乱问题  
- 文字游戏的工业化生产

## 硬约束规则

### 时间轴单位
- 1 Scene = 5-8分钟阅读时长
- 1 Chapter = 3-5个Scene
- MVP目标 = 8-12个Scene（总计60-90分钟）

### Scene类型（仅限这4种）
```
INTRO     - 开场/背景介绍
INVEST    - 调查/线索收集  
CHOICE    - 关键选择/分支
ENDING    - 结局场景
```

### 命名规范（强制）
```
Scene:     CH{XX}_{TYPE}_{NAME}
           例：CH01_INTRO_VILLAGE, CH03_INVEST_CRIME_SCENE

Variable:  {type}_{name}
           例：has_clue_main, is_suspect_trusted

Asset:     {type}_{scene}_{desc}
           例：bg_village_night, char_detective_thinking
```

### 变量白名单（仅限这些类型）
```
has_{name}     - 布尔型线索
is_{name}      - 布尔型状态  
trust_{name}   - 0-100信任度
time_{name}    - 时间相关
```

## 禁止规则
- 禁止自创Scene类型
- 禁止使用未定义变量
- 禁止跨Chapter直接跳转
- 禁止超过10个并行变量

## 成功标准
- KIRO能自动拒绝违规生成
- 任何Scene都能独立验证
- 整个项目能一键导出到Ren'Py