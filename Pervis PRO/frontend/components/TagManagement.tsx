/**
 * 标签管理页面
 * 支持标签层级可视化、拖拽编辑、权重调整
 */

import React, { useState, useEffect } from 'react';
import { 
  getVideoTags, 
  updateTagHierarchy, 
  updateTagWeight, 
  batchUpdateTags 
} from '../services/apiClient';

// 标签节点接口
interface TagNode {
  id: string;
  name: string;
  category: string;
  weight: number;
  parent_id: string | null;
  order: number;
  children: TagNode[];
}

// 标签管理页面组件
export const TagManagement: React.FC<{ assetId: string }> = ({ assetId }) => {
  const [tags, setTags] = useState<TagNode[]>([]);
  const [selectedTag, setSelectedTag] = useState<TagNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载标签数据
  useEffect(() => {
    loadTags();
  }, [assetId]);

  const loadTags = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getVideoTags(assetId);
      
      if (response.status === 'success') {
        setTags(response.tags);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载标签失败');
    } finally {
      setLoading(false);
    }
  };

  // 更新标签权重
  const handleWeightChange = async (tagId: string, newWeight: number) => {
    try {
      setSaving(true);
      await updateTagWeight({
        asset_id: assetId,
        tag_id: tagId,
        weight: newWeight
      });
      
      // 更新本地状态
      setTags(prevTags => updateTagInTree(prevTags, tagId, { weight: newWeight }));
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新权重失败');
    } finally {
      setSaving(false);
    }
  };

  // 更新标签层级
  const handleHierarchyChange = async (
    tagId: string, 
    newParentId: string | null, 
    newOrder: number
  ) => {
    try {
      setSaving(true);
      await updateTagHierarchy({
        asset_id: assetId,
        tag_id: tagId,
        parent_id: newParentId,
        order: newOrder
      });
      
      await loadTags(); // 重新加载以获取最新层级
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新层级失败');
    } finally {
      setSaving(false);
    }
  };

  // 递归更新标签树中的节点
  const updateTagInTree = (
    nodes: TagNode[], 
    tagId: string, 
    updates: Partial<TagNode>
  ): TagNode[] => {
    return nodes.map(node => {
      if (node.id === tagId) {
        return { ...node, ...updates };
      }
      if (node.children.length > 0) {
        return {
          ...node,
          children: updateTagInTree(node.children, tagId, updates)
        };
      }
      return node;
    });
  };

  // 渲染标签树
  const renderTagTree = (nodes: TagNode[], level: number = 0) => {
    return nodes.map(node => (
      <div key={node.id} style={{ marginLeft: `${level * 20}px` }}>
        <TagNodeItem
          node={node}
          selected={selectedTag?.id === node.id}
          onSelect={() => setSelectedTag(node)}
          onWeightChange={(weight) => handleWeightChange(node.id, weight)}
          onMove={(parentId, order) => handleHierarchyChange(node.id, parentId, order)}
        />
        {node.children.length > 0 && renderTagTree(node.children, level + 1)}
      </div>
    ));
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>加载标签数据中...</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>标签管理</h2>
        <button 
          onClick={loadTags} 
          style={styles.refreshButton}
          disabled={saving}
        >
          刷新
        </button>
      </div>

      {error && (
        <div style={styles.error}>
          {error}
          <button onClick={() => setError(null)} style={styles.closeError}>×</button>
        </div>
      )}

      <div style={styles.content}>
        <div style={styles.treePanel}>
          <h3 style={styles.panelTitle}>标签层级树</h3>
          <div style={styles.tree}>
            {tags.length > 0 ? renderTagTree(tags) : (
              <div style={styles.emptyState}>暂无标签数据</div>
            )}
          </div>
        </div>

        <div style={styles.detailPanel}>
          <h3 style={styles.panelTitle}>标签详情</h3>
          {selectedTag ? (
            <TagDetail 
              tag={selectedTag} 
              onWeightChange={(weight) => handleWeightChange(selectedTag.id, weight)}
            />
          ) : (
            <div style={styles.emptyState}>请选择一个标签查看详情</div>
          )}
        </div>
      </div>

      {saving && (
        <div style={styles.savingOverlay}>
          <div style={styles.savingMessage}>保存中...</div>
        </div>
      )}
    </div>
  );
};

