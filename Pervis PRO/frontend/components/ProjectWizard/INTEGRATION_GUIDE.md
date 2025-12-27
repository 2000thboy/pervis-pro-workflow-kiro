# ProjectWizard 集成指南

## 已创建的文件

```
Pervis PRO/frontend/components/ProjectWizard/
├── index.tsx              # 主向导组件
├── types.ts               # 类型定义
├── api.ts                 # Wizard API 客户端
├── WizardContext.tsx      # 状态管理上下文
├── WizardStep1_BasicInfo.tsx   # 步骤1: 基本信息
├── WizardStep2_Script.tsx      # 步骤2: 剧本导入
├── WizardStep3_Characters.tsx  # 步骤3: 角色设定
├── WizardStep4_Scenes.tsx      # 步骤4: 场次规划
├── WizardStep5_References.tsx  # 步骤5: 参考资料
├── WizardStep6_Confirm.tsx     # 步骤6: 确认提交
├── AgentStatusPanel.tsx        # Agent 状态面板
└── exports.ts                  # 导出文件
```

## 集成到 App.tsx

在 `Pervis PRO/frontend/App.tsx` 中添加以下修改：

### 1. 添加导入

```tsx
// 在文件顶部添加
import { ProjectWizard } from './components/ProjectWizard';
```

### 2. 添加状态

```tsx
// 在 UI Modal States 部分添加
const [showWizard, setShowWizard] = useState(false);
```

### 3. 修改 LandingPage 的 onStart

```tsx
// 将 onStart={() => setShowIngestion(true)} 改为
onStart={() => setShowWizard(true)}
```

### 4. 添加 ProjectWizard 组件

```tsx
// 在 showIngestion 条件渲染后添加
{showWizard && (
    <ProjectWizard
        onClose={() => setShowWizard(false)}
        onComplete={(projectId) => {
            setShowWizard(false);
            // 可选：加载新创建的项目
            refreshProjects();
        }}
    />
)}
```

## 使用方式

1. 用户点击首页的"新建项目"按钮
2. 打开 ProjectWizard 向导
3. 按步骤填写项目信息
4. AI Agent 自动解析剧本、分类素材
5. 确认后创建项目

## API 端点

向导组件调用以下后端 API：

- `POST /api/wizard/parse-script` - 剧本解析
- `POST /api/wizard/generate-content` - 内容生成
- `POST /api/wizard/process-assets` - 素材处理
- `POST /api/wizard/create-project` - 创建项目
- `POST /api/wizard/validate-project` - 验证项目
- `POST /api/wizard/review-content` - 内容审核
- `GET /api/wizard/task-status/{id}` - 任务状态

## 功能特性

- ✅ 6 步向导流程
- ✅ AI 剧本解析 (Script_Agent)
- ✅ AI 素材分类 (Art_Agent)
- ✅ AI 内容审核 (Director_Agent)
- ✅ 实时 Agent 状态显示
- ✅ 项目完成度计算
- ✅ 验证错误提示
- ✅ 步骤间自由跳转
