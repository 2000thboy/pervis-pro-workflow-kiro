import React, { useState, useEffect } from 'react';
import { analyzeScriptToStructure, generateStructureFromSynopsis, smartBuildScript } from './services/geminiService';
import { Beat, ProjectSpecs, Character } from './types';
import {
    Sparkles,
    ArrowRight,
    FileText,
    Upload,
    PenTool,
    Zap,
    Loader2,
    AlertCircle,
    X,
    Shuffle,
    Timer,
    Settings,
    Monitor,
    Film,
    RefreshCw
} from 'lucide-react';

interface ScriptIngestionProps {
    onProcessComplete: (beats: Beat[], scriptRaw: string, meta: { title: string, logline?: string, synopsis?: string }, specs: ProjectSpecs, characters: Character[]) => void;
    onClose?: () => void;
}

type TabMode = 'creation' | 'import';
type BuildMode = 'manual' | 'ai_build' | 'parse' | 'smart_build';
type DurationUnit = 's' | 'm';

// --- Demo Data (Restored for MVP Testing) ---

const TRAILER_SCRIPT = `Title: 疾速追杀：代号S (Trailer)
Genre: Action / Cyberpunk

SCENE 1
内景. 拉面店 - 夜
霓虹灯透过满是雨水的玻璃窗，在蒸汽腾腾的店内投下红蓝交错的光影。
S (30岁，黑色西装，眼神疲惫) 独自坐在吧台角落，面前是一碗未动的拉面。
他缓缓放下筷子。左手微微颤抖，但他迅速按住。
周围的食客（西装暴徒）突然停止了进食，手伸向怀里。

S
(低语)
哪怕一顿饭的时间都不给吗？

SCENE 2
内景. 拉面店 - 连续
暴徒A猛地拔枪。
S 抓起面前滚烫的拉面碗，反手泼在暴徒A脸上。
暴徒A惨叫。
S 顺势将筷子刺入暴徒B的手背，将其钉在桌上。
枪声大作。S 翻身躲入吧台内，酒瓶在头顶炸裂。

SCENE 3
外景. 后巷 - 夜
S 撞开后门，跌跌撞撞冲入雨中。
他捂着侧腹，鲜血渗出指缝。
一辆重型黑色机车停在垃圾箱旁。
S 跨上机车，引擎轰鸣声撕裂雨夜。

SCENE 4
外景. 涩谷街头 - 夜
机车在车流中以此字形穿梭。
后视镜中，三辆黑色 SUV 紧追不舍。
SUV 天窗打开，机枪手向 S 扫射。
路人尖叫四散。

SCENE 5
外景. 高架桥 - 夜
S 猛拧油门，机车前轮抬起，飞跃过一辆侧翻的轿车。
一架武装无人机从大楼后升起，红外激光锁定 S 的背影。
S 拔出腰间的手枪，在高速行驶中回头。
砰！砰！
无人机旋翼冒烟，旋转着坠毁在后方的 SUV 上。
爆炸火光照亮了 S 冷峻的脸。

SCENE 6
外景. 避难所入口（废弃教堂） - 暴雨
S 驾驶机车滑行甩尾，停在教堂巨大的木门前。
他力竭倒地，雨水冲刷着地上的血迹。
门缓缓打开。
一个高大的身影（王牌特工 ZERO）撑着黑伞走出。

ZERO
你迟到了，S。

S 艰难地抬起头，举起满是鲜血的手，手里紧攥着那枚存有情报的芯片。

S
只要还没死，就不算迟。

ZERO 扔掉雨伞，拔出长刀。

ZERO
那就让你死透一点。

两人在暴雨中对冲。
刀光与雷电同时闪过。

黑屏。
字幕：疾速追杀：代号 S - 2025.
`;

