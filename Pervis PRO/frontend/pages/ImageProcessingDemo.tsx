import React from 'react';
import { ImageManager } from '../components/ImageProcessing';

const ImageProcessingDemo: React.FC = () => {
  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            PreVis PRO - 图片处理系统
          </h1>
          <p className="text-zinc-400">
            智能图片管理、分析和搜索系统演示
          </p>
        </div>

        <ImageManager projectId="demo-project" />
      </div>
    </div>
  );
};

export default ImageProcessingDemo;