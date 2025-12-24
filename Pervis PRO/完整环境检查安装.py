#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pervis PRO 完整环境检查和安装脚本
自动检查并安装所有必需的组件
"""

import os
import sys
import subprocess
import json
import time
import urllib.request
import shutil
from pathlib import Path
import platform

class PervisInstaller:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.install_log = []
        self.status = {
            'python': False,
            'nodejs': False,
            'git': False,
            'ffmpeg': False,
            'ollama': False,
            'backend_deps': False,
            'frontend_deps': False,
            'launcher_deps': False,
            'ai_models': False
        }
        
    def log(self, message):
        """记录日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.install_log.append(log_entry)
        
    def run_command(self, command, shell=True, capture_output=True):
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                command, 
                shell=shell, 
                capture_output=capture_output, 
                text=True,
                timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_python(self):
        """检查Python安装"""
        self.log("检查Python...")
        success, stdout, stderr = self.run_command("python --version")
        if success and "Python 3." in stdout:
            version = stdout.strip()
            self.log(f"Python已安装: {version}")
            self.status['python'] = True
            return True
        
        # 尝试python3命令
        success, stdout, stderr = self.run_command("python3 --version")
        if success and "Python 3." in stdout:
            version = stdout.strip()
            self.log(f"Python已安装: {version}")
            self.status['python'] = True
            return True
            
        self.log("Python未安装或版本不正确")
        return False
    
    def check_nodejs(self):
        """检查Node.js安装"""
        self.log("检查Node.js...")
        success, stdout, stderr = self.run_command("node --version")
        if success and stdout.strip().startswith('v'):
            version = stdout.strip()
            self.log(f"Node.js已安装: {version}")
            self.status['nodejs'] = True
            return True
        
        self.log("Node.js未安装")
        return False
    
    def check_git(self):
        """检查Git安装"""
        self.log("检查Git...")
        success, stdout, stderr = self.run_command("git --version")
        if success and "git version" in stdout:
            version = stdout.strip()
            self.log(f"Git已安装: {version}")
            self.status['git'] = True
            return True
        
        self.log("Git未安装")
        return False
    
    def check_ffmpeg(self):
        """检查FFmpeg安装"""
        self.log("检查FFmpeg...")
        success, stdout, stderr = self.run_command("ffmpeg -version")
        if success and "ffmpeg version" in stdout:
            version_line = stdout.split('\n')[0]
            self.log(f"FFmpeg已安装: {version_line}")
            self.status['ffmpeg'] = True
            return True
        
        self.log("FFmpeg未安装")
        return False
    
    def check_ollama(self):
        """检查Ollama安装"""
        self.log("检查Ollama...")
        success, stdout, stderr = self.run_command("ollama --version")
        if success and "ollama version" in stdout:
            version = stdout.strip()
            self.log(f"Ollama已安装: {version}")
            self.status['ollama'] = True
            return True
        
        self.log("Ollama未安装")
        return False
    
    def install_nodejs_manual(self):
        """手动安装Node.js"""
        self.log("开始安装Node.js...")
        
        # 下载Node.js
        node_url = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
        node_installer = self.base_dir / "node_installer.msi"
        
        try:
            self.log("下载Node.js安装包...")
            urllib.request.urlretrieve(node_url, node_installer)
            self.log("Node.js下载完成")
            
            # 静默安装
            self.log("安装Node.js...")
            success, stdout, stderr = self.run_command(
                f'msiexec /i "{node_installer}" /quiet /norestart'
            )
            
            if success:
                self.log("Node.js安装完成")
                # 刷新环境变量
                self.refresh_env()
                time.sleep(5)
                return self.check_nodejs()
            else:
                self.log(f"Node.js安装失败: {stderr}")
                return False
                
        except Exception as e:
            self.log(f"Node.js安装异常: {str(e)}")
            return False
        finally:
            # 清理安装包
            if node_installer.exists():
                node_installer.unlink()
    
    def install_ffmpeg_manual(self):
        """手动安装FFmpeg"""
        self.log("开始安装FFmpeg...")
        
        # 创建FFmpeg目录
        ffmpeg_dir = self.base_dir / "ffmpeg"
        ffmpeg_dir.mkdir(exist_ok=True)
        
        # 下载FFmpeg
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        ffmpeg_zip = self.base_dir / "ffmpeg.zip"
        
        try:
            self.log("下载FFmpeg...")
            urllib.request.urlretrieve(ffmpeg_url, ffmpeg_zip)
            self.log("FFmpeg下载完成")
            
            # 解压
            self.log("解压FFmpeg...")
            import zipfile
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall(ffmpeg_dir)
            
            # 找到ffmpeg.exe并添加到PATH
            for root, dirs, files in os.walk(ffmpeg_dir):
                if 'ffmpeg.exe' in files:
                    ffmpeg_bin = Path(root)
                    self.log(f"找到FFmpeg: {ffmpeg_bin}")
                    
                    # 添加到系统PATH
                    self.add_to_path(str(ffmpeg_bin))
                    return self.check_ffmpeg()
            
            self.log("未找到ffmpeg.exe")
            return False
            
        except Exception as e:
            self.log(f"FFmpeg安装异常: {str(e)}")
            return False
        finally:
            # 清理压缩包
            if ffmpeg_zip.exists():
                ffmpeg_zip.unlink()
    
    def install_ollama_manual(self):
        """手动安装Ollama"""
        self.log("开始安装Ollama...")
        
        # 下载Ollama
        ollama_url = "https://ollama.com/download/OllamaSetup.exe"
        ollama_installer = self.base_dir / "OllamaSetup.exe"
        
        try:
            self.log("下载Ollama安装包...")
            urllib.request.urlretrieve(ollama_url, ollama_installer)
            self.log("Ollama下载完成")
            
            # 静默安装
            self.log("安装Ollama...")
            success, stdout, stderr = self.run_command(
                f'"{ollama_installer}" /S'
            )
            
            if success:
                self.log("Ollama安装完成")
                # 刷新环境变量
                self.refresh_env()
                time.sleep(5)
                
                # 启动Ollama服务
                self.log("启动Ollama服务...")
                self.run_command("ollama serve", capture_output=False)
                time.sleep(3)
                
                return self.check_ollama()
            else:
                self.log(f"Ollama安装失败: {stderr}")
                return False
                
        except Exception as e:
            self.log(f"Ollama安装异常: {str(e)}")
            return False
        finally:
            # 清理安装包
            if ollama_installer.exists():
                ollama_installer.unlink()
    
    def refresh_env(self):
        """刷新环境变量"""
        self.log("刷新环境变量...")
        self.run_command('powershell -Command "refreshenv"')
    
    def add_to_path(self, path):
        """添加路径到系统PATH"""
        try:
            current_path = os.environ.get('PATH', '')
            if path not in current_path:
                os.environ['PATH'] = f"{path};{current_path}"
                self.log(f"已添加到PATH: {path}")
        except Exception as e:
            self.log(f"添加PATH失败: {str(e)}")
    
    def install_python_deps(self):
        """安装Python依赖"""
        self.log("安装Python依赖...")
        
        # 检查虚拟环境
        venv_path = self.base_dir / "backend" / "venv"
        if not venv_path.exists():
            self.log("创建Python虚拟环境...")
            success, stdout, stderr = self.run_command(
                f"python -m venv {venv_path}"
            )
            if not success:
                self.log(f"虚拟环境创建失败: {stderr}")
                return False
        
        # 激活虚拟环境并安装依赖
        if platform.system() == "Windows":
            pip_cmd = f"{venv_path}\\Scripts\\pip.exe"
        else:
            pip_cmd = f"{venv_path}/bin/pip"
        
        requirements_file = self.base_dir / "backend" / "requirements.txt"
        if requirements_file.exists():
            self.log("安装backend依赖...")
            success, stdout, stderr = self.run_command(
                f'"{pip_cmd}" install -r "{requirements_file}"'
            )
            if success:
                self.log("Backend依赖安装完成")
                self.status['backend_deps'] = True
                return True
            else:
                self.log(f"Backend依赖安装失败: {stderr}")
        
        return False
    
    def install_frontend_deps(self):
        """安装前端依赖"""
        if not self.status['nodejs']:
            self.log("Node.js未安装，跳过前端依赖安装")
            return False
        
        frontend_dir = self.base_dir / "frontend"
        if not frontend_dir.exists():
            self.log("前端目录不存在")
            return False
        
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            self.log("package.json不存在")
            return False
        
        self.log("安装前端依赖...")
        success, stdout, stderr = self.run_command(
            "npm install", 
            shell=True
        )
        
        if success:
            self.log("前端依赖安装完成")
            self.status['frontend_deps'] = True
            return True
        else:
            self.log(f"前端依赖安装失败: {stderr}")
            return False
    
    def install_ai_models(self):
        """安装AI模型"""
        if not self.status['ollama']:
            self.log("Ollama未安装，跳过AI模型安装")
            return False
        
        self.log("下载AI模型...")
        
        # 下载Qwen2.5:7b模型
        self.log("下载Qwen2.5:7b模型（约4GB）...")
        success, stdout, stderr = self.run_command(
            "ollama pull qwen2.5:7b",
            timeout=1800  # 30分钟超时
        )
        
        if success:
            self.log("AI模型下载完成")
            self.status['ai_models'] = True
            return True
        else:
            self.log(f"AI模型下载失败: {stderr}")
            return False
    
    def create_config_files(self):
        """创建配置文件"""
        self.log("创建配置文件...")
        
        # 创建.env文件
        env_file = self.base_dir / "backend" / ".env"
        if not env_file.exists():
            env_content = """# Pervis PRO Configuration
DATABASE_URL=sqlite:///./pervis_director.db
SECRET_KEY=your-secret-key-here
DEBUG=True

# AI Configuration
USE_LOCAL_AI=True
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b

# Cloud AI (optional)
GEMINI_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# File Storage
UPLOAD_FOLDER=./storage/uploads
MAX_CONTENT_LENGTH=100MB
"""
            env_file.write_text(env_content, encoding='utf-8')
            self.log("创建了backend/.env配置文件")
        
        return True
    
    def generate_report(self):
        """生成安装报告"""
        self.log("生成安装报告...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "summary": {
                "total_components": len(self.status),
                "installed_components": sum(self.status.values()),
                "success_rate": f"{sum(self.status.values())}/{len(self.status)}"
            },
            "install_log": self.install_log
        }
        
        # 保存JSON报告
        report_file = self.base_dir / "installation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成Markdown报告
        md_report = f"""# Pervis PRO 安装报告

**生成时间**: {report['timestamp']}

## 安装状态

| 组件 | 状态 |
|------|------|
| Python | {'✅ 已安装' if self.status['python'] else '❌ 未安装'} |
| Node.js | {'✅ 已安装' if self.status['nodejs'] else '❌ 未安装'} |
| Git | {'✅ 已安装' if self.status['git'] else '❌ 未安装'} |
| FFmpeg | {'✅ 已安装' if self.status['ffmpeg'] else '❌ 未安装'} |
| Ollama | {'✅ 已安装' if self.status['ollama'] else '❌ 未安装'} |
| Backend依赖 | {'✅ 已安装' if self.status['backend_deps'] else '❌ 未安装'} |
| Frontend依赖 | {'✅ 已安装' if self.status['frontend_deps'] else '❌ 未安装'} |
| Launcher依赖 | {'✅ 已安装' if self.status['launcher_deps'] else '❌ 未安装'} |
| AI模型 | {'✅ 已安装' if self.status['ai_models'] else '❌ 未安装'} |

## 总结

- **总组件数**: {report['summary']['total_components']}
- **已安装组件**: {report['summary']['installed_components']}
- **成功率**: {report['summary']['success_rate']}

## 下一步

{'### 🎉 安装完成！' if sum(self.status.values()) == len(self.status) else '### ⚠️ 部分组件需要手动安装'}

{'所有组件已成功安装，可以启动Pervis PRO了：' if sum(self.status.values()) == len(self.status) else '请根据上述状态表手动安装缺失的组件。'}

```bash
python 启动_Pervis_PRO.py
```

## 配置说明

1. **本地AI**: 已配置使用Ollama + Qwen2.5:7b模型
2. **云端AI**: 如需使用，请在 `backend/.env` 中设置API密钥
3. **数据库**: 使用SQLite，位于 `pervis_director.db`

## 故障排除

如果遇到问题，请检查：
1. 所有组件是否正确安装
2. 环境变量是否正确设置
3. 防火墙是否阻止了网络连接
4. 磁盘空间是否充足（AI模型需要约4GB空间）
"""
        
        md_report_file = self.base_dir / "安装报告.md"
        md_report_file.write_text(md_report, encoding='utf-8')
        
        self.log(f"安装报告已保存: {report_file}")
        self.log(f"安装报告已保存: {md_report_file}")
        
        return report
    
    def run_full_installation(self):
        """运行完整安装流程"""
        self.log("开始Pervis PRO完整环境检查和安装...")
        
        # 1. 检查现有组件
        self.log("=== 第1步: 检查现有组件 ===")
        self.check_python()
        self.check_nodejs()
        self.check_git()
        self.check_ffmpeg()
        self.check_ollama()
        
        # 2. 安装缺失的系统组件
        self.log("=== 第2步: 安装缺失的系统组件 ===")
        
        if not self.status['nodejs']:
            self.install_nodejs_manual()
        
        if not self.status['ffmpeg']:
            self.install_ffmpeg_manual()
        
        if not self.status['ollama']:
            self.install_ollama_manual()
        
        # 3. 安装项目依赖
        self.log("=== 第3步: 安装项目依赖 ===")
        
        if self.status['python']:
            self.install_python_deps()
        
        if self.status['nodejs']:
            self.install_frontend_deps()
        
        # 4. 安装AI模型
        self.log("=== 第4步: 安装AI模型 ===")
        self.install_ai_models()
        
        # 5. 创建配置文件
        self.log("=== 第5步: 创建配置文件 ===")
        self.create_config_files()
        
        # 6. 生成报告
        self.log("=== 第6步: 生成安装报告 ===")
        report = self.generate_report()
        
        # 7. 显示结果
        self.log("=== 安装完成 ===")
        success_count = sum(self.status.values())
        total_count = len(self.status)
        
        if success_count == total_count:
            self.log("🎉 所有组件安装成功！")
            self.log("可以运行: python 启动_Pervis_PRO.py")
        else:
            self.log(f"⚠️ {success_count}/{total_count} 组件安装成功")
            self.log("请查看安装报告了解详情")
        
        return report

if __name__ == "__main__":
    installer = PervisInstaller()
    installer.run_full_installation()