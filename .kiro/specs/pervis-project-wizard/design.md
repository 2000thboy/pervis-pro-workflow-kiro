# Design Document: Pervis PRO 项目立项向导系统

## Overview

本设计文档描述 Pervis PRO 项目立项向导系统的架构设计。系统采用 MVP 简化方案，将 Agent 功能直接集成到 Pervis PRO 后端，保留 Agent 概念和状态显示。

**核心目标**：
1. 引导用户完成项目建档
2. 自动解析剧本并提取项目信息
3. 使用 Agent 生成缺失内容（Script_Agent、Art_Agent）
4. Director_Agent 审核所有 Agent 输出
5. 处理素材并生成标签，为 Beatboard 阶段准备数据

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                             │
├─────────────────────────────────────────────────────────────────────┤
│  ProjectWizard.tsx                                                   │
│  ├── WizardStep1_BasicInfo.tsx    (基本信息)                        │
│  ├── WizardStep2_Script.tsx       (剧本导入)                        │
│  ├── WizardStep3_Characters.tsx   (角色设定)                        │
│  ├── WizardStep4_Scenes.tsx       (场次规划)                        │
│  ├── WizardStep5_References.tsx   (参考资料)                        │
│  └── WizardStep6_Confirm.tsx      (确认提交)                        │
│                                                                      │
│  Components:                                                         │
│  ├── MissingContentDialog.tsx     (缺失内容处理对话框)              │
│  ├── AgentStatusPanel.tsx         (Agent 状态面板)                  │
│  └── ProjectPreview.tsx           (项目预览)                        │
└─────────────────────────────────────────────────────────────────────┘
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────┤
│  /api/wizard/                                                        │
│  ├── POST /parse-script         - Script_Agent 解析剧本             │
│  ├── POST /generate-content     - Agent 生成内容                    │
│  ├── POST /process-assets       - Art_Agent 处理素材                │
│  ├── POST /create-project       - 创建项目                          │
│  ├── GET  /templates            - 获取模板列表                      │
│  └── GET  /task-status/{id}     - 获取 Agent 任务状态               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AgentService Layer                              │
├─────────────────────────────────────────────────────────────────────┤
│  AgentService                                                        │
│  ├── Script_Agent (编剧)                                            │
│  │   ├── parse_script()         - 剧本解析                          │
│  │   ├── generate_logline()     - Logline 生成                      │
│  │   ├── generate_synopsis()    - Synopsis 生成                     │
│  │   ├── generate_bio()         - 人物小传生成                      │
│  │   └── estimate_duration()    - 时长估算                          │
│  │                                                                   │
│  ├── Art_Agent (美术)                                               │
│  │   ├── classify_file()        - 文件分类                          │
│  │   ├── extract_metadata()     - 元数据提取                        │
│  │   ├── generate_tags()        - 标签生成                          │
│  │   └── create_thumbnail()     - 缩略图生成                        │
│  │                                                                   │
│  ├── Director_Agent (导演) - 有项目记忆                             │
│  │   ├── review_output()        - 审核其他 Agent 输出               │
│  │   ├── check_consistency()    - 检查与项目规格一致性              │
│  │   └── compare_versions()     - 对比历史版本                      │
│  │                                                                   │
│  └── PM_Agent (项目管理) - 隐藏，后台运行                           │
│      ├── get_project_context()  - 获取项目上下文                    │
│      ├── record_version()       - 记录版本                          │
│      └── record_decision()      - 记录用户决策                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Project Context (项目上下文)                    │
├─────────────────────────────────────────────────────────────────────┤
│  PM_Agent 管理的数据：                                               │
│  ├── 项目规格 (时长、画幅、帧率、分辨率)                            │
│  ├── 艺术风格 (已确定的视觉风格、对标项目)                          │
│  ├── 版本历史 (每次 Agent 生成的内容版本)                           │
│  └── 用户决策 (接受/拒绝/修改的历史)                                │
└─────────────────────────────────────────────────────────────────────┘
```

## Director_Agent 审核机制

### 审核流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Director_Agent 审核流程                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Script_Agent/Art_Agent 生成内容                                    │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 1: 规则校验                                            │   │
│  │  ├── 内容不为空                                              │   │
│  │  ├── 字数在合理范围内                                        │   │
│  │  └── 格式正确                                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 2: 项目规格一致性检查 (从 PM_Agent 获取上下文)         │   │
│  │  ├── 时长是否符合项目设定                                    │   │
│  │  ├── 画幅是否符合项目设定                                    │   │
│  │  └── 帧率是否符合项目设定                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 3: 艺术风格一致性检查                                  │   │
│  │  ├── 是否符合已确定的视觉风格                                │   │
│  │  └── 是否符合对标项目的调性                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 4: 历史版本对比 (从 PM_Agent 获取历史)                 │   │
│  │  ├── 是否与之前被否决的版本相似                              │   │
│  │  ├── 是否与用户已确认的内容矛盾                              │   │
│  │  └── 避免"改回第一版"的问题                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 5: 返回审核结果                                        │   │
│  │  ├── 审核通过 → 返回结果给用户                               │   │
│  │  └── 审核建议 → 返回结果 + 改进建议                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Director_Agent 实现

```python
class DirectorAgent:
    """导演 Agent - 有项目记忆，审核其他 Agent 的输出"""
    
    def __init__(self, llm_provider: LLMProvider, pm_agent: PMAgent):
        self.llm = llm_provider
        self.pm_agent = pm_agent
    
    async def review(self, result: Any, task_type: str, project_id: str) -> ReviewResult:
        """审核 Agent 输出结果"""
        
        # 1. 获取项目上下文
        context = await self.pm_agent.get_project_context(project_id)
        
        # 2. 规则校验
        rule_check = self._check_rules(result, task_type)
        if not rule_check.passed:
            return ReviewResult(
                status="rejected",
                reason=rule_check.reason,
                suggestions=rule_check.suggestions
            )
        
        # 3. 项目规格一致性检查
        spec_check = self._check_project_specs(result, context.specs)
        
        # 4. 艺术风格一致性检查
        style_check = await self._check_style_consistency(result, context.style)
        
        # 5. 历史版本对比
        history_check = await self._compare_with_history(
            result, 
            context.version_history,
            context.user_decisions
        )
        
        # 6. 综合评估
        if spec_check.passed and style_check.passed and history_check.passed:
            return ReviewResult(
                status="approved",
                message="审核通过"
            )
        else:
            return ReviewResult(
                status="suggestions",
                message="审核通过，但有改进建议",
                suggestions=self._merge_suggestions(spec_check, style_check, history_check)
            )
    
    def _check_rules(self, result: Any, task_type: str) -> RuleCheckResult:
        """规则校验"""
        # 内容不为空
        # 字数在合理范围内
        # 格式正确
        pass
    
    def _check_project_specs(self, result: Any, specs: ProjectSpecs) -> CheckResult:
        """检查项目规格一致性"""
        # 时长、画幅、帧率是否符合项目设定
        pass
    
    async def _check_style_consistency(self, result: Any, style: StyleContext) -> CheckResult:
        """检查艺术风格一致性（使用 LLM）"""
        prompt = f"""
        请检查以下内容是否符合项目的艺术风格：
        
        项目风格：{style.description}
        对标项目：{style.reference_projects}
        
        待检查内容：{result}
        
        请评估一致性并给出建议。
        """
        pass
    
    async def _compare_with_history(
        self, 
        result: Any, 
        history: List[VersionRecord],
        decisions: List[UserDecision]
    ) -> CheckResult:
        """对比历史版本，避免改回被否决的版本"""
        # 检查是否与之前被否决的版本相似
        # 检查是否与用户已确认的内容矛盾
        pass
