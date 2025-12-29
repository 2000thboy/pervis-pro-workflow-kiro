/**
 * 渲染对话框组件
 * 
 * Phase 2 Task 2.1: 视频渲染完善
 * - 渲染配置选择
 * - 启动渲染
 * - 进度显示
 */

import React, { useState, useEffect, useCallback } from 'react';
import { RenderProgress } from './RenderProgress';

interface RenderConfig {
  formats: Array<{ value: string; label: string; codecs: any }>;
  resolutions: Array<{ value: string; label: string; width: number; height: number }>;
  framerates: number[];
  quality_presets: Array<{ value: string; label: string; crf: number; bitrate: string }>;
}

interface RenderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  timelineId: string;
  timelineName?: string;
}

export const RenderDialog: React.FC<RenderDialogProps> = ({
  isOpen,
  onClose,
  timelineId,
  timelineName = '时间轴'
}) => {
  const [config, setConfig] = useState<RenderConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [checkResult, setCheckResult] = useState<any>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 渲染选项
  const [format, setFormat] = useState('mp4');
  const [resolution, setResolution] = useState('1080p');
  const [framerate, setFramerate] = useState(30);
  const [quality, setQuality] = useState('high');

  // 加载配置
  useEffect(() => {
    if (!isOpen) return;

    const loadConfig = async () => {
      try {
        const response = await fetch('/api/render/config');
        const result = await response.json();
        if (result.status === 'success') {
          setConfig(result);
        }
      } catch (e) {
        console.error('加载渲染配置失败:', e);
      }
    };

    loadConfig();
  }, [isOpen]);

  // 检查渲染条件
  useEffect(() => {
    if (!isOpen || !timelineId) return;

    const checkRequirements = async () => {
      setChecking(true);
      try {
        const response = await fetch(`/api/render/check/${timelineId}`);
        const result = await response.json();
        setCheckResult(result.check_result);
      } catch (e) {
        console.error('检查渲染条件失败:', e);
      } finally {
        setChecking(false);
      }
    };

    checkRequirements();
  }, [isOpen, timelineId]);

  // 启动渲染
  const handleStartRender = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/render/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timeline_id: timelineId,
          format,
          resolution,
          framerate,
          quality
        })
      });

      const result = await response.json();

      if (result.status === 'success') {
        setTaskId(result.task_id);
      } else {
        setError(result.detail?.message || '启动渲染失败');
      }
    } catch (e) {
      setError('网络错误，请重试');
    } finally {
      setLoading(false);
    }
  }, [timelineId, format, resolution, framerate, quality]);

  // 渲染完成
  const handleComplete = useCallback(() => {
    // 可以在这里添加完成后的逻辑
  }, []);

  // 重置状态
  const handleReset = useCallback(() => {
    setTaskId(null);
    setError(null);
  }, []);

  if (!isOpen) return null;

  return (
    <div className="render-dialog-overlay" onClick={onClose}>
      <div className="render-dialog" onClick={e => e.stopPropagation()}>
        <div className="render-dialog__header">
          <h2>导出视频</h2>
          <button className="render-dialog__close" onClick={onClose}>×</button>
        </div>

        <div className="render-dialog__content">
          {/* 时间轴信息 */}
          <div className="render-dialog__info">
            <span className="render-dialog__label">时间轴:</span>
            <span>{timelineName}</span>
          </div>

          {/* 检查结果 */}
          {checking && (
            <div className="render-dialog__checking">
              检查渲染条件...
            </div>
          )}

          {checkResult && !checkResult.can_render && (
            <div className="render-dialog__errors">
              <h4>无法渲染</h4>
              <ul>
                {checkResult.errors?.map((err: string, i: number) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 渲染进度 */}
          {taskId ? (
            <div className="render-dialog__progress">
              <RenderProgress
                taskId={taskId}
                onComplete={handleComplete}
                onError={setError}
              />
              <button 
                className="render-dialog__btn render-dialog__btn--secondary"
                onClick={handleReset}
                style={{ marginTop: 12 }}
              >
                新建渲染
              </button>
            </div>
          ) : (
            <>
              {/* 渲染配置 */}
              {config && checkResult?.can_render && (
                <div className="render-dialog__config">
                  {/* 格式 */}
                  <div className="render-dialog__field">
                    <label>输出格式</label>
                    <select value={format} onChange={e => setFormat(e.target.value)}>
                      {config.formats.map(f => (
                        <option key={f.value} value={f.value}>{f.label}</option>
                      ))}
                    </select>
                  </div>

                  {/* 分辨率 */}
                  <div className="render-dialog__field">
                    <label>分辨率</label>
                    <select value={resolution} onChange={e => setResolution(e.target.value)}>
                      {config.resolutions.map(r => (
                        <option key={r.value} value={r.value}>
                          {r.label} ({r.width}×{r.height})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* 帧率 */}
                  <div className="render-dialog__field">
                    <label>帧率</label>
                    <select value={framerate} onChange={e => setFramerate(Number(e.target.value))}>
                      {config.framerates.map(f => (
                        <option key={f} value={f}>{f} fps</option>
                      ))}
                    </select>
                  </div>

                  {/* 质量 */}
                  <div className="render-dialog__field">
                    <label>质量</label>
                    <select value={quality} onChange={e => setQuality(e.target.value)}>
                      {config.quality_presets.map(q => (
                        <option key={q.value} value={q.value}>
                          {q.label} ({q.bitrate})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* 预估信息 */}
                  {checkResult && (
                    <div className="render-dialog__estimate">
                      <div>
                        <span>时长:</span>
                        <span>{Math.round(checkResult.timeline_duration || 0)}秒</span>
                      </div>
                      <div>
                        <span>片段数:</span>
                        <span>{checkResult.clip_count || 0}</span>
                      </div>
                      <div>
                        <span>预计大小:</span>
                        <span>{(checkResult.estimated_size_mb || 0).toFixed(1)} MB</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 错误信息 */}
              {error && (
                <div className="render-dialog__error">
                  {error}
                </div>
              )}

              {/* 操作按钮 */}
              <div className="render-dialog__actions">
                <button 
                  className="render-dialog__btn render-dialog__btn--secondary"
                  onClick={onClose}
                >
                  取消
                </button>
                <button 
                  className="render-dialog__btn render-dialog__btn--primary"
                  onClick={handleStartRender}
                  disabled={loading || !checkResult?.can_render}
                >
                  {loading ? '启动中...' : '开始渲染'}
                </button>
              </div>
            </>
          )}
        </div>

        <style>{`
          .render-dialog-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
          }
          
          .render-dialog {
            background: #1f2937;
            border-radius: 12px;
            width: 480px;
            max-width: 90vw;
            max-height: 90vh;
            overflow: auto;
            color: #e5e7eb;
          }
          
          .render-dialog__header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid #374151;
          }
          
          .render-dialog__header h2 {
            margin: 0;
            font-size: 18px;
            font-weight: 600;
          }
          
          .render-dialog__close {
            background: none;
            border: none;
            color: #9ca3af;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            line-height: 1;
          }
          
          .render-dialog__close:hover {
            color: #e5e7eb;
          }
          
          .render-dialog__content {
            padding: 20px;
          }
          
          .render-dialog__info {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            font-size: 14px;
          }
          
          .render-dialog__label {
            color: #9ca3af;
          }
          
          .render-dialog__checking {
            text-align: center;
            color: #9ca3af;
            padding: 20px;
          }
          
          .render-dialog__errors {
            background: #7f1d1d;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 16px;
          }
          
          .render-dialog__errors h4 {
            margin: 0 0 8px;
            color: #fca5a5;
          }
          
          .render-dialog__errors ul {
            margin: 0;
            padding-left: 20px;
            color: #fca5a5;
            font-size: 13px;
          }
          
          .render-dialog__config {
            display: flex;
            flex-direction: column;
            gap: 16px;
          }
          
          .render-dialog__field {
            display: flex;
            flex-direction: column;
            gap: 6px;
          }
          
          .render-dialog__field label {
            font-size: 13px;
            color: #9ca3af;
          }
          
          .render-dialog__field select {
            padding: 10px 12px;
            background: #374151;
            border: 1px solid #4b5563;
            border-radius: 6px;
            color: #e5e7eb;
            font-size: 14px;
          }
          
          .render-dialog__field select:focus {
            outline: none;
            border-color: #3b82f6;
          }
          
          .render-dialog__estimate {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            padding: 12px;
            background: #374151;
            border-radius: 8px;
            font-size: 13px;
          }
          
          .render-dialog__estimate > div {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }
          
          .render-dialog__estimate span:first-child {
            color: #9ca3af;
          }
          
          .render-dialog__error {
            background: #7f1d1d;
            border-radius: 8px;
            padding: 12px;
            margin-top: 16px;
            color: #fca5a5;
            font-size: 13px;
          }
          
          .render-dialog__actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid #374151;
          }
          
          .render-dialog__btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: opacity 0.2s;
          }
          
          .render-dialog__btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          
          .render-dialog__btn--primary {
            background: #3b82f6;
            color: white;
          }
          
          .render-dialog__btn--secondary {
            background: #4b5563;
            color: white;
          }
          
          .render-dialog__btn:hover:not(:disabled) {
            opacity: 0.9;
          }
          
          .render-dialog__progress {
            padding: 8px 0;
          }
        `}</style>
      </div>
    </div>
  );
};

export default RenderDialog;
