/**
 * Pervis PRO 布局组件
 * 专业导演工作台的布局系统
 */

// 主布局
export {
  MainLayout,
  LayoutProvider,
  LayoutContext,
  useLayout,
  type LayoutState,
  type MainLayoutProps
} from './MainLayout';

// 全局头部
export {
  GlobalHeader,
  ProjectHeader,
  WorkflowHeader,
  type BreadcrumbItem,
  type GlobalHeaderProps
} from './GlobalHeader';