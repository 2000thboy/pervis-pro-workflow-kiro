import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    const isProduction = mode === 'production';
    
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      plugins: [react()],
      define: {
        'import.meta.env.VITE_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'import.meta.env.VITE_GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      build: {
        // 启用代码分割
        rollupOptions: {
          output: {
            manualChunks: {
              // React相关库单独打包
              'react-vendor': ['react', 'react-dom', 'react-router-dom'],
              // UI组件库单独打包
              'ui-vendor': ['lucide-react'],
            },
            // 优化chunk文件名
            chunkFileNames: isProduction ? 'assets/js/[name]-[hash].js' : 'assets/js/[name].js',
            entryFileNames: isProduction ? 'assets/js/[name]-[hash].js' : 'assets/js/[name].js',
            assetFileNames: isProduction ? 'assets/[ext]/[name]-[hash].[ext]' : 'assets/[ext]/[name].[ext]'
          }
        },
        // 启用压缩
        minify: isProduction ? 'terser' : false,
        terserOptions: isProduction ? {
          compress: {
            drop_console: true,
            drop_debugger: true,
            pure_funcs: ['console.log', 'console.info', 'console.debug']
          },
          mangle: {
            safari10: true
          }
        } : undefined,
        // 设置chunk大小警告阈值
        chunkSizeWarningLimit: 1000,
        // 启用CSS代码分割
        cssCodeSplit: true,
        // 生成source map (开发环境)
        sourcemap: !isProduction,
        // 优化构建目标
        target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari13.1']
      },
      // 优化依赖预构建
      optimizeDeps: {
        include: [
          'react', 
          'react-dom', 
          'react-router-dom',
          'lucide-react'
        ],
        // 排除不需要预构建的依赖
        exclude: ['@vitejs/plugin-react']
      },
      // CSS配置 - 开发模式下简化配置
      css: {
        devSourcemap: !isProduction
      }
    };
});
