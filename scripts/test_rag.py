#!/usr/bin/env python3
"""
RAG功能测试脚本
测试文档解析、向量生成、ES连接和检索功能
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试1: 模块导入")
    print("=" * 60)
    
    try:
        from backend.app.service.core.rag.nlp.model import generate_embedding
        print("✓ 成功导入 generate_embedding")
    except Exception as e:
        print(f"✗ 导入 generate_embedding 失败: {e}")
        return False
    
    try:
        from backend.app.service.core.rag.app.naive import chunk
        print("✓ 成功导入 chunk")
    except Exception as e:
        print(f"✗ 导入 chunk 失败: {e}")
        return False
    
    try:
        from backend.app.service.core.rag.utils.rag_utils import ESConnection
        print("✓ 成功导入 ESConnection")
    except Exception as e:
        print(f"✗ 导入 ESConnection 失败: {e}")
        return False
    
    try:
        from backend.app.service.core.rag.nlp.search_v2 import Dealer
        print("✓ 成功导入 Dealer")
    except Exception as e:
        print(f"✗ 导入 Dealer 失败: {e}")
        return False
    
    try:
        from backend.app.service.core.document_service import DocumentService
        print("✓ 成功导入 DocumentService")
    except Exception as e:
        print(f"✗ 导入 DocumentService 失败: {e}")
        return False
    
    try:
        from backend.app.service.core.retrieval_service import RetrievalService
        print("✓ 成功导入 RetrievalService")
    except Exception as e:
        print(f"✗ 导入 RetrievalService 失败: {e}")
        return False
    
    print("\n✓ 所有模块导入成功\n")
    return True


def test_es_connection():
    """测试ES连接"""
    print("=" * 60)
    print("测试2: ES连接")
    print("=" * 60)
    
    try:
        from backend.app.service.core.rag.utils.rag_utils import ESConnection
        
        es_host = os.getenv("ES_HOST")
        if not es_host:
            print("⚠ 未设置 ES_HOST 环境变量")
            print("  请在 .env 文件中设置: ES_HOST=http://localhost:9200")
            return False
        
        print(f"ES_HOST: {es_host}")
        
        es_conn = ESConnection()
        print("✓ ES连接实例创建成功")
        
        # 测试ES健康状态
        try:
            health = es_conn.es.cluster.health()
            print(f"✓ ES集群状态: {health.get('status', 'unknown')}")
            print(f"  集群名称: {health.get('cluster_name', 'unknown')}")
            print(f"  节点数量: {health.get('number_of_nodes', 0)}")
        except Exception as e:
            print(f"⚠ ES健康检查失败: {e}")
            print("  请确保Elasticsearch正在运行")
            return False
        
        print("\n✓ ES连接测试成功\n")
        return True
        
    except Exception as e:
        print(f"✗ ES连接测试失败: {e}")
        return False


def test_vector_generation():
    """测试向量生成"""
    print("=" * 60)
    print("测试3: 向量生成")
    print("=" * 60)
    
    try:
        from backend.app.service.core.rag.nlp.model import generate_embedding
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("⚠ 未设置 DASHSCOPE_API_KEY 环境变量")
            print("  请在 .env 文件中设置: DASHSCOPE_API_KEY=your_api_key")
            return False
        
        print(f"DASHSCOPE_API_KEY: {api_key[:10]}...")
        
        # 测试单个文本向量生成
        test_text = "这是一个测试文本"
        print(f"测试文本: {test_text}")
        
        embedding = generate_embedding(test_text)
        
        if embedding is None:
            print("✗ 向量生成返回None")
            return False
        
        print(f"✓ 向量生成成功")
        print(f"  向量维度: {len(embedding)}")
        print(f"  前5个值: {embedding[:5]}")
        
        # 测试批量向量生成
        test_texts = ["文本1", "文本2", "文本3"]
        print(f"\n测试批量向量生成: {len(test_texts)} 个文本")
        
        embeddings = generate_embedding(test_texts)
        
        if embeddings is None or len(embeddings) != len(test_texts):
            print(f"✗ 批量向量生成失败")
            return False
        
        print(f"✓ 批量向量生成成功")
        print(f"  生成向量数: {len(embeddings)}")
        print(f"  每个向量维度: {len(embeddings[0])}")
        
        print("\n✓ 向量生成测试成功\n")
        return True
        
    except Exception as e:
        print(f"✗ 向量生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_parsing():
    """测试文档解析"""
    print("=" * 60)
    print("测试4: 文档解析")
    print("=" * 60)
    
    try:
        from backend.app.service.core.rag.app.naive import chunk
        
        # 查找测试文件
        test_files = [
            "/home/tianwenkai/workspace/DM-Code-Agent/README.md",
            "/home/tianwenkai/workspace/DM-Code-Agent/requirements.txt",
        ]
        
        test_file = None
        for file_path in test_files:
            if os.path.exists(file_path):
                test_file = file_path
                break
        
        if not test_file:
            print("⚠ 未找到测试文件")
            print("  请在项目目录中放置一个可解析的文件（如.txt, .md, .pdf等）")
            return False
        
        print(f"测试文件: {test_file}")
        
        def dummy_callback(prog=None, msg=""):
            if msg:
                print(f"  {msg}")
        
        chunks = chunk(test_file, callback=dummy_callback)
        
        if not chunks:
            print("✗ 文档解析返回空结果")
            return False
        
        print(f"✓ 文档解析成功")
        print(f"  解析到 {len(chunks)} 个文档块")
        
        if len(chunks) > 0:
            first_chunk = chunks[0]
            print(f"  第一个文档块字段: {list(first_chunk.keys())}")
            if "content_with_weight" in first_chunk:
                content = first_chunk["content_with_weight"]
                print(f"  内容预览: {content[:100]}...")
        
        print("\n✓ 文档解析测试成功\n")
        return True
        
    except Exception as e:
        print(f"✗ 文档解析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval_service():
    """测试检索服务"""
    print("=" * 60)
    print("测试5: 检索服务")
    print("=" * 60)
    
    try:
        from backend.app.service.core.retrieval_service import RetrievalService
        
        # 检查ES是否可用
        es_host = os.getenv("ES_HOST")
        if not es_host:
            print("⚠ 未设置 ES_HOST 环境变量，跳过检索测试")
            return False
        
        print(f"ES_HOST: {es_host}")
        
        retrieval_service = RetrievalService()
        print("✓ 检索服务实例创建成功")
        
        # 测试检索（可能没有数据，所以会返回空）
        test_question = "测试问题"
        print(f"测试问题: {test_question}")
        
        results = retrieval_service.retrieve_content(
            question=test_question,
            index_names="test_index",
            page_size=3
        )
        
        print(f"✓ 检索调用成功")
        print(f"  检索结果数: {len(results)}")
        
        if results:
            for i, result in enumerate(results[:3], start=1):
                print(f"  结果{i}:")
                print(f"    文档: {result.get('document_name', 'N/A')}")
                print(f"    相似度: {result.get('similarity', 0.0):.3f}")
        
        print("\n✓ 检索服务测试成功\n")
        return True
        
    except Exception as e:
        print(f"✗ 检索服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 60)
    print("RAG功能测试")
    print("=" * 60 + "\n")
    
    results = {
        "模块导入": test_imports(),
        "ES连接": test_es_connection(),
        "向量生成": test_vector_generation(),
        "文档解析": test_document_parsing(),
        "检索服务": test_retrieval_service(),
    }
    
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！RAG功能集成成功！")
        return 0
    else:
        print("\n⚠ 部分测试失败，请检查配置和依赖")
        return 1


if __name__ == "__main__":
    sys.exit(main())
