# Production模块设计

## 核心功能
把"自由生成的内容"变成"合格零件"

## 输入接口
```typescript
interface SceneBrief {
  id: string;           // CH01_INTRO_VILLAGE
  type: SceneType;      // INTRO | INVEST | CHOICE | ENDING  
  description: string;  // 场景描述
  duration: number;     // 预期时长（分钟）
  variables?: string[]; // 涉及的变量
}
```

## 处理流程
1. **规范检查**：验证命名、类型、变量合法性
2. **内容生成**：调用AI生成符合规范的内容
3. **结构化输出**：生成标准JSON格式

## 输出格式
```typescript
interface SceneOutput {
  id: string;
  type: SceneType;
  content: {
    narrative: string[];    // 旁白文本数组
    dialogue: Dialogue[];   // 对话数组
    choices?: Choice[];     // 选择项（如有）
    variables: Variable[];  // 变量操作
  };
  assets: {
    background: string;     // 背景图占位符
    characters: string[];   // 角色立绘占位符
    music?: string;         // 音乐占位符
  };
  validation: {
    isValid: boolean;
    errors: string[];
  };
}
```

## KIRO实现要点
- 使用Spec驱动开发
- 内置规范校验器
- 自动拒绝不合规生成
- 支持批量处理