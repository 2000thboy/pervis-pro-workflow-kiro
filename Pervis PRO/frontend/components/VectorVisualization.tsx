/**
 * 向量可视化页面
 * 支持相似度搜索测试、匹配解释、向量空间可视化
 */

import React, { useState, useEffect } from 'react';
import {
  calculateSimilarity,
  explainMatch,
  saveTestCase,
  getTestCases
} from '../services/apiClient';

// 搜索结果接口
interface SearchResult {
  asset_id: string;
  filename: string;
  similarity_score: number;
  matched_tags: string[];
  explanation: string;
}

// 测试案例接口
interface TestCase {
  id: string;
  name: string;
  query: string;
  status: string;
  expected_count: number;
  actual_count: number;
  created_at: string;
}

// 向量可视化页面组件
export const VectorVisualization: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [explanation, setExplanation] = useState<string>('');
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState(10);

  // 加载测试案例
  useEffect(() => {
    loadTestCases();
  }, []);

  const loadTestCases = async () => {
    try {
      const response = await getTestCases();
      if (response.status === 'success') {
        setTestCases(response.test_cases);
      }
    } catch (err) {
      console.error('加载测试案例失败:', err);
    }
  };

  // 执行搜索
  const handleSearch = async () => {
    if (!query.trim()) {
      setError('请输入搜索查询');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await calculateSimilarity({
        query: query.trim(),
        top_k: topK
      });

      if (response.status === 'success') {
        setResults(response.results);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败');
    } finally {
      setLoading(false);
    }
  };

  // 解释匹配结果
  const handleExplain = async (assetId: string) => {
    try {
      setLoading(true);
      
      const response = await explainMatch({
        query: query.trim(),
        asset_id: assetId
      });

      if (response.status === 'success') {
        setExplanation(response.explanation);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取解释失败');
    } finally {
      setLoading(false);
    }
  };

  // 保存为测试案例
  const handleSaveTestCase = async () => {
    const name = prompt('请输入测试案例名称:');
    if (!name) return;

    try {
      const expectedResults = results.slice(0, 5).map(r => r.asset_id);
      
      await saveTestCase({
        name,
        query: query.trim(),
        expected_results: expectedResults
      });

      alert('测试案例保存成功');
      loadTestCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存测试案例失败');
    }
  };

  // 选择结果并获取解释
  const handleSelectResult = (result: SearchResult) => {
    setSelectedResult(result);
    handleExplain(result.asset_id);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>向量搜索测试</h2>
      </div>

      {error && (
        <div style={styles.error}>
          {error}
          <button onClick={() => setError(null)} style={styles.closeError}>×</button>
        </div>
      )}

      <div style={styles.content}>
        {/* 搜索面板 */}
        <div style={styles.searchPanel}>
          <h3 style={styles.panelTitle}>搜索查询</h3>
          
          <div style={styles.searchBox}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="输入搜索查询..."
              style={styles.searchInput}
            />
            <button 
              onClick={handleSearch} 
              disabled={loading}
              style={styles.searchButton}
            >
              {loading ? '搜索中...' : '搜索'}
            </button>
          </div>

          <div style={styles.searchOptions}>
            <label style={styles.optionLabel}>
              返回结果数:
              <input
                type="number"
                min="1"
                max="50"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                style={styles.optionInput}
              />
            </label>
            <button 
              onClick={handleSaveTestCase}
              disabled={results.length === 0}
              style={styles.saveButton}
            >
              保存为测试案例
            </button>
          </div>

          {/* 搜索结果列表 */}
          <div style={styles.resultsSection}>
            <h4 style={styles.sectionTitle}>
              搜索结果 ({results.length})
            </h4>
            <div style={styles.resultsList}>
              {results.map((result, index) => (
                <ResultCard
                  key={result.asset_id}
                  result={result}
                  index={index}
                  selected={selectedResult?.asset_id === result.asset_id}
                  onSelect={() => handleSelectResult(result)}
                />
              ))}
              {results.length === 0 && !loading && (
                <div style={styles.emptyState}>
                  输入查询并点击搜索按钮开始测试
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 详情面板 */}
        <div style={styles.detailPanel}>
          <h3 style={styles.panelTitle}>匹配解释</h3>
          
          {selectedResult ? (
            <div style={styles.explanationSection}>
              <div style={styles.resultInfo}>
                <div style={styles.infoRow}>
                  <span style={styles.infoLabel}>资产ID:</span>
                  <span style={styles.infoValue}>{selectedResult.asset_id}</span>
                </div>
                <div style={styles.infoRow}>
                  <span style={styles.infoLabel}>文件名:</span>
                  <span style={styles.infoValue}>{selectedResult.filename}</span>
                </div>
                <div style={styles.infoRow}>
                  <span style={styles.infoLabel}>相似度:</span>
                  <span style={styles.scoreValue}>
                    {(selectedResult.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div style={styles.tagsSection}>
                <h4 style={styles.sectionTitle}>匹配标签</h4>
                <div style={styles.tagsList}>
                  {selectedResult.matched_tags.map((tag, i) => (
                    <span key={i} style={styles.tag}>{tag}</span>
                  ))}
                </div>
              </div>

              <div style={styles.explanationText}>
                <h4 style={styles.sectionTitle}>详细解释</h4>
                <p style={styles.explanation}>
                  {explanation || '加载解释中...'}
                </p>
              </div>

              {/* 相似度可视化 */}
              <div style={styles.visualizationSection}>
                <h4 style={styles.sectionTitle}>相似度分布</h4>
                <SimilarityChart results={results} selectedId={selectedResult.asset_id} />
              </div>
            </div>
          ) : (
            <div style={styles.emptyState}>
              点击搜索结果查看详细解释
            </div>
          )}
        </div>

        {/* 测试案例面板 */}
        <div style={styles.testCasesPanel}>
          <h3 style={styles.panelTitle}>测试案例</h3>
          <div style={styles.testCasesList}>
            {testCases.map((testCase) => (
              <TestCaseCard
                key={testCase.id}
                testCase={testCase}
                onSelect={() => setQuery(testCase.query)}
              />
            ))}
            {testCases.length === 0 && (
              <div style={styles.emptyState}>暂无测试案例</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// 搜索结果卡片组件
const ResultCard: React.FC<{
  result: SearchResult;
  index: number;
  selected: boolean;
  onSelect: () => void;
}> = ({ result, index, selected, onSelect }) => {
  return (
    <div
      style={{
        ...styles.resultCard,
        ...(selected ? styles.resultCardSelected : {})
      }}
      onClick={onSelect}
    >
      <div style={styles.resultHeader}>
        <span style={styles.resultRank}>#{index + 1}</span>
        <span style={styles.resultScore}>
          {(result.similarity_score * 100).toFixed(1)}%
        </span>
      </div>
      <div style={styles.resultFilename}>{result.filename}</div>
      <div style={styles.resultTags}>
        {result.matched_tags.slice(0, 3).map((tag, i) => (
          <span key={i} style={styles.miniTag}>{tag}</span>
        ))}
      </div>
    </div>
  );
};

// 测试案例卡片组件
const TestCaseCard: React.FC<{
  testCase: TestCase;
  onSelect: () => void;
}> = ({ testCase, onSelect }) => {
  return (
    <div style={styles.testCaseCard} onClick={onSelect}>
      <div style={styles.testCaseName}>{testCase.name}</div>
      <div style={styles.testCaseQuery}>{testCase.query}</div>
      <div style={styles.testCaseStats}>
        <span>期望: {testCase.expected_count}</span>
        <span>实际: {testCase.actual_count}</span>
        <span style={
          testCase.status === 'passed' 
            ? styles.statusPassed 
            : styles.statusFailed
        }>
          {testCase.status}
        </span>
      </div>
    </div>
  );
};

// 相似度图表组件
const SimilarityChart: React.FC<{
  results: SearchResult[];
  selectedId: string;
}> = ({ results, selectedId }) => {
  const maxScore = Math.max(...results.map(r => r.similarity_score), 0.1);
  
  return (
    <div style={styles.chart}>
      {results.slice(0, 10).map((result, index) => {
        const barWidth = (result.similarity_score / maxScore) * 100;
        const isSelected = result.asset_id === selectedId;
        
        return (
          <div key={result.asset_id} style={styles.chartRow}>
            <span style={styles.chartLabel}>#{index + 1}</span>
            <div style={styles.chartBarContainer}>
              <div
                style={{
                  ...styles.chartBar,
                  width: `${barWidth}%`,
                  backgroundColor: isSelected ? '#2196F3' : '#4CAF50'
                }}
              />
            </div>
            <span style={styles.chartValue}>
              {(result.similarity_score * 100).toFixed(1)}%
            </span>
          </div>
        );
      })}
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
  content: {
    flex: 1,
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 300px',
    gap: '20px',
    padding: '20px',
    overflow: 'hidden'
  },
  searchPanel: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  detailPanel: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '20px',
    overflow: 'auto',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  testCasesPanel: {
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
  searchBox: {
    display: 'flex',
    gap: '10px',
    marginBottom: '15px'
  },
  searchInput: {
    flex: 1,
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px'
  },
  searchButton: {
    padding: '10px 20px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold'
  },
  searchOptions: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    padding: '10px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px'
  },
  optionLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '14px',
    color: '#555'
  },
  optionInput: {
    width: '60px',
    padding: '5px',
    border: '1px solid #ddd',
    borderRadius: '4px'
  },
  saveButton: {
    padding: '8px 16px',
    backgroundColor: '#2196F3',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  resultsSection: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  sectionTitle: {
    margin: '0 0 10px 0',
    fontSize: '16px',
    fontWeight: 'bold',
    color: '#555'
  },
  resultsList: {
    flex: 1,
    overflow: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px'
  },
  resultCard: {
    padding: '15px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: '1px solid transparent'
  },
  resultCardSelected: {
    backgroundColor: '#e3f2fd',
    border: '1px solid #2196F3'
  },
  resultHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px'
  },
  resultRank: {
    fontWeight: 'bold',
    color: '#666'
  },
  resultScore: {
    fontWeight: 'bold',
    color: '#4CAF50',
    fontSize: '16px'
  },
  resultFilename: {
    marginBottom: '8px',
    color: '#333',
    fontSize: '14px'
  },
  resultTags: {
    display: 'flex',
    gap: '5px',
    flexWrap: 'wrap'
  },
  miniTag: {
    padding: '2px 8px',
    backgroundColor: '#e0e0e0',
    borderRadius: '12px',
    fontSize: '12px',
    color: '#555'
  },
  explanationSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px'
  },
  resultInfo: {
    padding: '15px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px'
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '10px'
  },
  infoLabel: {
    fontWeight: 'bold',
    color: '#555'
  },
  infoValue: {
    color: '#333'
  },
  scoreValue: {
    fontWeight: 'bold',
    color: '#4CAF50',
    fontSize: '18px'
  },
  tagsSection: {
    padding: '15px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px'
  },
  tagsList: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap'
  },
  tag: {
    padding: '5px 12px',
    backgroundColor: '#4CAF50',
    color: 'white',
    borderRadius: '16px',
    fontSize: '14px'
  },
  explanationText: {
    padding: '15px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px'
  },
  explanation: {
    margin: 0,
    lineHeight: '1.6',
    color: '#333'
  },
  visualizationSection: {
    padding: '15px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px'
  },
  chart: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  },
  chartRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },
  chartLabel: {
    minWidth: '30px',
    fontSize: '12px',
    color: '#666'
  },
  chartBarContainer: {
    flex: 1,
    height: '20px',
    backgroundColor: '#e0e0e0',
    borderRadius: '10px',
    overflow: 'hidden'
  },
  chartBar: {
    height: '100%',
    transition: 'width 0.3s'
  },
  chartValue: {
    minWidth: '50px',
    textAlign: 'right',
    fontSize: '12px',
    fontWeight: 'bold',
    color: '#555'
  },
  testCasesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px'
  },
  testCaseCard: {
    padding: '15px',
    backgroundColor: '#f9f9f9',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: '1px solid transparent'
  },
  testCaseName: {
    fontWeight: 'bold',
    marginBottom: '5px',
    color: '#333'
  },
  testCaseQuery: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '10px'
  },
  testCaseStats: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    color: '#888'
  },
  statusPassed: {
    color: '#4CAF50',
    fontWeight: 'bold'
  },
  statusFailed: {
    color: '#f44336',
    fontWeight: 'bold'
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
  }
};

export default VectorVisualization;
