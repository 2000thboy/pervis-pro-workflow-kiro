import React, { useState } from 'react';
import { Plus, Search, Image as ImageIcon, Video } from 'lucide-react';
import { Button, ButtonProps } from '../ui/Button';
import AssetPickerModal, { Asset, SearchResult } from './AssetPickerModal';

export interface AssetPickerButtonProps extends Omit<ButtonProps, 'onClick'> {
  projectId?: string;
  beatContent?: string;
  beatTags?: {
    emotion_tags?: string[];
    scene_tags?: string[];
    action_tags?: string[];
    cinematography_tags?: string[];
  };
  onSelect: (asset: Asset | SearchResult) => void;
  onMultiSelect?: (assets: (Asset | SearchResult)[]) => void;
  allowMultiSelect?: boolean;
  assetTypes?: ('video' | 'image')[];
  modalTitle?: string;
  modalSubtitle?: string;
  buttonText?: string;
  buttonIcon?: React.ComponentType<{ size?: number; className?: string }>;
}

export const AssetPickerButton: React.FC<AssetPickerButtonProps> = ({
  projectId,
  beatContent,
  beatTags,
  onSelect,
  onMultiSelect,
  allowMultiSelect = false,
  assetTypes = ['video', 'image'],
  modalTitle,
  modalSubtitle,
  buttonText,
  buttonIcon,
  ...buttonProps
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 默认按钮文本和图标
  const defaultButtonText = buttonText || (
    allowMultiSelect ? '选择素材' : '添加素材'
  );
  
  const defaultButtonIcon = buttonIcon || (
    assetTypes.length === 1 
      ? assetTypes[0] === 'video' ? Video : ImageIcon
      : Search
  );

  // 默认模态窗口标题
  const defaultModalTitle = modalTitle || (
    assetTypes.length === 1
      ? `选择${assetTypes[0] === 'video' ? '视频' : '图片'}`
      : '选择素材'
  );

  const handleSelect = (asset: Asset | SearchResult) => {
    onSelect(asset);
    setIsModalOpen(false);
  };

  const handleMultiSelect = (assets: (Asset | SearchResult)[]) => {
    if (onMultiSelect) {
      onMultiSelect(assets);
    }
    setIsModalOpen(false);
  };

  return (
    <>
      <Button
        {...buttonProps}
        icon={defaultButtonIcon}
        onClick={() => setIsModalOpen(true)}
      >
        {defaultButtonText}
      </Button>

      <AssetPickerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSelect={handleSelect}
        onMultiSelect={allowMultiSelect ? handleMultiSelect : undefined}
        title={defaultModalTitle}
        subtitle={modalSubtitle}
        projectId={projectId}
        beatContent={beatContent}
        beatTags={beatTags}
        allowMultiSelect={allowMultiSelect}
        assetTypes={assetTypes}
      />
    </>
  );
};

export default AssetPickerButton;