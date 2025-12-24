import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { AssetPickerButton, Asset, SearchResult } from '../components/AssetPicker';
import { Video, Image as ImageIcon, Plus, Search } from 'lucide-react';

const AssetPickerDemo: React.FC = () => {
  const [selectedAssets, setSelectedAssets] = useState<(Asset | SearchResult)[]>([]);
  const [lastSelectedAsset, setLastSelectedAsset] = useState<Asset | SearchResult | null>(null);

  // 模拟Beat数据
  const mockBeatData = {
    content: "雨夜城市街道，Alex匆忙逃跑",
    tags: {
      emotion_tags: ["紧张", "恐惧", "急迫"],
      scene_tags: ["城市", "夜晚", "雨天", "街道", "霓虹灯"],
      action_tags: ["奔跑", "逃跑", "回头张望"],
      cinematography_tags: ["手持摄影", "追踪镜头", "特写"]
    }
  };

  const handleSingleSelect = (asset: Asset | SearchResult) => {
    setLastSelectedAsset(asset);
    console.log('Selected asset:', asset);
  };

  const handleMultiSelect = (assets: (Asset | SearchResult)[]) => {
    setSelectedAssets(assets);
    console.log('Selected assets:', assets);
  };

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-black text-white p-6">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* 页面标题 */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white mb-2">
            AssetPicker 组件演示
          </h1>
          <p className="text-zinc-400">
            演示素材选择器的各种使用场景和功能
          </p>
        </div>

        {/* 基础用法 */}
        <Card title="基础用法" variant="elevated">
          <div className="space-y-4">
            <p className="text-zinc-400">
              基本的素材选择功能，支持单选和多选模式
            </p>
            
            <div className="flex flex-wrap gap-3">
              <AssetPickerButton
                projectId="demo-project"
                onSelect={handleSingleSelect}
                buttonText="选择单个素材"
                variant="primary"
              />
              
              <AssetPickerButton
                projectId="demo-project"
                onMultiSelect={handleMultiSelect}
                allowMultiSelect={true}
                buttonText="选择多个素材"
                variant="secondary"
              />
              
              <AssetPickerButton
                projectId="demo-project"
                onSelect={handleSingleSelect}
                assetTypes={['video']}
                buttonText="仅选择视频"
                variant="outline"
                icon={Video}
              />
              
              <AssetPickerButton
                projectId="demo-project"
                onSelect={handleSingleSelect}
                assetTypes={['image']}
                buttonText="仅选择图片"
                variant="outline"
                icon={ImageIcon}
              />
            </div>
          </div>
        </Card>

        {/* 语义搜索用法 */}
        <Card title="语义搜索用法" variant="elevated">
          <div className="space-y-4">
            <p className="text-zinc-400">
              基于Beat内容和标签的智能素材推荐
            </p>
            
            <div className="p-4 bg-zinc-800/30 rounded-lg">
              <h4 className="font-medium text-white mb-2">模拟Beat数据:</h4>
              <div className="space-y-2 text-sm">
                <p><span className="text-zinc-400">内容:</span> {mockBeatData.content}</p>
                <p><span className="text-zinc-400">情绪标签:</span> {mockBeatData.tags.emotion_tags.join(', ')}</p>
                <p><span className="text-zinc-400">场景标签:</span> {mockBeatData.tags.scene_tags.join(', ')}</p>
                <p><span className="text-zinc-400">动作标签:</span> {mockBeatData.tags.action_tags.join(', ')}</p>
                <p><span className="text-zinc-400">摄影标签:</span> {mockBeatData.tags.cinematography_tags.join(', ')}</p>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-3">
              <AssetPickerButton
                projectId="demo-project"
                beatContent={mockBeatData.content}
                beatTags={mockBeatData.tags}
                onSelect={handleSingleSelect}
                buttonText="智能推荐素材"
                variant="primary"
                icon={Search}
                modalTitle="智能素材推荐"
                modalSubtitle="基于Beat内容的语义搜索结果"
              />
              
              <AssetPickerButton
                projectId="demo-project"
                beatContent={mockBeatData.content}
                beatTags={mockBeatData.tags}
                onMultiSelect={handleMultiSelect}
                allowMultiSelect={true}
                buttonText="批量智能推荐"
                variant="secondary"
                icon={Plus}
              />
            </div>
          </div>
        </Card>

        {/* 选择结果显示 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 单选结果 */}
          <Card title="最后选择的素材" variant="elevated">
            {lastSelectedAsset ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  {lastSelectedAsset.type === 'video' ? (
                    <Video size={20} className="text-blue-400" />
                  ) : (
                    <ImageIcon size={20} className="text-green-400" />
                  )}
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-white truncate">
                      {lastSelectedAsset.filename}
                    </h4>
                    <p className="text-sm text-zinc-400">
                      {lastSelectedAsset.type === 'video' && lastSelectedAsset.duration
                        ? `时长: ${formatDuration(lastSelectedAsset.duration)}`
                        : lastSelectedAsset.type === 'image' && lastSelectedAsset.width
                        ? `尺寸: ${lastSelectedAsset.width}×${lastSelectedAsset.height}`
                        : ''}
                    </p>
                  </div>
                </div>
                
                {/* 相似度分数 */}
                {'similarity_score' in lastSelectedAsset && lastSelectedAsset.similarity_score && (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-zinc-400">相似度:</span>
                    <div className="flex-1 bg-zinc-700 rounded-full h-2">
                      <div 
                        className="bg-amber-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${lastSelectedAsset.similarity_score * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-amber-400">
                      {(lastSelectedAsset.similarity_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
                
                {/* 匹配理由 */}
                {'match_reason' in lastSelectedAsset && lastSelectedAsset.match_reason && (
                  <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                    <p className="text-sm text-amber-400">
                      <span className="font-medium">推荐理由:</span> {lastSelectedAsset.match_reason}
                    </p>
                  </div>
                )}
                
                {/* 基本信息 */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-zinc-400">文件大小:</span>
                    <span className="ml-2 text-white">{formatFileSize(lastSelectedAsset.file_size)}</span>
                  </div>
                  <div>
                    <span className="text-zinc-400">创建时间:</span>
                    <span className="ml-2 text-white">
                      {new Date(lastSelectedAsset.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                
                {/* 标签 */}
                {lastSelectedAsset.tags && (
                  <div className="space-y-2">
                    <span className="text-sm text-zinc-400">标签:</span>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(lastSelectedAsset.tags).map(([category, tags]) =>
                        tags.slice(0, 3).map((tag, index) => (
                          <span
                            key={`${category}-${index}`}
                            className="px-2 py-1 bg-zinc-700/50 text-xs text-zinc-300 rounded-md"
                          >
                            {tag}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-zinc-500">
                <Video size={48} className="mx-auto mb-3 opacity-50" />
                <p>尚未选择任何素材</p>
              </div>
            )}
          </Card>

          {/* 多选结果 */}
          <Card title={`已选择的素材 (${selectedAssets.length})`} variant="elevated">
            {selectedAssets.length > 0 ? (
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {selectedAssets.map((asset, index) => (
                  <div key={asset.id} className="flex items-center gap-3 p-2 bg-zinc-800/30 rounded-lg">
                    <div className="flex-shrink-0">
                      {asset.type === 'video' ? (
                        <Video size={16} className="text-blue-400" />
                      ) : (
                        <ImageIcon size={16} className="text-green-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {asset.filename}
                      </p>
                      <p className="text-xs text-zinc-400">
                        {formatFileSize(asset.file_size)}
                        {'similarity_score' in asset && asset.similarity_score && (
                          <span className="ml-2 text-amber-400">
                            {(asset.similarity_score * 100).toFixed(0)}%
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="text-xs text-zinc-500">
                      #{index + 1}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-zinc-500">
                <Plus size={48} className="mx-auto mb-3 opacity-50" />
                <p>尚未选择任何素材</p>
              </div>
            )}
          </Card>
        </div>

        {/* 使用说明 */}
        <Card title="使用说明" variant="outlined">
          <div className="space-y-4 text-sm text-zinc-400">
            <div>
              <h4 className="font-medium text-white mb-2">功能特性:</h4>
              <ul className="space-y-1 list-disc list-inside">
                <li>支持单选和多选模式</li>
                <li>智能语义搜索和关键词搜索</li>
                <li>可筛选素材类型（视频/图片）</li>
                <li>Fuzziness控制匹配精度</li>
                <li>丰富的筛选和排序选项</li>
                <li>响应式网格和列表视图</li>
                <li>实时预览和播放功能</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-white mb-2">使用方法:</h4>
              <ul className="space-y-1 list-disc list-inside">
                <li>点击按钮打开素材选择器</li>
                <li>使用搜索框进行语义或关键词搜索</li>
                <li>调整Fuzziness滑块控制匹配精度</li>
                <li>使用筛选器缩小选择范围</li>
                <li>点击素材卡片进行选择</li>
                <li>多选模式下点击确认按钮完成选择</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AssetPickerDemo;