```

### PM_Agent 实现（隐藏）

```python
class PMAgent:
    """项目管理 Agent - 隐藏，后台运行"""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def get_project_context(self, project_id: str) -> ProjectContext:
        """获取项目上下文"""
        return ProjectContext(
            specs=await self._get_project_specs(project_id),
            style=await self._get_style_context(project_id),
            version_history=await self._get_version_history(project_id),
            user_decisions=await self._get_user_decisions(project_id)
        )
    
    async def record_version(
        self, 
        project_id: str, 
        content_type: str, 
        content: Any,
        agent: str
    ):
        """记录版本"""
        await self.db.insert("content_versions", {
            "project_id": project_id,
            "content_type": content_type,
            "content": content,
            "agent": agent,
            "created_at": datetime.now()
        })
    
    async def record_decision(
        self, 
        project_id: str, 
        version_id: str, 
        decision: str,  # accepted, rejected, modified
        user_feedback: str = None
    ):
        """记录用户决策"""
        await self.db.insert("user_decisions", {
            "project_id": project_id,
            "version_id": version_id,
            "decision": decision,
            "feedback": user_feedback,
            "created_at": datetime.now()
        })


@dataclass
class ProjectContext:
    """项目上下文"""
    specs: ProjectSpecs          # 项目规格
    style: StyleContext          # 艺术风格
    version_history: List[VersionRecord]  # 版本历史
    user_decisions: List[UserDecision]    # 用户决策


