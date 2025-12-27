/**
 * 市场分析面板
 * 显示目标受众、市场定位、竞品分析、发行渠道建议
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Users, 
  Target, 
  Film,
  Tv,
  Globe,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  BarChart3,
  Sparkles
} from 'lucide-react';
import { wizardApi, MarketAnalysis } from './api';

interface MarketAnalysisPanelProps {
  projectId: string;
  projectType?: string;
  genre?: string;
  onAnalysisComplete?: (analysis: MarketAnalysis) => void;
}

export const MarketAnalysisPanel: React.FC<MarketAnalysisPanelProps> = ({
  projectId,
  projectType,
  genre,
  onAnalysisComplete
}) => {
  const [analysis, setAnalysis] = useState<MarketAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<string[]>(['audience', 'positioning']);

  // 加载分析
  useEffect(() => {
    if (projectId) {
      loadAnalysis();
    }
  }, [projectId]);

  const loadAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await wizardApi.getMarketAnalysis(projectId);
      setAnalysis(result);
      if (onAnalysisComplete) {
        onAnalysisComplete(result);
      }
    } catch (err) {
      // 如果没有现有分析，尝试生成新的
      await generateAnalysis();
    } finally {
      setLoading(false);
    }
  };

  const generateAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await wizardApi.analyzeMarket({
        project_id: projectId,
        project_type: projectType,
        genre: genre
      });
      setAnalysis(result);
      if (onAnalysisComplete) {
        onAnalysisComplete(result);
      }
    } catch (err) {
      setError('市场分析生成失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => 
      prev.includes(section) 
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  // 渲染可折叠区块
  const Section: React.FC<{
    id: string;
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
  }> = ({ id, title, icon, children }) => {
    const isExpanded = expandedSections.includes(id);
    return (
      <div className="border border-zinc-800 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection(id)}
          className="w-full flex items-center justify-between p-3 bg-zinc-800/50 hover:bg-zinc-800 transition-colors"
        >
          <div className="flex items-center gap-2">
            {icon}
            <span className="text-sm font-medium text-zinc-300">{title}</span>
          </div>
          {isExpanded ? (
            <ChevronUp size={16} className="text-zinc-500" />
          ) : (
            <ChevronDown size={16} className="text-zinc-500" />
          )}
        </button>
        {isExpanded && (
          <div className="p-3 bg-zinc-900/50">
            {children}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 bg-zinc-900/50 rounded-lg">
        <Loader2 className="text-amber-500 animate-spin mb-3" size={32} />
        <div className="text-sm text-zinc-400">Market_Agent 正在分析...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 bg-zinc-900/50 rounded-lg">
        <div className="text-sm text-red-400 mb-3">{error}</div>
        <button
          onClick={generateAnalysis}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors"
        >
          <RefreshCw size={14} />
          <span>重试</span>
        </button>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center py-12 bg-zinc-900/50 rounded-lg border border-dashed border-zinc-800">
        <BarChart3 className="text-zinc-700 mb-3" size={32} />
        <div className="text-sm text-zinc-500 mb-3">尚未生成市场分析</div>
        <button
          onClick={generateAnalysis}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-400 rounded-lg text-sm text-black font-medium transition-colors"
        >
          <Sparkles size={14} />
          <span>生成市场分析</span>
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="text-amber-500" size={18} />
          <span className="text-sm font-medium text-white">市场分析报告</span>
        </div>
        <button
          onClick={generateAnalysis}
          className="flex items-center gap-1 px-2 py-1 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <RefreshCw size={12} />
          <span>刷新</span>
        </button>
      </div>

      {/* 目标受众 */}
      <Section
        id="audience"
        title="目标受众"
        icon={<Users size={16} className="text-blue-400" />}
      >
        <div className="space-y-2">
          {analysis.target_audience?.demographics && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">人口统计</div>
              <div className="text-sm text-zinc-300">{analysis.target_audience.demographics}</div>
            </div>
          )}
          {analysis.target_audience?.psychographics && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">心理特征</div>
              <div className="text-sm text-zinc-300">{analysis.target_audience.psychographics}</div>
            </div>
          )}
          {analysis.target_audience?.viewing_habits && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">观看习惯</div>
              <div className="text-sm text-zinc-300">{analysis.target_audience.viewing_habits}</div>
            </div>
          )}
        </div>
      </Section>

      {/* 市场定位 */}
      <Section
        id="positioning"
        title="市场定位"
        icon={<Target size={16} className="text-green-400" />}
      >
        <div className="space-y-2">
          {analysis.market_positioning?.unique_selling_points && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">独特卖点</div>
              <ul className="list-disc list-inside text-sm text-zinc-300 space-y-1">
                {analysis.market_positioning.unique_selling_points.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          {analysis.market_positioning?.market_gap && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">市场空白</div>
              <div className="text-sm text-zinc-300">{analysis.market_positioning.market_gap}</div>
            </div>
          )}
        </div>
      </Section>

      {/* 竞品分析 */}
      <Section
        id="competitors"
        title="竞品分析"
        icon={<Film size={16} className="text-purple-400" />}
      >
        <div className="space-y-2">
          {analysis.competitor_analysis?.similar_projects && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">类似项目</div>
              <div className="flex flex-wrap gap-2">
                {analysis.competitor_analysis.similar_projects.map((project, i) => (
                  <span key={i} className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-300">
                    {project}
                  </span>
                ))}
              </div>
            </div>
          )}
          {analysis.competitor_analysis?.differentiation && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">差异化策略</div>
              <div className="text-sm text-zinc-300">{analysis.competitor_analysis.differentiation}</div>
            </div>
          )}
        </div>
      </Section>

      {/* 发行渠道 */}
      <Section
        id="distribution"
        title="发行渠道建议"
        icon={<Globe size={16} className="text-cyan-400" />}
      >
        <div className="space-y-2">
          {analysis.distribution_channels?.primary && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">主要渠道</div>
              <div className="flex flex-wrap gap-2">
                {analysis.distribution_channels.primary.map((channel, i) => (
                  <span key={i} className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded text-xs">
                    {channel}
                  </span>
                ))}
              </div>
            </div>
          )}
          {analysis.distribution_channels?.secondary && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">次要渠道</div>
              <div className="flex flex-wrap gap-2">
                {analysis.distribution_channels.secondary.map((channel, i) => (
                  <span key={i} className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400">
                    {channel}
                  </span>
                ))}
              </div>
            </div>
          )}
          {analysis.distribution_channels?.strategy && (
            <div>
              <div className="text-xs text-zinc-500 mb-1">发行策略</div>
              <div className="text-sm text-zinc-300">{analysis.distribution_channels.strategy}</div>
            </div>
          )}
        </div>
      </Section>

      {/* 数据来源标注 */}
      <div className="text-[10px] text-zinc-600 text-center pt-2">
        由 Market_Agent 生成 · {analysis.is_dynamic ? '基于项目数据的动态分析' : '基于规则的静态分析'}
      </div>
    </div>
  );
};

export default MarketAnalysisPanel;
