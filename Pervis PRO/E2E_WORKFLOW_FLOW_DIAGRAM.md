# Pervis PRO 完整工作流程图

生成时间: 2025-12-27 01:06:34

## 数据流转和审核机制

```mermaid
flowchart TB
    subgraph Input["📥 用户输入"]
        A[十分钟剧本<br/>约3000字]
    end
    
    subgraph Phase1["🎬 Phase 1: 剧本解析"]
        B[Script_Agent<br/>剧本解析]
        B1[提取场次信息]
        B2[提取角色信息]
        B3[提取对话内容]
        B4[时长估算]
        
        A --> B
        B --> B1
        B --> B2
        B --> B3
        B --> B4
    end
    
    subgraph Phase2["✍️ Phase 2: 内容生成"]
        C1[Script_Agent<br/>生成 Logline]
        C2[Script_Agent<br/>生成 Synopsis]
        C3[Script_Agent<br/>生成人物小传]
        
        B1 --> C1
        B1 --> C2
        B2 --> C3
    end
    
    subgraph Review["🔍 审核机制"]
        D[Director_Agent<br/>内容审核]
        D1{规则校验}
        D2{项目规格检查}
        D3{风格一致性}
        D4{历史版本对比}
        
        C1 --> D
        C2 --> D
        C3 --> D
        D --> D1
        D --> D2
        D --> D3
        D --> D4
    end
    
    subgraph Decision["⚖️ 审核决策"]
        E1[✅ 通过]
        E2[💡 建议修改]
        E3[❌ 拒绝]
        
        D1 --> E1
        D1 --> E2
        D1 --> E3
    end
    
    subgraph Phase3["🎨 Phase 3: 素材召回"]
        F[Storyboard_Agent<br/>素材召回]
        F1[标签搜索]
        F2[向量搜索]
        F3[混合排序]
        F4[Top 5 候选]
        
        E1 --> F
        B1 --> F
        F --> F1
        F --> F2
        F1 --> F3
        F2 --> F3
        F3 --> F4
    end
    
    subgraph Phase4["🎬 Phase 4: 视频输出"]
        G[Storyboard_Agent<br/>粗剪]
        G1[FFmpeg 切割]
        G2[片段拼接]
        G3[输出视频]
        
        F4 --> G
        G --> G1
        G1 --> G2
        G2 --> G3
    end
    
    subgraph Output["📤 最终输出"]
        H[粗剪视频<br/>MP4 格式]
        I[项目文档<br/>场次/角色/小传]
        
        G3 --> H
        E1 --> I
    end
    
    style Input fill:#e1f5fe
    style Phase1 fill:#fff3e0
    style Phase2 fill:#f3e5f5
    style Review fill:#ffebee
    style Decision fill:#fff8e1
    style Phase3 fill:#e8f5e9
    style Phase4 fill:#fce4ec
    style Output fill:#e0f2f1
```

## 详细数据流转

```mermaid
sequenceDiagram
    participant U as 用户
    participant SA as Script_Agent
    participant DA as Director_Agent
    participant SBA as Storyboard_Agent
    participant FF as FFmpeg
    
    U->>SA: 提交剧本 (3000字)
    activate SA
    SA->>SA: 正则解析场次
    SA->>SA: 提取角色对话
    SA->>SA: 估算时长
    SA-->>U: 返回解析结果
    deactivate SA
    
    U->>SA: 请求生成 Logline
    activate SA
    SA->>SA: LLM 生成内容
    SA->>DA: 提交审核
    activate DA
    DA->>DA: 规则校验
    DA->>DA: 字数检查
    DA-->>SA: 审核结果
    deactivate DA
    SA-->>U: Logline + 审核状态
    deactivate SA
    
    U->>SA: 请求生成 Synopsis
    activate SA
    SA->>SA: LLM 生成内容
    SA->>DA: 提交审核
    activate DA
    DA->>DA: 内容审核
    DA-->>SA: 审核结果
    deactivate DA
    SA-->>U: Synopsis + 审核状态
    deactivate SA
    
    U->>SBA: 请求素材召回
    activate SBA
    SBA->>SBA: 标签搜索
    SBA->>SBA: 向量搜索
    SBA->>SBA: 混合排序
    SBA-->>U: Top 5 候选
    deactivate SBA
    
    U->>SBA: 请求粗剪
    activate SBA
    SBA->>FF: 切割片段
    FF-->>SBA: 临时文件
    SBA->>FF: 拼接视频
    FF-->>SBA: 输出文件
    SBA-->>U: 粗剪视频路径
    deactivate SBA
```

## 审核机制详解

```mermaid
flowchart LR
    subgraph Input["输入内容"]
        I1[Logline]
        I2[Synopsis]
        I3[人物小传]
    end
    
    subgraph Rules["规则校验"]
        R1[内容不为空]
        R2[字数范围检查]
        R3[格式正确性]
    end
    
    subgraph Context["上下文检查"]
        C1[项目规格一致性]
        C2[艺术风格一致性]
        C3[历史版本对比]
    end
    
    subgraph Result["审核结果"]
        O1[✅ approved<br/>直接通过]
        O2[💡 suggestions<br/>通过但有建议]
        O3[❌ rejected<br/>需要修改]
    end
    
    I1 --> R1
    I2 --> R1
    I3 --> R1
    
    R1 -->|通过| R2
    R2 -->|通过| R3
    R3 -->|通过| C1
    
    C1 --> C2
    C2 --> C3
    
    C3 -->|全部通过| O1
    C3 -->|有建议| O2
    R1 -->|失败| O3
    R2 -->|失败| O3
```

## 本次测试结果

| 步骤 | Agent | 状态 | 耗时 |
|------|-------|------|------|
| 健康检查 | System | ✅ completed | 2041ms |
| 剧本解析 | Script_Agent | ✅ completed | 8ms |
| 生成 Logline | Script_Agent | ✅ completed | 3ms |
| 生成 Synopsis | Script_Agent | ✅ completed | 1ms |
| 生成人物小传 | Script_Agent | ✅ completed | 5ms |
| 内容审核 | Director_Agent | ✅ completed | 2ms |
| 素材召回 | Storyboard_Agent | ✅ completed | 7860ms |
| 粗剪视频 | Storyboard_Agent | ✅ completed | 0ms |

## 关键数据

- **项目ID**: test_project_20251227_010624
- **剧本长度**: 2076 字符
- **测试时间**: 2025-12-27 01:06:34
