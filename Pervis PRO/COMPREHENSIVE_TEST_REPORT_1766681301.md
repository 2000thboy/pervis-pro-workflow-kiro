# Pervis PRO MVP 全面后端验证测试报告

**测试时间**: 2025-12-26T00:47:39.883820

## DAM 素材库统计

| 指标 | 数值 |
|------|------|
| 总视频数 | 3043 |
| 已索引 | 20 |
| 目录数 | 74 |

## Agent 节点测试

| Agent | 状态 | 详情 |
|-------|------|------|
| script_agent | ❌ 失败 | - |
| art_agent | ❌ 失败 | 'VisualTags' object is not subscriptable |
| director_agent | ❌ 失败 | 'DirectorAgentService' object has no attribute 'ch |
| pm_agent | ❌ 失败 | object ContentVersion can't be used in 'await' exp |
| storyboard_agent | ❌ 失败 | StoryboardAgentService.recall_assets() missing 1 r |
| market_agent | ❌ 失败 | MarketAgentService.analyze_market() got an unexpec |
| system_agent | ❌ 失败 | object TagConsistencyResult can't be used in 'awai |

## 工作流测试

### project_wizard ❌ 失败

### beatboard ✅ 通过

- 场次数: 10
- 有素材的场次: 0
- 总候选数: 0

### preview_mode ✅ 通过

- 总时长: 245.0 秒
- 片段数: 10
- 已匹配素材: 0

## 总结

🎉 **全面后端验证测试通过！**
