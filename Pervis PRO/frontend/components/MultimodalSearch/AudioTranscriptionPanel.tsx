import React, { useState, useEffect, useCallback } from 'react';
import { 
  Mic, 
  Play, 
  Pause, 
  Volume2, 
  VolumeX,
  Search,
  Download,
  RefreshCw,
  Clock,
  FileText,
  Languages,
  Zap,
  AlertCircle,
  CheckCircle,
  Loader2,
  Edit3,
  Save,
  X
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Card } from '../ui/Card';

// 转录数据类型
export interface TranscriptionSegment {
  id: string;
  start_time: number;
  end_time: number;
  text: string;
  confidence: number;
  speaker?: string;
  language?: string;
  words?: Array<{
    word: string;
    start_time: number;
    end_time: number;
    confidence: number;
  }>;
}

export interface TranscriptionData {
  duration: number;
  language: string;
  confidence: number;
  segments: TranscriptionSegment[];
  full_text: string;
  word_count: number;
  speaker_count: number;
  processing_time: number;
}

// 转录状态
export interface TranscriptionStatus {
  status: 'not_transcribed' | 'processing' | 'completed' | 'failed';
  has_transcription: boolean;
  duration?: number;
  language?: string;
  confidence?: number;
  word_count?: number;
  error_message?: string;
}

// 组件属性
export interface AudioTranscriptionPanelProps {
  assetId: string;
  assetFilename?: string;
  onTranscriptionComplete?: (data: TranscriptionData) => void;
  onSegmentSelect?: (segment: TranscriptionSegment) => void;
  className?: string;
}

