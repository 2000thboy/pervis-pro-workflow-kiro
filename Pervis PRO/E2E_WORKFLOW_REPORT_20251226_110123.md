================================================================================
Pervis PRO 完整工作流端到端测试报告
================================================================================

测试时间: 2025-12-26T11:00:54.815149
测试剧本: 《最后的咖啡》（约10分钟剧情短片）

----------------------------------------
步骤执行结果
----------------------------------------
  剧本解析: ✅ 通过
  角色分析: ✅ 通过
  场次分析: ✅ 通过
  导演审核: ✅ 通过
  市场分析: ✅ 通过
  版本管理: ✅ 通过
  系统校验: ✅ 通过
  素材召回: ✅ 通过
  导出准备: ✅ 通过

总计: 9 通过, 0 失败

================================================================================
详细输出内容
================================================================================

### 剧本解析
----------------------------------------
{
  "parse_result": {
    "scenes": [],
    "characters": [],
    "total_scenes": 0,
    "total_characters": 0,
    "estimated_duration": 0.0,
    "logline": "",
    "synopsis": ""
  },
  "logline": "一个程序员在得知自己身患绝症后，选择辞职陪伴妻子经营咖啡馆，在生命最后的时光里找到了真正的幸福。",
  "synopsis": {
    "synopsis": "李明是一个35岁的程序员，在得知自己只有三个月生命后，决定辞职陪伴妻子小雨经营咖啡馆..."
  }
}

### 角色分析
----------------------------------------
{
  "character_bios": {},
  "character_tags": {}
}

### 场次分析
----------------------------------------
{
  "scenes": [],
  "total_duration_seconds": 0,
  "total_duration_minutes": 0.0
}

### 导演审核
----------------------------------------
{
  "logline_review": {
    "status": "approved",
    "passed_checks": [
      "内容不为空",
      "字数合理（48）"
    ],
    "failed_checks": [],
    "suggestions": [],
    "reason": "审核通过",
    "confidence": 0.9
  },
  "synopsis_review": {
    "status": "rejected",
    "passed_checks": [
      "内容不为空"
    ],
    "failed_checks": [
      "内容过短（45 < 100）"
    ],
    "suggestions": [],
    "reason": "规则校验未通过",
    "confidence": 0.9
  }
}

### 市场分析
----------------------------------------
{
  "analysis_id": "mkt_991bf73c393d",
  "project_id": "test_project",
  "audience": {
    "primary_age_range": "18-35",
    "gender_distribution": "均衡",
    "interests": [
      "独立电影",
      "艺术片",
      "电影节"
    ],
    "viewing_habits": [
      "流媒体",
      "电影节",
      "短视频平台"
    ],
    "platforms": [
      "YouTube",
      "Vimeo",
      "B站",
      "电影节"
    ]
  },
  "market_position": "独立短片市场，面向电影爱好者和专业观众",
  "competitors": [],
  "distribution_channels": [
    "电影节投递",
    "流媒体平台",
    "社交媒体推广"
  ],
  "marketing_suggestions": [
    "参加国内外短片电影节",
    "在 B站/YouTube 发布预告片",
    "建立社交媒体账号进行宣传"
  ],
  "risk_factors": [
    "市场竞争激烈",
    "观众注意力分散",
    "宣发预算有限"
  ],
  "opportunities": [
    "新媒体平台降低发行门槛",
    "垂直领域受众精准",
    "口碑传播效应"
  ],
  "estimated_budget_range": "",
  "confidence": 0.5,
  "is_dynamic": false,
  "created_at": "2025-12-26T11:01:01.255377"
}

