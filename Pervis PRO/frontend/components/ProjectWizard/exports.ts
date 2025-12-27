/**
 * 项目立项向导 - 导出文件
 */

// 主组件
export { ProjectWizard, default } from './index';

// 上下文
export { WizardProvider, useWizard } from './WizardContext';

// 类型
export * from './types';

// API
export { wizardApi } from './api';

// 步骤组件
export { WizardStep1_BasicInfo } from './WizardStep1_BasicInfo';
export { WizardStep2_Script } from './WizardStep2_Script';
export { WizardStep3_Characters } from './WizardStep3_Characters';
export { WizardStep4_Scenes } from './WizardStep4_Scenes';
export { WizardStep5_References } from './WizardStep5_References';
export { WizardStep6_Confirm } from './WizardStep6_Confirm';

// 辅助组件
export { AgentStatusPanel } from './AgentStatusPanel';
export { VersionHistoryPanel } from './VersionHistoryPanel';
export { CandidateSwitcher } from './CandidateSwitcher';
export { MissingContentDialog } from './MissingContentDialog';
export { MarketAnalysisPanel } from './MarketAnalysisPanel';
export { 
  DataTypeIndicator, 
  DataSourceBadges, 
  ContentSource, 
  DataTypeLegend 
} from './DataTypeIndicator';
export type { DataType } from './DataTypeIndicator';