@dataclass
class ProjectSpecs:
    """项目规格"""
    duration: int       # 时长（秒）
    aspect_ratio: str   # 画幅（如 16:9）
    frame_rate: int     # 帧率
    resolution: str     # 分辨率（如 1920x1080）


@dataclass
class StyleContext:
    """艺术风格上下文"""
    description: str              # 风格描述
    reference_projects: List[str] # 对标项目
    color_palette: List[str]      # 色彩倾向
    mood: str                     # 情绪基调
```


## Components and Interfaces

### 1. 前端组件

#### 1.1 ProjectWizard 主组件

```typescript
interface ProjectWizardProps {
  templateId?: string;  // 可选的模板 ID
  onComplete: (projectId: string) => void;
}

interface WizardState {
  currentStep: number;
  projectData: ProjectData;
  agentTasks: AgentTask[];
  completionPercentage: number;
}

interface ProjectData {
  // 基本信息
  title: string;
  type: 'short_film' | 'ad' | 'mv' | 'feature';
  duration: number;
  aspectRatio: string;
  frameRate: number;
  
  // 剧本相关
  logline: string;
  synopsis: string;
  script: string;
  
  // 角色
  characters: Character[];
  
  // 场次
  scenes: Scene[];
  
  // 参考资料
  references: Reference[];
  
  // 制作信息
  budget?: string;
  timeline?: string;
  teamSize?: number;
  
  // 元数据
  fieldStatus: Record<string, FieldStatus>;
}

type FieldStatus = 'empty' | 'user_input' | 'script_agent' | 'art_agent' | 'placeholder' | 'processing';

interface AgentTask {
  id: string;
  agentType: 'script_agent' | 'art_agent' | 'director_agent';
  taskType: 'parse_script' | 'generate_logline' | 'generate_synopsis' | 
            'generate_bio' | 'estimate_duration' | 'analyze_style' | 'review';
  status: 'pending' | 'working' | 'reviewing' | 'completed' | 'failed';
  progress: number;
  result?: any;
  error?: string;
}
```

#### 1.2 AgentStatusPanel 组件

```typescript
interface AgentStatusPanelProps {
  tasks: AgentTask[];
  onRetry: (taskId: string) => void;
}

// 显示示例：
// ┌─────────────────────────────────────┐
// │  🖊️ 编剧 Agent 正在工作...          │
// │  ████████░░░░░░░░░░░░ 40%           │
// │                                      │
// │  → 下一步：导演 Agent 审核          │
// └─────────────────────────────────────┘
```

#### 1.3 MissingContentDialog 组件

```typescript
interface MissingContentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  missingFields: MissingField[];
  onAction: (fieldId: string, action: ContentAction) => void;
  onBatchAction: (action: ContentAction) => void;
}

interface MissingField {
  id: string;
  name: string;
  description: string;
  responsibleAgent: 'script_agent' | 'art_agent';  // 负责生成的 Agent
}

type ContentAction = 'placeholder' | 'agent_generate' | 'manual_input';
```

### 2. 后端 API 接口

#### 2.1 剧本解析 API

```python
# POST /api/wizard/parse-script
class ParseScriptRequest(BaseModel):
    content: str  # 剧本文本内容
    format: str = "txt"  # txt, pdf, docx, fdx

class ParseScriptResponse(BaseModel):
    task_id: str
    status: str
    agent: str = "script_agent"

# 任务状态响应
class AgentTaskStatus(BaseModel):
    task_id: str
    agent_type: str  # script_agent, art_agent, director_agent
    task_type: str
    status: str  # pending, working, reviewing, completed, failed
    progress: int
    current_step: str  # "编剧 Agent 正在工作...", "导演 Agent 审核中..."
    result: Optional[Dict] = None
    error: Optional[str] = None
```

#### 2.2 Agent 内容生成 API

```python
# POST /api/wizard/generate-content
class GenerateContentRequest(BaseModel):
    type: str  # logline, synopsis, bio, duration, style
    context: Dict[str, Any]  # 上下文信息
    
class GenerateContentResponse(BaseModel):
    task_id: str
    status: str
    agent: str  # 负责的 Agent

# Agent 工作流程：
# 1. Script_Agent/Art_Agent 执行任务
# 2. Director_Agent 审核
# 3. 返回结果
```

#### 2.3 素材处理 API

```python
# POST /api/wizard/process-assets
class ProcessAssetsRequest(BaseModel):
    asset_ids: List[str]
    