// 标签节点项组件
const TagNodeItem: React.FC<{
  node: TagNode;
  selected: boolean;
  onSelect: () => void;
  onWeightChange: (weight: number) => void;
  onMove: (parentId: string | null, order: number) => void;
}> = ({ node, selected, onSelect, onWeightChange }) => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <div
      style={{
        ...styles.tagNode,
        ...(selected ? styles.tagNodeSelected : {}),
        ...(isDragging ? styles.tagNodeDragging : {})
      }}
      onClick={onSelect}
      draggable
      onDragStart={() => setIsDragging(true)}
      onDragEnd={() => setIsDragging(false)}
    >
      <span style={styles.tagName}>{node.name}</span>
      <span style={styles.tagCategory}>({node.category})</span>
      <input
        type="range"
        min="0"
        max="1"
        step="0.1"
        value={node.weight}
        onChange={(e) => onWeightChange(parseFloat(e.target.value))}
        style={styles.weightSlider}
        onClick={(e) => e.stopPropagation()}
      />
      <span style={styles.weightValue}>{node.weight.toFixed(1)}</span>
    </div>
  );
};

// 标签详情组件
const TagDetail: React.FC<{
  tag: TagNode;
  onWeightChange: (weight: number) => void;
}> = ({ tag, onWeightChange }) => {
  return (
    <div style={styles.detail}>
      <div style={styles.detailRow}>
        <label style={styles.detailLabel}>标签名称:</label>
        <span style={styles.detailValue}>{tag.name}</span>
      </div>
      <div style={styles.detailRow}>
        <label style={styles.detailLabel}>分类:</label>
        <span style={styles.detailValue}>{tag.category}</span>
      </div>
      <div style={styles.detailRow}>
        <label style={styles.detailLabel}>权重:</label>
        <input
          type="number"
          min="0"
          max="1"
          step="0.1"
          value={tag.weight}
          onChange={(e) => onWeightChange(parseFloat(e.target.value))}
          style={styles.weightInput}
        />
      </div>
      <div style={styles.detailRow}>
        <label style={styles.detailLabel}>顺序:</label>
        <span style={styles.detailValue}>{tag.order}</span>
      </div>
      <div style={styles.detailRow}>
        <label style={styles.detailLabel}>父标签:</label>
        <span style={styles.detailValue}>{tag.parent_id || '无'}</span>
      </div>
      <div style={styles.detailRow}>
        <label style={styles.detailLabel}>子标签数:</label>
        <span style={styles.detailValue}>{tag.children.length}</span>
      </div>
    </div>
  );
};

// 样式定义
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    width: '100%',
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f5f5f5',
    fontFamily: 'Arial, sans-serif'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px',
    backgroundColor: '#fff',
    borderBottom: '1px solid #e0e0e0'
  },
  title: {
    margin: 0,
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#333'
  },
  refreshButton: {
    padding: '8px 16px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  content: {
    flex: 1,
    display: 'flex',
    gap: '20px',
    padding: '20px',
    overflow: 'hidden'
  },
  treePanel: {
    flex: 2,
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '20px',
    overflow: 'auto',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  detailPanel: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '20px',
    overflow: 'auto',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  panelTitle: {
    margin: '0 0 20px 0',
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#333',
    borderBottom: '2px solid #4CAF50',
    paddingBottom: '10px'
  },
  tree: {
    marginTop: '10px'
  },
  tagNode: {
    display: 'flex',
    alignItems: 'center',
    padding: '10px',
    marginBottom: '5px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: '1px solid transparent'
  },
  tagNodeSelected: {
    backgroundColor: '#e3f2fd',
    border: '1px solid #2196F3'
  },
  tagNodeDragging: {
    opacity: 0.5
  },
  tagName: {
    flex: 1,
    fontWeight: 'bold',
    color: '#333'
  },
  tagCategory: {
    marginLeft: '10px',
    color: '#666',
    fontSize: '12px'
  },
  weightSlider: {
    width: '100px',
    marginLeft: '10px'
  },
  weightValue: {
    marginLeft: '10px',
    minWidth: '30px',
    textAlign: 'right',
    color: '#666',
    fontSize: '14px'
  },
  detail: {
    marginTop: '10px'
  },
  detailRow: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '15px',
    padding: '10px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px'
  },
  detailLabel: {
    fontWeight: 'bold',
    minWidth: '100px',
    color: '#555'
  },
  detailValue: {
    flex: 1,
    color: '#333'
  },
  weightInput: {
    flex: 1,
    padding: '5px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px'
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    fontSize: '18px',
    color: '#666'
  },
  error: {
    margin: '20px',
    padding: '15px',
    backgroundColor: '#ffebee',
    color: '#c62828',
    borderRadius: '4px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  closeError: {
    background: 'none',
    border: 'none',
    fontSize: '20px',
    cursor: 'pointer',
    color: '#c62828'
  },
  emptyState: {
    textAlign: 'center',
    padding: '40px',
    color: '#999',
    fontSize: '16px'
  },
  savingOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000
  },
  savingMessage: {
    padding: '20px 40px',
    backgroundColor: '#fff',
    borderRadius: '8px',
    fontSize: '18px',
    fontWeight: 'bold'
  }
};

export default TagManagement;
