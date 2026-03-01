#!/usr/bin/env python3
"""
批量修复导入路径脚本
将源项目的导入路径替换为目标项目的导入路径
"""

import os
import re
from pathlib import Path

BASE_DIR = Path("/home/tianwenkai/workspace/DM-Code-Agent/backend/app/service/core")

REPLACEMENTS = [
    ("from service.core.rag", "from backend.app.service.core.rag"),
    ("from service.core.deepdoc", "from backend.app.service.core.deepdoc"),
    ("from service.core.api.utils.file_utils", "from backend.app.utils.file_utils"),
    ("import service.core.rag", "import backend.app.service.core.rag"),
    ("import service.core.deepdoc", "import backend.app.service.core.deepdoc"),
]

def fix_imports_in_file(file_path: Path) -> int:
    """修复单个文件的导入路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements_made = 0
        
        for old, new in REPLACEMENTS:
            if old in content:
                content = content.replace(old, new)
                replacements_made += content.count(new)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return replacements_made
        
        return 0
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return 0

def fix_imports_in_directory(directory: Path) -> dict:
    """递归修复目录中所有Python文件的导入路径"""
    results = {
        "total_files": 0,
        "modified_files": 0,
        "total_replacements": 0,
        "files": []
    }
    
    for file_path in directory.rglob("*.py"):
        results["total_files"] += 1
        replacements = fix_imports_in_file(file_path)
        
        if replacements > 0:
            results["modified_files"] += 1
            results["total_replacements"] += replacements
            results["files"].append({
                "path": str(file_path.relative_to(BASE_DIR)),
                "replacements": replacements
            })
    
    return results

def main():
    print("=" * 60)
    print("开始批量修复导入路径")
    print("=" * 60)
    
    target_dirs = [
        BASE_DIR / "rag",
        BASE_DIR / "deepdoc",
    ]
    
    total_results = {
        "total_files": 0,
        "modified_files": 0,
        "total_replacements": 0,
        "files": []
    }
    
    for target_dir in target_dirs:
        if not target_dir.exists():
            print(f"⚠ 目录不存在: {target_dir}")
            continue
        
        print(f"\n处理目录: {target_dir.name}")
        print("-" * 60)
        
        results = fix_imports_in_directory(target_dir)
        
        total_results["total_files"] += results["total_files"]
        total_results["modified_files"] += results["modified_files"]
        total_results["total_replacements"] += results["total_replacements"]
        total_results["files"].extend(results["files"])
        
        print(f"✓ 扫描文件: {results['total_files']}")
        print(f"✓ 修改文件: {results['modified_files']}")
        print(f"✓ 替换次数: {results['total_replacements']}")
    
    print("\n" + "=" * 60)
    print("修复完成统计")
    print("=" * 60)
    print(f"总扫描文件: {total_results['total_files']}")
    print(f"总修改文件: {total_results['modified_files']}")
    print(f"总替换次数: {total_results['total_replacements']}")
    
    if total_results["files"]:
        print("\n修改的文件列表:")
        for file_info in total_results["files"][:20]:
            print(f"  - {file_info['path']} ({file_info['replacements']} 处替换)")
        
        if len(total_results["files"]) > 20:
            print(f"  ... 还有 {len(total_results['files']) - 20} 个文件")
    
    print("\n✓ 导入路径修复完成!")

if __name__ == "__main__":
    main()