class ProcessAssetsResponse(BaseModel):
    task_id: str
    status: str
    agent: str = "art_agent"
```

### 3. AgentService 服务层

```python
class AgentService:
    """Agent 服务层 - 管理 Agent 工作流程"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.script_agent = ScriptAgent(llm_provider)
        self.art_agent = ArtAgent(llm_provider)
        self.director_agent = DirectorAgent(llm_provider)
    
    async def execute_task(self, task_type: str, context: Dict) -> AgentTaskResult:
        """执行 Agent 任务，包含审核流程"""
        
        # 1. 确定负责的 Agent
        if task_type in ['parse_script', 'generate_logline', 'generate_synopsis', 
                         'generate_bio', 'estimate_duration']:
            agent = self.script_agent
            agent_name = "script_agent"
        else:
            agent = self.art_agent
            agent_name = "art_agent"
        
        # 2. 更新状态：Agent 工作中
        await self.update_status(task_id, agent_name, "working", 
                                 "编剧 Agent 正在工作..." if agent_name == "script_agent" 
                                 else "美术 Agent 正在工作...")
        
        # 3. 执行任务
        result = await agent.execute(task_type, context)
        
        # 4. 更新状态：导演 Agent 审核中
        await self.update_status(task_id, "director_agent", "reviewing", 
                                 "导演 Agent 审核中...")
        
        # 5. 导演 Agent 审核
        review_result = await self.director_agent.review(result, task_type)
        
        # 6. 返回结果
        return AgentTaskResult(
            agent=agent_name,
            result=result,
            review=review_result,
            status="completed"
        )


class ScriptAgent:
    """编剧 Agent"""
    
    async def parse_script(self, content: str, format: str) -> ScriptParseResult:
        """解析剧本，提取场次和角色信息"""
        pass
    
    async def generate_logline(self, script: str) -> str:
        """生成 Logline"""
        pass
    
    async def generate_synopsis(self, script: str) -> str:
        """生成故事概要"""
        pass
    
    async def generate_character_bio(self, character_name: str, script: str) -> str:
        """生成人物小传"""
        pass
    
    async def estimate_scene_duration(self, scene_content: str) -> int:
        """估算场次时长"""
        pass


class ArtAgent:
    """美术 Agent"""
    
    async def classify_file(self, file_path: str) -> str:
        """识别文件类型"""
        pass
    
    async def extract_metadata(self, file_path: str) -> Dict:
        """提取文件元数据"""
        pass
    
    async def generate_tags(self, file_path: str) -> List[str]:
        """生成描述标签"""
        pass
    
    async def create_thumbnail(self, file_path: str) -> str:
        """生成缩略图"""
        pass


class DirectorAgent:
    """导演 Agent - 审核其他 Agent 的输出"""
    
    async def review(self, result: Any, task_type: str) -> ReviewResult:
        """审核 Agent 输出结果"""
        # 使用 LLM 评估结果质量
        # 返回审核意见和建议
        pass
```


## 数据流程

### 项目建档完整流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      项目建档流程                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Step 1: 基本信息                                                   │
│  └── 用户填写: 标题、类型、时长、画幅、帧率                         │
│                                                                      │
│  Step 2: 剧本导入                                                   │
│  ├── 用户上传剧本文件                                               │
│  ├── AIService.parse_script() 解析                                  │
│  │   ├── 提取场次信息                                               │
│  │   ├── 提取角色名称                                               │
│  │   └── 生成结构分析                                               │
│  └── 自动填充 scenes 和 characters                                  │
│                                                                      │
│  Step 3: 角色设定                                                   │
│  ├── 显示解析出的角色列表                                           │
│  ├── 用户可编辑角色信息                                             │
│  └── AIService.generate_character_bio() 生成人物小传                │
│                                                                      │
│  Step 4: 场次规划                                                   │
│  ├── 显示解析出的场次列表                                           │
│  ├── 用户可编辑场次信息                                             │
│  └── AIService.estimate_scene_duration() 估算时长                   │
│                                                                      │
│  Step 5: 参考资料                                                   │
│  ├── 用户上传参考图片/视频                                          │
│  ├── AssetProcessor.classify_file() 分类                            │
│  ├── AssetProcessor.extract_metadata() 提取元数据                   │
│  ├── AssetProcessor.generate_tags() 生成标签                        │
│  └── 存储到素材库，为 Beatboard 准备                                │
│                                                                      │
│  Step 6: 确认提交                                                   │
│  ├── 检查缺失字段                                                   │
│  ├── 弹出 MissingContentDialog（如有缺失）                          │
│  ├── 用户选择处理方式                                               │
│  ├── 验证项目信息                                                   │
│  └── 创建项目，跳转到 Analysis 阶段                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 素材处理与 Beatboard 集成流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                 素材处理与 Beatboard 集成                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 立项阶段 - 素材上传                                             │
│     ├── 用户上传参考图片/视频                                       │
│     ├── AssetProcessor 处理:                                        │
│     │   ├── 生成缩略图 (thumbnail)                                  │
│     │   ├── 生成代理文件 (proxy)                                    │
│     │   ├── 提取元数据 (分辨率、时长、颜色)                         │
│     │   └── AI 生成标签 (内容、风格、技术)                          │
│     └── 存储到素材库 (assets 表)                                    │
│                                                                      │
│  2. 立项完成 - 数据打包                                             │
│     └── 项目信息打包:                                               │
│         ├── 角色列表 + 人物小传                                     │
│         ├── 场次列表 + 时长估算                                     │
│         ├── 风格参考标签                                            │
│         └── 视觉参考标签                                            │
│                                                                      │
│  3. Beatboard 阶段 - 素材召回                                       │
│     ├── 基于场次描述生成搜索词条                                    │
│     ├── 基于角色信息生成搜索词条                                    │
│     ├── 基于风格标签进行相似度匹配                                  │
│     └── 从素材库召回匹配的参考素材                                  │
│                                                                      │
│  4. Beatboard 阶段 - 素材装配                                       │
│     ├── 将召回的素材推荐给用户                                      │
│     ├── 用户选择/替换素材                                           │
│     └── 装配到故事板中                                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Models

### ProjectWizardDraft 表（草稿）

```python
class ProjectWizardDraft(Base):
    """项目建档草稿 - 保存用户进度"""
    __tablename__ = "project_wizard_drafts"
    
    id = Column(String, primary_key=True)
    user_id = Column(String)
    
    # 进度
    current_step = Column(Integer, default=1)
    completion_percentage = Column(Float, default=0)
    
    # 项目数据 (JSON)
    project_data = Column(JSON)
    
    # 字段状态 (JSON)
    field_status = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### ProjectTemplate 表

```python
class ProjectTemplate(Base):
    """项目模板"""
    __tablename__ = "project_templates"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    type = Column(String)  # short_film, ad, mv, feature, custom
    description = Column(String)
    
    # 模板数据 (JSON)
    template_data = Column(JSON)
    
    # 是否系统预设
    is_system = Column(Boolean, default=False)
    
    # 用户自定义模板
    user_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### AITask 表

```python
class AITask(Base):
    """AI 任务记录"""
    __tablename__ = "ai_tasks"
    
    id = Column(String, primary_key=True)
    type = Column(String)  # parse_script, generate_logline, etc.
    status = Column(String)  # pending, processing, completed, failed
    
    # 输入参数 (JSON)
    input_params = Column(JSON)
    
    # 输出结果 (JSON)
    result = Column(JSON, nullable=True)
    
    # 错误信息
    error_message = Column(String, nullable=True)
    
    # 进度 (0-100)
    progress = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
```

## Error Handling

### 错误类型

1. **文件解析错误**
   - 不支持的文件格式
   - 文件损坏或无法读取
   - 剧本格式无法识别

2. **AI 生成错误**
   - LLM 服务不可用
   - 生成超时
   - 内容不符合预期

3. **素材处理错误**
   - 文件过大
   - 格式不支持
   - 元数据提取失败

### 错误处理策略

```python
class WizardError(Exception):
    def __init__(self, code: str, message: str, recoverable: bool = True):
        self.code = code
        self.message = message
        self.recoverable = recoverable

ERROR_CODES = {
    "SCRIPT_PARSE_FAILED": "剧本解析失败",
    "AI_SERVICE_UNAVAILABLE": "AI 服务不可用",
    "AI_GENERATION_TIMEOUT": "AI 生成超时",
    "ASSET_TOO_LARGE": "文件过大",
    "UNSUPPORTED_FORMAT": "不支持的格式",
}
```

## MVP 与后续迁移

### MVP 阶段（当前）

- AIService 直接集成到 Pervis PRO 后端
- 使用 REST API + 轮询获取任务状态
- 简化的素材处理流程

### 后续迁移路径

1. **独立 Agent 服务**
   - 将 AIService 迁移到独立服务
   - 添加 WebSocket 实时通信
   - 支持更复杂的 Agent 协作

2. **集成 multi-agent-workflow**
   - 复用现有的 Agent 架构
   - 添加 REST API 网关
   - 实现 Agent 间协作流程