export const AudioTranscriptionPanel: React.FC<AudioTranscriptionPanelProps> = ({
  assetId,
  assetFilename,
  onTranscriptionComplete,
  onSegmentSelect,
  className = ''
}) => {
  // 状态管理
  const [status, setStatus] = useState<TranscriptionStatus | null>(null);
  const [transcriptionData, setTranscriptionData] = useState<TranscriptionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredSegments, setFilteredSegments] = useState<TranscriptionSegment[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);
  const [editingSegment, setEditingSegment] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  
  // 转录配置
  const [transcriptionConfig, setTranscriptionConfig] = useState({
    model_size: 'base',
    language: 'auto',
    enable_speaker_detection: true,
    enable_word_timestamps: true
  });

  // 加载转录状态
  useEffect(() => {
    loadTranscriptionStatus();
  }, [assetId]);

  // 搜索过滤
  useEffect(() => {
    if (!transcriptionData?.segments) {
      setFilteredSegments([]);
      return;
    }

    if (!searchQuery.trim()) {
      setFilteredSegments(transcriptionData.segments);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = transcriptionData.segments.filter(segment =>
      segment.text.toLowerCase().includes(query) ||
      segment.speaker?.toLowerCase().includes(query)
    );
    setFilteredSegments(filtered);
  }, [transcriptionData, searchQuery]);

  const loadTranscriptionStatus = async () => {
    try {
      const response = await fetch(`/api/transcription/status/${assetId}`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
        
        // 如果已有转录数据，加载完整数据
        if (data.has_transcription) {
          loadTranscriptionData();
        }
      }
    } catch (error) {
      console.error('Failed to load transcription status:', error);
      setError('加载转录状态失败');
    }
  };

  const loadTranscriptionData = async () => {
    try {
      const response = await fetch(`/api/transcription/data/${assetId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setTranscriptionData(data.transcription);
          onTranscriptionComplete?.(data.transcription);
        }
      }
    } catch (error) {
      console.error('Failed to load transcription data:', error);
      setError('加载转录数据失败');
    }
  };

  // 开始转录
  const startTranscription = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/transcription/transcribe/${assetId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(transcriptionConfig)
      });

      if (!response.ok) {
        throw new Error(`Transcription failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.status === 'success') {
        setTranscriptionData(data.transcription);
        setStatus({
          status: 'completed',
          has_transcription: true,
          ...data.transcription
        });
        onTranscriptionComplete?.(data.transcription);
      } else {
        throw new Error(data.message || '转录失败');
      }

    } catch (err) {
      console.error('Transcription failed:', err);
      setError(`音频转录失败: ${err}`);
      setStatus(prev => prev ? { ...prev, status: 'failed', error_message: String(err) } : null);
    } finally {
      setLoading(false);
    }
  };

  // 编辑转录文本
  const handleEditSegment = (segmentId: string, currentText: string) => {
    setEditingSegment(segmentId);
    setEditText(currentText);
  };

  const saveSegmentEdit = async () => {
    if (!editingSegment || !transcriptionData) return;

    try {
      const response = await fetch(`/api/transcription/edit/${assetId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          segment_id: editingSegment,
          new_text: editText
        })
      });

      if (response.ok) {
        // 更新本地数据
        const updatedSegments = transcriptionData.segments.map(segment =>
          segment.id === editingSegment ? { ...segment, text: editText } : segment
        );
        
        setTranscriptionData({
          ...transcriptionData,
          segments: updatedSegments,
          full_text: updatedSegments.map(s => s.text).join(' ')
        });
        
        setEditingSegment(null);
        setEditText('');
      }
    } catch (error) {
      console.error('Failed to save edit:', error);
      setError('保存编辑失败');
    }
  };

  const cancelEdit = () => {
    setEditingSegment(null);
    setEditText('');
  };

  // 格式化时间
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  // 格式化置信度
  const formatConfidence = (confidence: number): string => {
    return `${(confidence * 100).toFixed(0)}%`;
  };

  // 获取置信度颜色
  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  // 渲染状态指示器
  const renderStatusIndicator = () => {
    if (!status) return null;

    const statusConfig = {
      not_transcribed: {
        icon: AlertCircle,
        color: 'text-zinc-400',
        bg: 'bg-zinc-700/30',
        text: '未转录'
      },
      processing: {
        icon: Loader2,
        color: 'text-blue-400',
        bg: 'bg-blue-500/10',
        text: '转录中...',
        animate: 'animate-spin'
      },
      completed: {
        icon: CheckCircle,
        color: 'text-green-400',
        bg: 'bg-green-500/10',
        text: '转录完成'
      },
      failed: {
        icon: AlertCircle,
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        text: '转录失败'
      }
    };

    const config = statusConfig[status.status];
    const Icon = config.icon;

    return (
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg}`}>
        <Icon size={16} className={`${config.color} ${config.animate || ''}`} />
        <span className={`text-sm ${config.color}`}>{config.text}</span>
        {status.status === 'completed' && status.word_count && (
          <span className="text-xs text-zinc-400">
            ({status.word_count} 词)
          </span>
        )}
      </div>
    );
  };

  // 渲染统计信息
  const renderStatistics = () => {
    if (!transcriptionData) return null;

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
          <Clock size={20} className="mx-auto mb-1 text-blue-400" />
          <div className="text-sm font-medium text-white">
            {formatTime(transcriptionData.duration)}
          </div>
          <div className="text-xs text-zinc-400">总时长</div>
        </div>
        
        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
          <FileText size={20} className="mx-auto mb-1 text-green-400" />
          <div className="text-sm font-medium text-white">
            {transcriptionData.word_count}
          </div>
          <div className="text-xs text-zinc-400">词数</div>
        </div>
        
        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
          <Languages size={20} className="mx-auto mb-1 text-amber-400" />
          <div className="text-sm font-medium text-white">
            {transcriptionData.language}
          </div>
          <div className="text-xs text-zinc-400">语言</div>
        </div>
        
        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
          <Mic size={20} className="mx-auto mb-1 text-purple-400" />
          <div className={`text-sm font-medium ${getConfidenceColor(transcriptionData.confidence)}`}>
            {formatConfidence(transcriptionData.confidence)}
          </div>
          <div className="text-xs text-zinc-400">置信度</div>
        </div>
      </div>
    );
  };

  // 渲染转录片段
  const renderTranscriptionSegments = () => {
    if (!filteredSegments.length) {
      return (
        <div className="text-center py-8">
          <FileText size={48} className="mx-auto mb-3 opacity-50 text-zinc-500" />
          <p className="text-zinc-400">
            {searchQuery ? '没有找到匹配的转录片段' : '没有转录数据'}
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {filteredSegments.map((segment, index) => (
          <div
            key={segment.id}
            className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
              selectedSegment === segment.id
                ? 'border-amber-500 bg-amber-500/5'
                : 'border-zinc-700 hover:border-zinc-600 bg-zinc-800/30'
            }`}
            onClick={() => {
              setSelectedSegment(selectedSegment === segment.id ? null : segment.id);
              onSegmentSelect?.(segment);
            }}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className="text-xs text-zinc-400 font-mono">
                  {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                </span>
                
                {segment.speaker && (
                  <span className="px-2 py-1 bg-blue-500/10 text-xs text-blue-400 rounded">
                    {segment.speaker}
                  </span>
                )}
                
                <span className={`text-xs ${getConfidenceColor(segment.confidence)}`}>
                  {formatConfidence(segment.confidence)}
                </span>
              </div>
              
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleEditSegment(segment.id, segment.text);
                  }}
                  icon={Edit3}
                />
                
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    // TODO: 播放这个片段
                  }}
                  icon={Play}
                />
              </div>
            </div>
            
            {/* 转录文本 */}
            {editingSegment === segment.id ? (
              <div className="space-y-2">
                <Input
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="text-sm"
                />
                <div className="flex items-center gap-2">
                  <Button size="sm" onClick={saveSegmentEdit} icon={Save}>
                    保存
                  </Button>
                  <Button size="sm" variant="ghost" onClick={cancelEdit} icon={X}>
                    取消
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-zinc-300 leading-relaxed">
                {segment.text}
              </p>
            )}
            
            {/* 词级时间戳 */}
            {selectedSegment === segment.id && segment.words && segment.words.length > 0 && (
              <div className="mt-3 pt-3 border-t border-zinc-700">
                <h6 className="text-xs text-zinc-400 mb-2">词级时间戳</h6>
                <div className="flex flex-wrap gap-1">
                  {segment.words.map((word, wordIndex) => (
                    <span
                      key={wordIndex}
                      className={`px-2 py-1 rounded text-xs cursor-pointer transition-colors ${
                        word.confidence >= 0.8
                          ? 'bg-green-500/10 text-green-400 hover:bg-green-500/20'
                          : word.confidence >= 0.6
                          ? 'bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20'
                          : 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                      }`}
                      title={`${formatTime(word.start_time)} - ${formatTime(word.end_time)} (${formatConfidence(word.confidence)})`}
                    >
                      {word.word}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 头部控制区域 */}
      <Card title={`音频转录 - ${assetFilename || assetId}`} variant="elevated">
        <div className="space-y-4">
          {/* 状态和控制 */}
          <div className="flex items-center justify-between">
            {renderStatusIndicator()}
            
            <div className="flex items-center gap-2">
              {status?.status === 'not_transcribed' && (
                <Button
                  onClick={startTranscription}
                  loading={loading}
                  icon={Zap}
                >
                  开始转录
                </Button>
              )}
              
              {status?.status === 'completed' && (
                <Button
                  variant="ghost"
                  onClick={() => {
                    // TODO: 导出转录文本
                  }}
                  icon={Download}
                >
                  导出
                </Button>
              )}
              
              <Button
                variant="ghost"
                onClick={loadTranscriptionStatus}
                icon={RefreshCw}
              >
                刷新
              </Button>
            </div>
          </div>
          
          {/* 转录配置 */}
          {status?.status === 'not_transcribed' && (
            <div className="p-3 bg-zinc-800/30 rounded-lg">
              <h4 className="text-sm font-medium text-white mb-3">转录配置</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">模型大小</label>
                  <select
                    value={transcriptionConfig.model_size}
                    onChange={(e) => setTranscriptionConfig(prev => ({
                      ...prev,
                      model_size: e.target.value
                    }))}
                    className="w-full px-2 py-1 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  >
                    <option value="tiny">Tiny (快速)</option>
                    <option value="base">Base (标准)</option>
                    <option value="small">Small (精确)</option>
                    <option value="medium">Medium (高精度)</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">语言</label>
                  <select
                    value={transcriptionConfig.language}
                    onChange={(e) => setTranscriptionConfig(prev => ({
                      ...prev,
                      language: e.target.value
                    }))}
                    className="w-full px-2 py-1 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  >
                    <option value="auto">自动检测</option>
                    <option value="zh">中文</option>
                    <option value="en">英文</option>
                    <option value="ja">日文</option>
                    <option value="ko">韩文</option>
                  </select>
                </div>
                
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-xs text-zinc-400">
                    <input
                      type="checkbox"
                      checked={transcriptionConfig.enable_speaker_detection}
                      onChange={(e) => setTranscriptionConfig(prev => ({
                        ...prev,
                        enable_speaker_detection: e.target.checked
                      }))}
                      className="rounded"
                    />
                    说话人识别
                  </label>
                </div>
                
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-xs text-zinc-400">
                    <input
                      type="checkbox"
                      checked={transcriptionConfig.enable_word_timestamps}
                      onChange={(e) => setTranscriptionConfig(prev => ({
                        ...prev,
                        enable_word_timestamps: e.target.checked
                      }))}
                      className="rounded"
                    />
                    词级时间戳
                  </label>
                </div>
              </div>
            </div>
          )}
          
          {/* 错误信息 */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
        </div>
      </Card>
      
      {/* 统计信息 */}
      {transcriptionData && (
        <Card title="转录统计" variant="elevated">
          {renderStatistics()}
        </Card>
      )}
      
      {/* 搜索和过滤 */}
      {transcriptionData && (
        <Card title="转录内容" variant="elevated">
          <div className="space-y-4">
            {/* 搜索框 */}
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <Input
                  placeholder="搜索转录内容或说话人..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  leftIcon={Search}
                />
              </div>
              
              <div className="text-sm text-zinc-400">
                {filteredSegments.length} / {transcriptionData.segments.length} 片段
              </div>
            </div>
            
            {/* 完整文本预览 */}
            {!searchQuery && (
              <div className="p-3 bg-zinc-800/30 rounded-lg">
                <h5 className="text-sm font-medium text-white mb-2">完整文本</h5>
                <p className="text-sm text-zinc-300 leading-relaxed line-clamp-4">
                  {transcriptionData.full_text}
                </p>
              </div>
            )}
            
            {/* 转录片段列表 */}
            {renderTranscriptionSegments()}
          </div>
        </Card>
      )}
    </div>
  );
};

export default AudioTranscriptionPanel;