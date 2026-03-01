#!/usr/bin/env python3
"""
文档导入脚本
支持将文档通过集成的文档解析和RAG能力存入ES数据库
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.service.core.document_service import get_document_service
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", 
    ".txt", ".md", ".html", ".json", ".pptx", ".ppt"
}


def is_supported_file(file_path: Path) -> bool:
    """检查文件是否支持"""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def collect_files(
    path: Path, recursive: bool = False
) -> List[Path]:
    """
    收集需要导入的文件
    
    Args:
        path: 文件或目录路径
        recursive: 是否递归处理子目录
        
    Returns:
        文件路径列表
    """
    files = []
    
    if path.is_file():
        if is_supported_file(path):
            files.append(path)
        else:
            logger.warning(f"不支持的文件类型: {path}")
    elif path.is_dir():
        if recursive:
            for file_path in path.rglob("*"):
                if file_path.is_file() and is_supported_file(file_path):
                    files.append(file_path)
        else:
            for file_path in path.glob("*"):
                if file_path.is_file() and is_supported_file(file_path):
                    files.append(file_path)
    else:
        logger.error(f"路径不存在: {path}")
    
    return sorted(files)


def import_file(
    file_path: Path, index_name: str, document_service
) -> bool:
    """
    导入单个文件
    
    Args:
        file_path: 文件路径
        index_name: ES索引名称
        document_service: 文档服务实例
        
    Returns:
        是否成功
    """
    try:
        file_name = file_path.name
        logger.info(f"开始导入: {file_name}")
        
        success = document_service.import_document(
            str(file_path), file_name, index_name
        )
        
        if success:
            logger.info(f"✓ 导入成功: {file_name}")
        else:
            logger.warning(f"✗ 导入失败: {file_name}")
        
        return success
    except Exception as e:
        logger.error(f"✗ 导入失败: {file_path}, 错误: {e}")
        return False


def import_files(
    files: List[Path], index_name: str, document_service
) -> dict:
    """
    批量导入文件
    
    Args:
        files: 文件路径列表
        index_name: ES索引名称
        document_service: 文档服务实例
        
    Returns:
        导入结果统计
    """
    results = {
        "total": len(files),
        "success": 0,
        "failed": 0,
        "failed_files": []
    }
    
    for i, file_path in enumerate(files, start=1):
        logger.info(f"[{i}/{len(files)}] 处理: {file_path.name}")
        
        success = import_file(file_path, index_name, document_service)
        
        if success:
            results["success"] += 1
        else:
            results["failed"] += 1
            results["failed_files"].append(str(file_path))
    
    return results


def print_summary(results: dict):
    """打印导入结果摘要"""
    print("\n" + "=" * 60)
    print("导入结果摘要")
    print("=" * 60)
    print(f"总文件数: {results['total']}")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    print(f"成功率: {results['success'] / results['total'] * 100:.1f}%")
    
    if results["failed_files"]:
        print("\n失败的文件:")
        for failed_file in results["failed_files"][:10]:
            print(f"  - {failed_file}")
        
        if len(results["failed_files"]) > 10:
            print(f"  ... 还有 {len(results['failed_files']) - 10} 个文件")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="文档导入脚本 - 将文档导入到Elasticsearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 导入单个文件
  python import_documents.py --file document.pdf --index my_knowledge_base
  
  # 导入整个目录
  python import_documents.py --directory ./docs --index my_knowledge_base
  
  # 递归导入目录（包括子目录）
  python import_documents.py --directory ./docs --index my_knowledge_base --recursive
        """
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="要导入的文件路径"
    )
    
    parser.add_argument(
        "--directory",
        type=str,
        help="要导入的目录路径"
    )
    
    parser.add_argument(
        "--index",
        type=str,
        required=True,
        help="Elasticsearch索引名称"
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="递归处理子目录"
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.file and not args.directory:
        parser.error("必须指定 --file 或 --directory 参数")
    
    if args.file and args.directory:
        parser.error("不能同时指定 --file 和 --directory 参数")
    
    # 收集文件
    files = []
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"文件不存在: {args.file}")
            sys.exit(1)
        files = collect_files(file_path)
    else:
        dir_path = Path(args.directory)
        if not dir_path.exists():
            logger.error(f"目录不存在: {args.directory}")
            sys.exit(1)
        files = collect_files(dir_path, args.recursive)
    
    if not files:
        logger.warning("没有找到可导入的文件")
        sys.exit(0)
    
    logger.info(f"找到 {len(files)} 个可导入的文件")
    
    # 导入文件
    document_service = get_document_service()
    results = import_files(files, args.index, document_service)
    
    # 打印摘要
    print_summary(results)
    
    # 退出码
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
