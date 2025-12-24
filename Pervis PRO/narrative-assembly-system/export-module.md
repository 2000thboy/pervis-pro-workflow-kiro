# Ren'Py导出模块

## 导出目标
从Assembly的时间轴结构，生成标准Ren'Py项目

## 输出结构
```
exported_game/
├── game/
│   ├── script.rpy           # 主脚本
│   ├── scripts/
│   │   ├── ch01_intro.rpy   # 分章节脚本
│   │   ├── ch02_invest.rpy
│   │   └── ...
│   ├── images/
│   │   ├── bg/              # 背景图占位符
│   │   ├── characters/      # 角色立绘占位符
│   │   └── ui/              # UI素材占位符
│   ├── audio/
│   │   ├── music/           # 音乐占位符
│   │   └── sfx/             # 音效占位符
│   └── options.rpy          # 游戏配置
└── README.md                # 装配说明
```

## 代码生成规则

### 主脚本模板
```renpy
# 自动生成的主脚本
define detective = Character("侦探", color="#c8ffc8")
define villager = Character("村民", color="#ffc8c8")

# 变量初始化
default has_clue_main = False
default is_suspect_trusted = False
default trust_villager = 50

# 开始游戏
label start:
    jump ch01_intro_village
```

### 章节脚本模板
```renpy
# CH01_INTRO_VILLAGE
label ch01_intro_village:
    scene bg_village_night
    show detective thinking
    
    "雨夜，荒村。"
    "你站在破败的村口，远处传来诡异的声音。"
    
    detective "这个村子...有些不对劲。"
    
    jump ch02_invest_crime_scene
```

## 验证机制
- 语法检查：确保生成的.rpy文件无语法错误
- 跳转验证：所有jump目标都存在
- 变量检查：所有使用的变量都已定义
- 资产检查：生成占位符文件，避免缺失报错

## 完成标准
- Ren'Py启动器能正常加载项目
- 游戏能从头到尾通关
- 所有分支路径都可达
- 变量逻辑正确执行