const LONG_FORM_SCRIPT = `Title: The Memory Architect
Genre: Sci-Fi / Drama

SCENE 1
INT. MEMORY LAB - DAY
White, sterile room. The hum of servers.
LEVI (35, tired eyes) adjusts a neural interface on ANNA (30, comatose).
ASSISTANT ZHANG watches a monitor.

ZHANG
Levels are stable. Ready for injection.

LEVI
Let's go deep this time. Layer 11.

Levi puts on his own headset.
Darkness.

SCENE 2
EXT. UNIVERSITY CAMPUS - DAWN (DREAM)
Golden hour. But something is wrong. The sun is flickering.
Levi walks across the empty quad.
Leaves hang suspended in mid-air.

LEVI
System check. Gravity normal. Atmosphere... decaying.

He spots ANNA sitting on a bench, reading.
She looks younger, happier.

SCENE 3
EXT. CAMPUS BENCH - CONTINUOUS
Levi approaches.

LEVI
Anna.

She looks up. Her eyes are pitch black.

ANNA
You shouldn't be here, Levi. The architecture is unstable.

LEVI
I'm bringing you back.

ANNA
Back to what? The machine? The tube?

The ground shakes. A crack forms in the sky, revealing binary code.

SCENE 4
INT. APARTMENT - NIGHT (FLASHBACK)
Rain hits the window.
Levi and the Real Anna are arguing.

REAL ANNA
You spend more time in the simulation than with me!

LEVI
I'm building our future!

REAL ANNA
You're building a cage.

She grabs her keys and leaves.
The sound of screeching tires. Crash.

SCENE 5
EXT. UNIVERSITY CAMPUS - DAWN (DREAM)
The dream is collapsing. Buildings fold onto themselves like Inception.
Levi grabs Dream Anna's hand.

LEVI
It wasn't my fault.

ANNA
(Voice distorting)
Then why are you trying to fix it?

SCENE 6
INT. MEMORY LAB - DAY
Alarms blaring.
Zhang is shaking Levi.

ZHANG
Wake up! His heart rate is spiking!

SCENE 7
INT. SUBWAY STATION - NIGHT (DREAM LAYER 12)
Levi wakes up on a cold platform.
The sign reads: "TERMINAL - NO RETURN".
He stands up. The tunnel is endless darkness.

A TRAIN approaches silently. No wheels, floating on magnets.
The doors open.
Inside is every memory Levi ever deleted.

SCENE 8
INT. TRAIN CAR - CONTINUOUS
Levi walks through the car.
He sees a birthday party. A wedding. The funeral.
He sees himself at the funeral, not crying. Working on a tablet.

LEVI
I was working... I was trying to save her mind data.

SCENE 9
INT. MEMORY LAB - DAY
Zhang prepares a syringe.

ZHANG
Emergency extraction protocol.

SCENE 10
EXT. VOID - TIMELESS
Levi falls through white space.
He lands in their old bedroom.
Anna is there, packing a suitcase.

LEVI
Don't go.

ANNA
I already left, Levi. Three years ago.
You're the one who needs to wake up.

Levi looks at his hands. They are turning into pixels.

LEVI
I'm the simulation?

ANNA
Goodbye, Architect.

She kisses his forehead. He shatters into light.

SCENE 11
INT. MEMORY LAB - DAY
Levi gasps, ripping the headset off.
Silence.
He looks at Anna's body in the pod.
She is still.

ZHANG
Welcome back. Did you find her?

Levi walks to the window. The city outside flickers for a second.

LEVI
No. But I found myself.

FADE OUT.
`;

const DEMO_SCENARIOS = [
    {
        type: "Action Trailer",
        specs: { duration: 120, fps: 24, ratio: '2.35:1' as const },
        title: "疾速追杀：代号S (Trailer)",
        logline: "当往日的杀手被昔日组织背叛，他必须在120秒内杀出重围，将重要情报送达避难所。",
        synopsis: "霓虹闪烁的东京雨夜。前顶级杀手'S'在一个拉面店被包围。他利用狭窄的空间和滚烫的汤底解决掉第一波敌人，随后驾驶一辆重型机车在涩谷街头狂飙。敌人的无人机在头顶盘旋，S必须在午夜钟声敲响前穿过十字路口。最终，他在避难所门前与组织的王牌特工进行了一场暴雨中的刀战。",
        raw: TRAILER_SCRIPT
    },
    {
        type: "Narrative Short (20min)",
        specs: { duration: 1200, fps: 24, ratio: '16:9' as const },
        title: "The Memory Architect",
        logline: "An architect of dreams dives too deep into his comatose wife's subconscious, only to question his own reality.",
        synopsis: "In 2045, memory diving is dangerous. Levi risks it all to save Anna. But the deeper he goes, the more the world breaks. He travels through layers of their past: the campus, the apartment, the accident. He discovers that his guilt has created a prison for her consciousness. Or is it his consciousness? The climax reveals a twist about who is truly in the machine.",
        raw: LONG_FORM_SCRIPT
    }
];

