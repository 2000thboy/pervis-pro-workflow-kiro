import React from 'react';
import { 
  // 基础图标
  Film, Play, Pause, Stop, SkipBack, SkipForward, Volume2, VolumeX,
  // 文件和媒体
  FileText, Image, Video, Music, File, Folder, FolderOpen, Upload, Download,
  // 编辑和工具
  Edit, Trash2, Copy, Cut, Paste, Undo, Redo, Save, Settings, Search,
  // 导航和界面
  Menu, X, ChevronLeft, ChevronRight, ChevronUp, ChevronDown, ArrowLeft, ArrowRight,
  // 状态和反馈
  Check, AlertCircle, Info, AlertTriangle, Loader2, Clock, Calendar,
  // 用户和系统
  User, Users, Eye, EyeOff, Lock, Unlock, Shield, Server, Database,
  // 创作工具
  Layers, Grid, Layout, Maximize, Minimize, RotateCcw, RotateCw, Crop,
  // 通信和分享
  Share2, Link, Mail, MessageCircle, Bell, Heart, Star, Bookmark,
  // 其他
  Plus, Minus, MoreHorizontal, MoreVertical, Filter, Sort, Zap, Sparkles
} from 'lucide-react';

export interface IconProps {
  size?: number;
  className?: string;
  color?: string;
}

export interface IconButtonProps {
  icon: React.ComponentType<IconProps>;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  variant?: 'ghost' | 'filled' | 'outlined';
  active?: boolean;
  disabled?: boolean;
  tooltip?: string;
  onClick?: () => void;
  className?: string;
}

// 图标尺寸映射
const iconSizes = {
  xs: 12,
  sm: 16,
  md: 20,
  lg: 24
};

const buttonSizes = {
  xs: 'w-6 h-6',
  sm: 'w-8 h-8',
  md: 'w-10 h-10',
  lg: 'w-12 h-12'
};

// 图标按钮组件
export const IconButton: React.FC<IconButtonProps> = ({
  icon: Icon,
  size = 'md',
  variant = 'ghost',
  active = false,
  disabled = false,
  tooltip,
  onClick,
  className = ''
}) => {
  const iconSize = iconSizes[size];
  
  const baseStyles = `
    inline-flex items-center justify-center rounded-lg
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:ring-offset-2 focus:ring-offset-black
    disabled:opacity-50 disabled:cursor-not-allowed
    relative overflow-hidden
  `;
  
  const variantStyles = {
    ghost: `
      text-zinc-400 hover:text-white hover:bg-zinc-800/50
      ${active ? 'text-amber-500 bg-amber-500/10' : ''}
    `,
    filled: `
      bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white
      ${active ? 'bg-amber-500 text-black' : ''}
    `,
    outlined: `
      border border-zinc-700 text-zinc-400 hover:border-zinc-600 hover:text-white hover:bg-zinc-800/30
      ${active ? 'border-amber-500 text-amber-500 bg-amber-500/10' : ''}
    `
  };
  
  return (
    <button
      className={`
        ${baseStyles}
        ${buttonSizes[size]}
        ${variantStyles[variant]}
        ${className}
      `}
      onClick={onClick}
      disabled={disabled}
      title={tooltip}
    >
      <Icon size={iconSize} />
    </button>
  );
};

// 预定义图标组件
export const PlayIcon = (props: IconProps) => <Play {...props} />;
export const PauseIcon = (props: IconProps) => <Pause {...props} />;
export const StopIcon = (props: IconProps) => <Stop {...props} />;
export const FilmIcon = (props: IconProps) => <Film {...props} />;
export const VideoIcon = (props: IconProps) => <Video {...props} />;
export const ImageIcon = (props: IconProps) => <Image {...props} />;
export const MusicIcon = (props: IconProps) => <Music {...props} />;
export const FileIcon = (props: IconProps) => <File {...props} />;
export const FolderIcon = (props: IconProps) => <Folder {...props} />;
export const EditIcon = (props: IconProps) => <Edit {...props} />;
export const DeleteIcon = (props: IconProps) => <Trash2 {...props} />;
export const SaveIcon = (props: IconProps) => <Save {...props} />;
export const SearchIcon = (props: IconProps) => <Search {...props} />;
export const SettingsIcon = (props: IconProps) => <Settings {...props} />;
export const LoadingIcon = (props: IconProps) => <Loader2 className="animate-spin" {...props} />;
export const CheckIcon = (props: IconProps) => <Check {...props} />;
export const ErrorIcon = (props: IconProps) => <AlertCircle {...props} />;
export const WarningIcon = (props: IconProps) => <AlertTriangle {...props} />;
export const InfoIcon = (props: IconProps) => <Info {...props} />;
export const CloseIcon = (props: IconProps) => <X {...props} />;
export const MenuIcon = (props: IconProps) => <Menu {...props} />;
export const PlusIcon = (props: IconProps) => <Plus {...props} />;
export const MinusIcon = (props: IconProps) => <Minus {...props} />;
export const MoreIcon = (props: IconProps) => <MoreHorizontal {...props} />;
export const LayersIcon = (props: IconProps) => <Layers {...props} />;
export const GridIcon = (props: IconProps) => <Grid {...props} />;
export const LayoutIcon = (props: IconProps) => <Layout {...props} />;
export const ShareIcon = (props: IconProps) => <Share2 {...props} />;
export const LinkIcon = (props: IconProps) => <Link {...props} />;
export const UserIcon = (props: IconProps) => <User {...props} />;
export const UsersIcon = (props: IconProps) => <Users {...props} />;
export const EyeIcon = (props: IconProps) => <Eye {...props} />;
export const EyeOffIcon = (props: IconProps) => <EyeOff {...props} />;
export const LockIcon = (props: IconProps) => <Lock {...props} />;
export const UnlockIcon = (props: IconProps) => <Unlock {...props} />;
export const ServerIcon = (props: IconProps) => <Server {...props} />;
export const DatabaseIcon = (props: IconProps) => <Database {...props} />;
export const ClockIcon = (props: IconProps) => <Clock {...props} />;
export const CalendarIcon = (props: IconProps) => <Calendar {...props} />;
export const HeartIcon = (props: IconProps) => <Heart {...props} />;
export const StarIcon = (props: IconProps) => <Star {...props} />;
export const BookmarkIcon = (props: IconProps) => <Bookmark {...props} />;
export const ZapIcon = (props: IconProps) => <Zap {...props} />;
export const SparklesIcon = (props: IconProps) => <Sparkles {...props} />;

