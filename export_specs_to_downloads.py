# -*- coding: utf-8 -*-
"""
将所有 spec 文件导出到 Downloads 文件夹
"""
import os
import shutil

# 目标文件夹
target_dir = r"C:\Users\hy10\Downloads\kiro_specs"
os.makedirs(target_dir, exist_ok=True)

# 源文件列表
spec_files = [
    (".kiro/specs/multi-agent-workflow-core/design.md", "multi-agent-workflow-core_design.txt"),
    (".kiro/specs/multi-agent-workflow-core/requirements.md", "multi-agent-workflow-core_requirements.txt"),
    (".kiro/specs/multi-agent-workflow-core/tasks.md", "multi-agent-workflow-core_tasks.txt"),
    (".kiro/specs/pervis-ai-integration-fix/design.md", "pervis-ai-integration-fix_design.txt"),
    (".kiro/specs/pervis-ai-integration-fix/requirements.md", "pervis-ai-integration-fix_requirements.txt"),
    (".kiro/specs/pervis-ai-integration-fix/tasks.md", "pervis-ai-integration-fix_tasks.txt"),
    (".kiro/specs/pervis-export-system/design.md", "pervis-export-system_design.txt"),
    (".kiro/specs/pervis-export-system/requirements.md", "pervis-export-system_requirements.txt"),
    (".kiro/specs/pervis-export-system/tasks.md", "pervis-export-system_tasks.txt"),
    (".kiro/specs/pervis-project-wizard/agent-workflow-diagram.md", "pervis-project-wizard_agent-workflow-diagram.txt"),
    (".kiro/specs/pervis-project-wizard/design.md", "pervis-project-wizard_design.txt"),
    (".kiro/specs/pervis-project-wizard/requirements.md", "pervis-project-wizard_requirements.txt"),
    (".kiro/specs/pervis-project-wizard/tasks.md", "pervis-project-wizard_tasks.txt"),
    (".kiro/specs/pervis-system-agent/design.md", "pervis-system-agent_design.txt"),
    (".kiro/specs/pervis-system-agent/requirements.md", "pervis-system-agent_requirements.txt"),
    (".kiro/specs/pervis-system-agent/tasks.md", "pervis-system-agent_tasks.txt"),
]

# 复制文件
success_count = 0
for src, dst in spec_files:
    try:
        src_path = os.path.join(os.getcwd(), src)
        dst_path = os.path.join(target_dir, dst)
        
        # 读取源文件
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 写入目标文件
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ {dst}")
        success_count += 1
    except Exception as e:
        print(f"✗ {dst}: {e}")

print(f"\n完成! 成功导出 {success_count}/{len(spec_files)} 个文件到 {target_dir}")