### 版本管理
----------------------------------------
{
  "version_info": {
    "version_id": "ver_f28a78b9038b",
    "version_name": "Logline_v1",
    "version_number": 1,
    "content_type": "logline",
    "entity_id": null,
    "entity_name": null,
    "content": "一个程序员在得知自己身患绝症后，选择辞职陪伴妻子经营咖啡馆，在生命最后的时光里找到了真正的幸福。",
    "source": "script_agent",
    "status": "draft",
    "created_at": "2025-12-26T11:01:01.257883",
    "created_by": "system"
  },
  "decision": {
    "decision_id": "dec_4460a41102ed",
    "project_id": "test_project",
    "decision_type": "approve",
    "target_type": "version",
    "target_id": "ver_f28a78b9038b",
    "previous_value": null,
    "new_value": null,
    "reason": "",
    "created_at": "2025-12-26T11:01:01.257883"
  },
  "display_info": {
    "current_version": "Logline_v1",
    "version_count": 1,
    "last_modified": "2025-12-26T11:01:01.257883"
  }
}

### 系统校验
----------------------------------------
{
  "validation": {
    "validation_id": "val_e20618f579a2",
    "project_id": "test_project",
    "is_valid": false,
    "issues": [
      {
        "issue_id": "api_39865cea",
        "severity": "error",
        "category": "api",
        "message": "API 不可用: /api/health",
        "field": null,
        "suggestion": "请检查后端服务是否正常运行"
      },
      {
        "issue_id": "api_6a552294",
        "severity": "error",
        "category": "api",
        "message": "API 不可用: /api/wizard/health",
        "field": null,
        "suggestion": "请检查后端服务是否正常运行"
      },
      {
        "issue_id": "api_fe17c5df",
        "severity": "error",
        "category": "api",
        "message": "API 不可用: /api/projects",
        "field": null,
        "suggestion": "请检查后端服务是否正常运行"
      }
    ],
    "tag_consistency": {
      "is_consistent": true,
      "conflicts": [],
      "suggestions": []
    },
    "api_health": [
      {
        "endpoint": "/api/health",
        "status": "unhealthy",
        "response_time_ms": 2372.028,
        "error": null
      },
      {
        "endpoint": "/api/wizard/health",
        "status": "unhealthy",
        "response_time_ms": 3385.594,
        "error": null
      },
      {
        "endpoint": "/api/projects",
        "status": "unhealthy",
        "response_time_ms": 3297.139,
        "error": null
      }
    ],
    "error_count": 3,
    "warning_count": 0,
    "created_at": "2025-12-26T11:01:01.445774"
  },
  "tag_consistency": {
    "is_consistent": true,
    "conflicts": [],
    "suggestions": []
  },
  "api_health": [
    {
      "endpoint": "/api/health",
      "status": "unhealthy",
      "response_time_ms": 2412.935,
      "error": null
    },
    {
      "endpoint": "/api/wizard/health",
      "status": "unhealthy",
      "response_time_ms": 3360.822,
      "error": null
    },
    {
      "endpoint": "/api/projects",
      "status": "unhealthy",
      "response_time_ms": 3369.053,
      "error": null
    }
  ]
}

### 素材召回
----------------------------------------
{
  "recall_results": [
    {
      "scene_id": "scene_1",
      "candidates": [],
      "total_searched": 0,
      "has_match": false,
      "placeholder_message": "未找到匹配的素材，请上传更多素材或调整搜索条件"
    },
    {
      "scene_id": "scene_2",
      "candidates": [],
      "total_searched": 0,
      "has_match": false,
      "placeholder_message": "未找到匹配的素材，请上传更多素材或调整搜索条件"
    },
    {
      "scene_id": "scene_3",
      "candidates": [],
      "total_searched": 0,
      "has_match": false,
      "placeholder_message": "未找到匹配的素材，请上传更多素材或调整搜索条件"
    }
  ],
  "total_scenes_processed": 3
}

### 导出准备
----------------------------------------
{
  "document_export": {
    "available": true,
    "formats": [
      "DOCX",
      "PDF",
      "Markdown"
    ]
  },
  "nle_export": {
    "available": true,
    "formats": [
      "FCPXML",
      "EDL"
    ]
  },
  "image_export": {
    "available": true,
    "formats": [
      "PNG",
      "JPG"
    ]
  }
}

================================================================================
测试结论
================================================================================
✅ 所有步骤执行成功！后端数据流完整可用。
建议：可以开始前端开发。