// 媒体控制图标组合
export const MediaControls = {
  Play: PlayIcon,
  Pause: PauseIcon,
  Stop: StopIcon,
  SkipBack: (props: IconProps) => <SkipBack {...props} />,
  SkipForward: (props: IconProps) => <SkipForward {...props} />,
  Volume: (props: IconProps) => <Volume2 {...props} />,
  Mute: (props: IconProps) => <VolumeX {...props} />
};

// 文件类型图标组合
export const FileTypeIcons = {
  Video: VideoIcon,
  Image: ImageIcon,
  Audio: MusicIcon,
  Text: (props: IconProps) => <FileText {...props} />,
  Generic: FileIcon,
  Folder: FolderIcon,
  FolderOpen: (props: IconProps) => <FolderOpen {...props} />
};

// 编辑工具图标组合
export const EditingIcons = {
  Edit: EditIcon,
  Delete: DeleteIcon,
  Copy: (props: IconProps) => <Copy {...props} />,
  Cut: (props: IconProps) => <Cut {...props} />,
  Paste: (props: IconProps) => <Paste {...props} />,
  Undo: (props: IconProps) => <Undo {...props} />,
  Redo: (props: IconProps) => <Redo {...props} />,
  Save: SaveIcon,
  Crop: (props: IconProps) => <Crop {...props} />,
  RotateLeft: (props: IconProps) => <RotateCcw {...props} />,
  RotateRight: (props: IconProps) => <RotateCw {...props} />
};

// 状态图标组合
export const StatusIcons = {
  Success: CheckIcon,
  Error: ErrorIcon,
  Warning: WarningIcon,
  Info: InfoIcon,
  Loading: LoadingIcon,
  Clock: ClockIcon
};

// 导航图标组合
export const NavigationIcons = {
  Menu: MenuIcon,
  Close: CloseIcon,
  Back: (props: IconProps) => <ArrowLeft {...props} />,
  Forward: (props: IconProps) => <ArrowRight {...props} />,
  Up: (props: IconProps) => <ChevronUp {...props} />,
  Down: (props: IconProps) => <ChevronDown {...props} />,
  Left: (props: IconProps) => <ChevronLeft {...props} />,
  Right: (props: IconProps) => <ChevronRight {...props} />
};

// 工具图标组合
export const ToolIcons = {
  Search: SearchIcon,
  Settings: SettingsIcon,
  Filter: (props: IconProps) => <Filter {...props} />,
  Sort: (props: IconProps) => <Sort {...props} />,
  Layers: LayersIcon,
  Grid: GridIcon,
  Layout: LayoutIcon,
  Maximize: (props: IconProps) => <Maximize {...props} />,
  Minimize: (props: IconProps) => <Minimize {...props} />,
  Upload: (props: IconProps) => <Upload {...props} />,
  Download: (props: IconProps) => <Download {...props} />
};

// 图标工具函数
export const getFileTypeIcon = (filename: string): React.ComponentType<IconProps> => {
  const ext = filename.split('.').pop()?.toLowerCase();
  
  switch (ext) {
    case 'mp4':
    case 'avi':
    case 'mov':
    case 'mkv':
    case 'webm':
      return VideoIcon;
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'webp':
    case 'svg':
      return ImageIcon;
    case 'mp3':
    case 'wav':
    case 'flac':
    case 'aac':
    case 'ogg':
      return MusicIcon;
    case 'txt':
    case 'md':
    case 'doc':
    case 'docx':
      return (props: IconProps) => <FileText {...props} />;
    default:
      return FileIcon;
  }
};

// 导出所有图标
export {
  // Lucide 原始图标
  Film, Play, Pause, Stop, SkipBack, SkipForward, Volume2, VolumeX,
  FileText, Image, Video, Music, File, Folder, FolderOpen, Upload, Download,
  Edit, Trash2, Copy, Cut, Paste, Undo, Redo, Save, Settings, Search,
  Menu, X, ChevronLeft, ChevronRight, ChevronUp, ChevronDown, ArrowLeft, ArrowRight,
  Check, AlertCircle, Info, AlertTriangle, Loader2, Clock, Calendar,
  User, Users, Eye, EyeOff, Lock, Unlock, Shield, Server, Database,
  Layers, Grid, Layout, Maximize, Minimize, RotateCcw, RotateCw, Crop,
  Share2, Link, Mail, MessageCircle, Bell, Heart, Star, Bookmark,
  Plus, Minus, MoreHorizontal, MoreVertical, Filter, Sort, Zap, Sparkles
};

export default IconButton;