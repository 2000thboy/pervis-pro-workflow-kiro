import React from 'react';
import ReactDOM from 'react-dom/client';

const SimpleApp = () => {
  return (
    <div style={{ 
      background: '#000', 
      color: '#fff', 
      padding: '20px', 
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>🎬 PreVis Pro 简单测试</h1>
      <p>如果你能看到这个页面，说明React正在工作！</p>
      <p>时间: {new Date().toLocaleString()}</p>
      <button 
        onClick={() => alert('React事件处理正常！')}
        style={{
          background: '#f59e0b',
          color: '#000',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        测试按钮
      </button>
    </div>
  );
};

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<SimpleApp />);
} else {
  console.error('Root element not found!');
}