export const ScriptIngestion: React.FC<ScriptIngestionProps> = ({ onProcessComplete, onClose }) => {
    const [activeTab, setActiveTab] = useState<TabMode>('creation');
    const [buildMode, setBuildMode] = useState<BuildMode>('manual');

    // Metadata State
    const [projectTitle, setProjectTitle] = useState('');
    const [logline, setLogline] = useState('');
    const [synopsis, setSynopsis] = useState('');
    const [scriptText, setScriptText] = useState('');

    // Specs State
    const [targetDuration, setTargetDuration] = useState<number>(120);
    const [durationUnit, setDurationUnit] = useState<DurationUnit>('s');
    const [fps, setFps] = useState<24 | 25 | 30 | 60>(24);
    const [aspectRatio, setAspectRatio] = useState<'16:9' | '9:16' | '4:3' | '2.35:1' | '1:1'>('16:9');

    const [isProcessing, setIsProcessing] = useState(false);
    const [statusMessage, setStatusMessage] = useState("");
    const [elapsedTime, setElapsedTime] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [isGeneratingDemo, setIsGeneratingDemo] = useState(false);

    useEffect(() => {
        let interval: number;
        if (isProcessing) {
            setElapsedTime(0);
            interval = window.setInterval(() => {
                setElapsedTime(prev => prev + 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [isProcessing]);

    useEffect(() => {
        if (!isProcessing) return;
        if (elapsedTime > 2 && elapsedTime <= 5) setStatusMessage("正在分析故事结构...");
        if (elapsedTime > 5 && elapsedTime <= 10) setStatusMessage("AI 正在构建角色与场景...");
        if (elapsedTime > 10 && elapsedTime <= 15) setStatusMessage("生成分镜头脚本中...");
        if (elapsedTime > 15 && elapsedTime <= 25) setStatusMessage("注入视觉参考素材 (Writer's DNA)...");
        if (elapsedTime > 25) setStatusMessage("正在进行最终组装...");
    }, [elapsedTime, isProcessing]);

    const handleCreate = async () => {
        if (!projectTitle.trim()) {
            setError("请输入项目标题");
            return;
        }

        setIsProcessing(true);
        setError(null);

        const specs: ProjectSpecs = {
            totalDuration: targetDuration,
            fps,
            aspectRatio: aspectRatio as any
        };

        try {
            let resultBeats: Beat[] = [];
            let resultScript = scriptText;
            let resultMeta = { title: projectTitle, logline, synopsis };
            let resultCharacters: Character[] = [];

            if (activeTab === 'creation') {
                if (buildMode === 'manual') {
                    // Empty
                } else if (buildMode === 'ai_build') {
                    if (!logline.trim()) throw new Error("AI 构建需要填写一句话故事 (Logline)");
                    setStatusMessage("正在启动 AI 引擎...");
                    const result = await generateStructureFromSynopsis(projectTitle, logline, synopsis);
                    resultBeats = result.beats;
                    resultScript = result.meta.synopsis + "\n\n" + (result.beats.map(b => b.content).join('\n')); // Simple reconstruction
                    resultMeta = { ...resultMeta, ...result.meta };
                    resultCharacters = result.characters;
                }
            } else {
                if (!scriptText.trim()) throw new Error("请输入或粘贴内容");

                if (buildMode === 'parse') {
                    setStatusMessage("正在解析剧本...");
                    const result = await analyzeScriptToStructure(scriptText);
                    resultBeats = result.beats;
                    resultCharacters = result.characters;
                    // Auto-fill meta if missing
                    if (!logline && result.meta.logline) resultMeta.logline = result.meta.logline;
                    if (!synopsis && result.meta.synopsis) resultMeta.synopsis = result.meta.synopsis;
                } else if (buildMode === 'smart_build') {
                    setStatusMessage("正在启动改编引擎...");
                    const result = await smartBuildScript(scriptText);
                    resultBeats = result.beats;
                    resultCharacters = result.characters;
                    // Auto-fill meta
                    resultMeta = { ...resultMeta, ...result.meta };
                    resultScript = scriptText; // Keep original source
                }
            }

            onProcessComplete(resultBeats, resultScript, resultMeta, specs, resultCharacters);

        } catch (e: any) {
            setError(e.message || "项目创建失败，请稍后重试");
        } finally {
            setIsProcessing(false);
            setStatusMessage("");
        }
    };

    const switchTab = (tab: TabMode) => {
        setActiveTab(tab);
        if (tab === 'creation') setBuildMode('manual');
        else setBuildMode('parse');
        setError(null);
    };


    // Real AI Demo Generation
    const fillRandomDemo = async () => {
        setIsGeneratingDemo(true);
        setError(null);
        setElapsedTime(0);

        try {
            const { api } = await import('./services/api');
            const demoData = await api.remoteGenerateDemoScript("Action Thriller");

            // Check for soft error from backend
            if (demoData.title.includes("失败") || demoData.title === "Error" || demoData.title === "System Error") {
                throw new Error(demoData.logline || demoData.synopsis || "AI服务未响应");
            }

            setProjectTitle(demoData.title);
            setLogline(demoData.logline);
            setSynopsis(demoData.synopsis);
            setScriptText(demoData.script_content);

            // Set some defaults
            setTargetDuration(120);
            setDurationUnit('s');
            setFps(24);
            setAspectRatio('2.35:1');

            if (activeTab === 'creation') {
                setBuildMode('ai_build'); // Suggest AI Build
            } else {
                setBuildMode('parse');
            }

        } catch (err: any) {
            setError("AI Demo Generation Failed: " + err.message);
        } finally {
            setIsGeneratingDemo(false);
        }
    };


    const handleDurationInputChange = (valStr: string) => {
        const val = parseFloat(valStr) || 0;
        if (durationUnit === 'm') {
            setTargetDuration(val * 60);
        } else {
            setTargetDuration(val);
        }
    };

    const toggleUnit = () => {
        const newUnit = durationUnit === 's' ? 'm' : 's';
        setDurationUnit(newUnit);
    };

    const displayDuration = durationUnit === 'm'
        ? parseFloat((targetDuration / 60).toFixed(2))
        : targetDuration;


    const ModeCard = ({
        mode,
        title,
        desc,
        icon: Icon,
        isAi = false
    }: { mode: BuildMode, title: string, desc: string, icon: any, isAi?: boolean }) => (
        <div
            onClick={() => setBuildMode(mode)}
            className={`relative p-4 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col gap-2 group ${buildMode === mode
                ? 'bg-yellow-500/10 border-yellow-500 ring-1 ring-yellow-500/50'
                : 'bg-zinc-900 border-zinc-800 hover:bg-zinc-800 hover:border-zinc-600'
                }`}
        >
            <div className="flex items-center justify-between">
                <div className={`flex items-center gap-2 font-bold ${buildMode === mode ? 'text-yellow-400' : 'text-zinc-300'}`}>
                    {buildMode === mode && <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />}
                    {title}
                </div>
                {isAi && <Sparkles size={14} className={buildMode === mode ? 'text-indigo-400' : 'text-zinc-600'} />}
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed">{desc}</p>

            <div className={`absolute top-4 right-4 w-4 h-4 rounded-full border flex items-center justify-center ${buildMode === mode ? 'border-yellow-500 bg-yellow-500' : 'border-zinc-700'
                }`}>
                {buildMode === mode && <div className="w-1.5 h-1.5 rounded-full bg-black" />}
            </div>
        </div>
    );

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-300">

            <div className="w-full max-w-2xl bg-zinc-950 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col z-10 animate-in zoom-in-95 duration-300 relative">

                {onClose && (
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 z-20 text-zinc-500 hover:text-white transition-colors"
                    >
                        <X size={20} />
                    </button>
                )}

                <div className="flex items-center justify-between border-b border-zinc-800 px-2 bg-zinc-900/50">
                    <div className="flex">
                        <button
                            onClick={() => switchTab('creation')}
                            className={`px-6 py-4 text-sm font-bold flex items-center gap-2 transition-colors border-b-2 ${activeTab === 'creation' ? 'text-yellow-500 border-yellow-500' : 'text-zinc-500 border-transparent hover:text-zinc-300'
                                }`}
                        >
                            <Sparkles size={16} />
                            从零创作 (Creation)
                        </button>
                        <div className="w-px h-6 bg-zinc-800 my-auto"></div>
                        <button
                            onClick={() => switchTab('import')}
                            className={`px-6 py-4 text-sm font-bold flex items-center gap-2 transition-colors border-b-2 ${activeTab === 'import' ? 'text-yellow-500 border-yellow-500' : 'text-zinc-500 border-transparent hover:text-zinc-300'
                                }`}
                        >
                            <Upload size={16} />
                            导入故事 (Import)
                        </button>
                    </div>
                </div>

                <div className="p-8 overflow-y-auto max-h-[70vh] scrollbar-thin scrollbar-thumb-zinc-800">

                    <div className="space-y-6">
                        <div className="space-y-2 relative">
                            <div className="flex justify-between items-center">
                                <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-1">
                                    项目标题 <span className="text-red-500">*</span>
                                </label>
                                <button onClick={fillRandomDemo} className="text-[10px] text-zinc-500 hover:text-zinc-300 flex items-center gap-1 px-2 py-0.5 bg-zinc-900 rounded border border-zinc-800 hover:border-zinc-700 transition-colors">
                                    <Shuffle size={10} /> 填充示例 (Fill Demo)
                                </button>
                            </div>
                            <input
                                type="text"
                                value={projectTitle}
                                onChange={(e) => setProjectTitle(e.target.value)}
                                placeholder="例如：消失的第十一层"
                                className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-yellow-500/50 focus:ring-1 focus:ring-yellow-500/50 transition-all"
                                autoFocus
                            />
                        </div>

                        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 grid grid-cols-3 gap-4">
                            <div className="space-y-1">
                                <div className="flex justify-between items-center">
                                    <label className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1">
                                        <Timer size={10} /> 目标时长
                                    </label>
                                    <button
                                        onClick={toggleUnit}
                                        className="text-[9px] font-bold bg-zinc-800 px-1.5 rounded text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-500 transition-colors flex items-center gap-1"
                                    >
                                        <RefreshCw size={8} /> {durationUnit === 's' ? 'Seconds (s)' : 'Minutes (m)'}
                                    </button>
                                </div>
                                <div className="relative">
                                    <input
                                        type="number"
                                        value={displayDuration}
                                        onChange={(e) => handleDurationInputChange(e.target.value)}
                                        className="w-full bg-black border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200 focus:border-indigo-500 outline-none font-mono"
                                    />
                                    <span className="absolute right-3 top-1.5 text-xs text-zinc-600 font-bold pointer-events-none">
                                        {durationUnit === 's' ? 's' : 'min'}
                                    </span>
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1">
                                    <Film size={10} /> 帧率 (FPS)
                                </label>
                                <select
                                    value={fps}
                                    onChange={(e) => setFps(parseInt(e.target.value) as any)}
                                    className="w-full bg-black border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200 focus:border-indigo-500 outline-none"
                                >
                                    <option value={24}>24 fps (Cinema)</option>
                                    <option value={25}>25 fps (PAL)</option>
                                    <option value={30}>30 fps (NTSC)</option>
                                    <option value={60}>60 fps (HFR)</option>
                                </select>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1">
                                    <Monitor size={10} /> 画幅 (Ratio)
                                </label>
                                <select
                                    value={aspectRatio}
                                    onChange={(e) => setAspectRatio(e.target.value as any)}
                                    className="w-full bg-black border border-zinc-700 rounded px-2 py-1.5 text-sm text-zinc-200 focus:border-indigo-500 outline-none"
                                >
                                    <option value="16:9">16:9 (HD)</option>
                                    <option value="2.35:1">2.35:1 (Scope)</option>
                                    <option value="9:16">9:16 (Vertical)</option>
                                    <option value="4:3">4:3 (TV)</option>
                                    <option value="1:1">1:1 (Square)</option>
                                </select>
                            </div>
                        </div>

                        {activeTab === 'creation' ? (
                            <>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">一句话故事 (Logline)</label>
                                    <input
                                        type="text"
                                        value={logline}
                                        onChange={(e) => setLogline(e.target.value)}
                                        placeholder="核心冲突与主角目标..."
                                        className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-yellow-500/50 transition-all"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">故事梗概 (Synopsis)</label>
                                    <textarea
                                        value={synopsis}
                                        onChange={(e) => setSynopsis(e.target.value)}
                                        placeholder="输入详细故事大纲..."
                                        className="w-full h-24 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-yellow-500/50 resize-none transition-all"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4 mt-6">
                                    <ModeCard
                                        mode="manual"
                                        title="手动创作 (Manual)"
                                        desc="创建一张空白的剧本纸，从零开始手动书写或填充大纲。"
                                        icon={PenTool}
                                    />
                                    <ModeCard
                                        mode="ai_build"
                                        title="AI 智能构建 (AI Build)"
                                        desc="根据 Logline 自动生成大纲、角色和剧本初稿。"
                                        icon={Sparkles}
                                        isAi={true}
                                    />
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-1">
                                        故事原文 / 小说 / 剧本草稿 <span className="text-red-500">*</span>
                                    </label>
                                    <textarea
                                        value={scriptText}
                                        onChange={(e) => setScriptText(e.target.value)}
                                        placeholder="在此粘贴您的故事全文。我们将为您保留原文，并自动生成大纲和 Timeline..."
                                        className="w-full h-48 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-yellow-500/50 resize-none font-mono text-sm leading-relaxed transition-all"
                                    />
                                </div>

                                <div className="space-y-2 mt-4">
                                    <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider">处理方式</label>
                                    <div className="grid grid-cols-2 gap-4">
                                        <ModeCard
                                            mode="parse"
                                            title="原样解析 (Parse)"
                                            desc="保留您粘贴的文本内容不变。AI 仅辅助分析结构、提取大纲和角色。适合已完成的剧本或草稿。"
                                            icon={FileText}
                                        />
                                        <ModeCard
                                            mode="smart_build"
                                            title="AI 智能构建 (Smart Build)"
                                            desc="将粘贴的文本视为小说/素材。AI 将重写并构建为标准剧本格式，生成全新的场景和对白。"
                                            icon={Zap}
                                            isAi={true}
                                        />
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                <div className="p-6 border-t border-zinc-800 bg-zinc-900/50 flex items-center justify-between">
                    <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300 text-sm transition-colors">取消</button>

                    <div className="flex items-center gap-4">
                        {error && <span className="text-red-400 text-xs flex items-center gap-1"><AlertCircle size={12} /> {error}</span>}
                        <button
                            onClick={handleCreate}
                            disabled={isProcessing}
                            className={`flex items-center gap-2 px-6 py-2.5 rounded text-sm font-bold text-black transition-all min-w-[140px] justify-center ${isProcessing
                                ? 'bg-zinc-700 cursor-wait opacity-80'
                                : 'bg-zinc-200 hover:bg-white hover:shadow-[0_0_15px_rgba(255,255,255,0.2)]'
                                }`}
                        >
                            {isProcessing ? (
                                <div className="flex flex-col items-start leading-tight">
                                    <div className="flex items-center gap-2">
                                        <Loader2 size={14} className="animate-spin" />
                                        <span>处理中 ({elapsedTime}s)</span>
                                    </div>
                                    {statusMessage && <span className="text-[9px] opacity-70 font-normal">{statusMessage}</span>}
                                </div>
                            ) : (
                                <>
                                    {buildMode === 'manual' ? '创建空白项目' : '解析并导入'}
                                    <ArrowRight size={16} />
                                </>
                            )}
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
};