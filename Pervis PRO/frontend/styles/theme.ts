/**
 * Pervis PRO 专业导演工作台主题系统
 * 电影级视觉质感的深色主题配置
 */

export const theme = {
  // 色彩系统 - 专业深色主题
  colors: {
    // 主背景色系 - 深黑专业主题
    background: {
      primary: '#0a0a0a',      // 主背景 - 纯黑
      secondary: '#1a1a1a',    // 次级背景 - 深灰
      tertiary: '#2a2a2a',     // 三级背景 - 中灰
      elevated: '#1f1f1f',     // 悬浮元素背景
      card: '#151515',         // 卡片背景
      overlay: 'rgba(0, 0, 0, 0.8)', // 遮罩背景
    },
    
    // 品牌色系 - 金黄色专业配色
    brand: {
      primary: '#f59e0b',      // 主品牌色 - 琥珀色
      secondary: '#fbbf24',    // 次品牌色 - 亮黄
      accent: '#92400e',       // 强调色 - 深琥珀
      light: '#fef3c7',       // 浅色变体
      dark: '#78350f',        // 深色变体
    },
    
    // 功能语义色
    semantic: {
      success: '#10b981',      // 成功 - 翠绿
      warning: '#f59e0b',      // 警告 - 橙黄
      error: '#ef4444',        // 错误 - 红色
      info: '#3b82f6',         // 信息 - 蓝色
      processing: '#8b5cf6',   // 处理中 - 紫色
    },
    
    // 文本色系
    text: {
      primary: '#ffffff',      // 主文本 - 纯白
      secondary: '#e5e7eb',    // 次文本 - 浅灰
      tertiary: '#9ca3af',     // 三级文本 - 中灰
      quaternary: '#6b7280',   // 四级文本 - 深灰
      disabled: '#4b5563',     // 禁用文本
      inverse: '#000000',      // 反色文本
    },
    
    // 边框色系
    border: {
      primary: '#374151',      // 主边框
      secondary: '#4b5563',    // 次边框
      accent: '#f59e0b',       // 强调边框
      subtle: '#1f2937',      // 微妙边框
      focus: '#fbbf24',       // 焦点边框
    },
    
    // 状态色系
    state: {
      hover: 'rgba(245, 158, 11, 0.1)',     // 悬停状态
      active: 'rgba(245, 158, 11, 0.2)',    // 激活状态
      selected: 'rgba(245, 158, 11, 0.15)', // 选中状态
      disabled: 'rgba(107, 114, 128, 0.5)', // 禁用状态
    }
  },
  
  // 渐变系统
  gradients: {
    brand: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
    brandReverse: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
    subtle: 'linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%)',
    glow: 'radial-gradient(circle, rgba(245, 158, 11, 0.3) 0%, transparent 70%)',
    overlay: 'linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.8) 100%)',
  },
  
  // 阴影系统 - 电影级深度效果
  shadows: {
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    
    // 特殊效果阴影
    glow: '0 0 20px rgba(245, 158, 11, 0.3)',
    glowLarge: '0 0 40px rgba(245, 158, 11, 0.2)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    card: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(255, 255, 255, 0.05)',
    elevated: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
  },
  
  // 动画系统
  animations: {
    // 持续时间
    duration: {
      fast: '150ms',
      normal: '300ms',
      slow: '500ms',
      slower: '750ms',
    },
    
    // 缓动函数
    easing: {
      linear: 'linear',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      elastic: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
    },
    
    // 预定义动画
    fadeIn: 'fadeIn 300ms cubic-bezier(0, 0, 0.2, 1)',
    slideUp: 'slideUp 300ms cubic-bezier(0, 0, 0.2, 1)',
    slideDown: 'slideDown 300ms cubic-bezier(0, 0, 0.2, 1)',
    scaleIn: 'scaleIn 200ms cubic-bezier(0, 0, 0.2, 1)',
    glow: 'glow 2s ease-in-out infinite alternate',
  },
  
  // 断点系统 - 响应式设计
  breakpoints: {
    xs: '480px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  
  // 间距系统
  spacing: {
    px: '1px',
    0: '0',
    0.5: '0.125rem',  // 2px
    1: '0.25rem',     // 4px
    1.5: '0.375rem',  // 6px
    2: '0.5rem',      // 8px
    2.5: '0.625rem',  // 10px
    3: '0.75rem',     // 12px
    3.5: '0.875rem',  // 14px
    4: '1rem',        // 16px
    5: '1.25rem',     // 20px
    6: '1.5rem',      // 24px
    7: '1.75rem',     // 28px
    8: '2rem',        // 32px
    9: '2.25rem',     // 36px
    10: '2.5rem',     // 40px
    11: '2.75rem',    // 44px
    12: '3rem',       // 48px
    14: '3.5rem',     // 56px
    16: '4rem',       // 64px
    20: '5rem',       // 80px
    24: '6rem',       // 96px
    28: '7rem',       // 112px
    32: '8rem',       // 128px
  },
  
  // 圆角系统
  borderRadius: {
    none: '0',
    sm: '0.125rem',   // 2px
    md: '0.375rem',   // 6px
    lg: '0.5rem',     // 8px
    xl: '0.75rem',    // 12px
    '2xl': '1rem',    // 16px
    '3xl': '1.5rem',  // 24px
    full: '9999px',
  },
  
  // Z-index 层级系统
  zIndex: {
    hide: -1,
    auto: 'auto',
    base: 0,
    docked: 10,
    dropdown: 1000,
    sticky: 1100,
    banner: 1200,
    overlay: 1300,
    modal: 1400,
    popover: 1500,
    skipLink: 1600,
    toast: 1700,
    tooltip: 1800,
  }
} as const;

// 排版系统
export const typography = {
  // 字体族
  fonts: {
    sans: [
      '"Inter"',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif'
    ].join(', '),
    
    serif: [
      '"Playfair Display"',
      'Georgia',
      'Cambria',
      '"Times New Roman"',
      'Times',
      'serif'
    ].join(', '),
    
    mono: [
      '"JetBrains Mono"',
      '"Fira Code"',
      '"SF Mono"',
      'Monaco',
      'Inconsolata',
      '"Roboto Mono"',
      'monospace'
    ].join(', '),
  },
  
  // 字体大小
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],      // 12px
    sm: ['0.875rem', { lineHeight: '1.25rem' }],  // 14px
    base: ['1rem', { lineHeight: '1.5rem' }],     // 16px
    lg: ['1.125rem', { lineHeight: '1.75rem' }],  // 18px
    xl: ['1.25rem', { lineHeight: '1.75rem' }],   // 20px
    '2xl': ['1.5rem', { lineHeight: '2rem' }],    // 24px
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }], // 30px
    '4xl': ['2.25rem', { lineHeight: '2.5rem' }], // 36px
    '5xl': ['3rem', { lineHeight: '1' }],         // 48px
    '6xl': ['3.75rem', { lineHeight: '1' }],      // 60px
    '7xl': ['4.5rem', { lineHeight: '1' }],       // 72px
    '8xl': ['6rem', { lineHeight: '1' }],         // 96px
    '9xl': ['8rem', { lineHeight: '1' }],         // 128px
  },
  
  // 字体粗细
  fontWeight: {
    thin: '100',
    extralight: '200',
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
    black: '900',
  },
  
  // 行高
  lineHeight: {
    none: '1',
    tight: '1.25',
    snug: '1.375',
    normal: '1.5',
    relaxed: '1.625',
    loose: '2',
  },
  
  // 字母间距
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  }
} as const;

// 主题类型定义
export type Theme = typeof theme;
export type Typography = typeof typography;

// CSS变量生成器
export const generateCSSVariables = (theme: Theme) => {
  const cssVars: Record<string, string> = {};
  
  // 递归处理嵌套对象
  const processObject = (obj: any, prefix = '') => {
    Object.entries(obj).forEach(([key, value]) => {
      const varName = prefix ? `${prefix}-${key}` : key;
      
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        processObject(value, varName);
      } else {
        cssVars[`--${varName}`] = String(value);
      }
    });
  };
  
  processObject(theme);
  return cssVars;
};

// 默认导出
export default theme;