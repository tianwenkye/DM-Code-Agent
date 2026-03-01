"""文档服务 - 封装文档解析、向量化和ES存储功能"""

from __future__ import annotations

import datetime
import logging
import os
from typing import Any, Dict, List

import xxhash
import numpy as np
from dotenv import load_dotenv

from backend.app.service.core.rag.app.naive import chunk
from backend.app.service.core.rag.utils.rag_utils import ESConnection
from backend.app.service.core.rag.nlp.model import generate_embedding

load_dotenv()

logger = logging.getLogger(__name__)


def dummy_callback(prog=None, msg=""):
    """空的回调函数，用于文档解析"""
    pass


class DocumentService:
    """文档服务类，提供文档解析、向量化和ES存储功能"""

    def __init__(self):
        self.es_connection = None

    def _get_es_connection(self) -> ESConnection:
        """获取ES连接实例（单例）"""
        if self.es_connection is None:
            self.es_connection = ESConnection()
        return self.es_connection

    def parse_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        解析文档文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的文档块列表
        """
        try:
            logger.info(f"开始解析文档: {file_path}")
            result = chunk(file_path, callback=dummy_callback)
            logger.info(f"文档解析完成，共 {len(result)} 个文档块")
            return result
        except Exception as e:
            logger.error(f"文档解析失败: {e}")
            raise

    def batch_generate_embeddings(
        self, texts: List[str], batch_size: int = 10
    ) -> List[List[float]]:
        """
        批量生成文本的向量嵌入
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小（阿里云DashScope限制为10）
            
        Returns:
            向量列表
        """
        try:
            logger.info(f"开始生成 {len(texts)} 个文本的向量嵌入")
            embeddings = generate_embedding(texts)
            
            if embeddings is None:
                logger.warning("向量生成返回None")
                return []
            
            logger.info(f"向量生成完成，共 {len(embeddings)} 个向量")
            return embeddings
        except Exception as e:
            logger.error(f"批量生成向量失败: {e}")
            return []

    def process_document_chunks(
        self, items: List[Dict[str, Any]], file_name: str, index_name: str
    ) -> List[Dict[str, Any]]:
        """
        批量处理数据项，生成向量并构建ES文档
        
        Args:
            items: 数据项列表
            file_name: 文件名
            index_name: ES索引名称
            
        Returns:
            处理后的数据项列表
        """
        try:
            logger.info(f"开始处理 {len(items)} 个文档块")
            
            texts = [item["content_with_weight"] for item in items]
            embeddings = self.batch_generate_embeddings(texts)
            
            if len(embeddings) != len(items):
                logger.error(f"向量数量 {len(embeddings)} 与文档块数量 {len(items)} 不匹配")
                return []
            
            results = []
            for item, embedding in zip(items, embeddings):
                chunk_id = xxhash.xxh64(
                    (item["content_with_weight"] + index_name).encode("utf-8")
                ).hexdigest()

                d = {
                    "id": chunk_id,
                    "content_ltks": item["content_ltks"],
                    "content_with_weight": item["content_with_weight"],
                    "content_sm_ltks": item["content_sm_ltks"],
                    "important_kwd": [],
                    "important_tks": [],
                    "question_kwd": [],
                    "question_tks": [],
                    "create_time": str(datetime.datetime.now()).replace("T", " ")[:19],
                    "create_timestamp_flt": datetime.datetime.now().timestamp(),
                }

                d["kb_id"] = index_name
                d["docnm_kwd"] = item["docnm_kwd"]
                d["title_tks"] = item["title_tks"]
                d["doc_id"] = xxhash.xxh64(file_name.encode("utf-8")).hexdigest()
                d["docnm"] = file_name
                
                d[f"q_{len(embedding)}_vec"] = embedding
                
                results.append(d)

            logger.info(f"文档块处理完成，共 {len(results)} 个文档块")
            return results

        except Exception as e:
            logger.error(f"process_document_chunks error: {e}")
            return []

    def insert_to_es(
        self, documents: List[Dict[str, Any]], index_name: str
    ) -> List[str]:
        """
        批量插入文档到Elasticsearch
        
        Args:
            documents: 文档列表
            index_name: ES索引名称
            
        Returns:
            错误列表（如果有的话）
        """
        try:
            logger.info(f"开始插入 {len(documents)} 个文档到ES索引: {index_name}")
            es_connection = self._get_es_connection()
            errors = es_connection.insert(documents=documents, indexName=index_name)
            
            if errors:
                logger.warning(f"插入完成，但有 {len(errors)} 个错误")
                for error in errors[:5]:
                    logger.warning(f"  错误: {error}")
            else:
                logger.info(f"成功插入 {len(documents)} 个文档到ES")
            
            return errors
        except Exception as e:
            logger.error(f"插入ES失败: {e}")
            raise

    def import_document(
        self, file_path: str, file_name: str, index_name: str
    ) -> bool:
        """
        完整的文档导入流程：解析 -> 处理 -> 插入ES
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            index_name: ES索引名称
            
        Returns:
            是否成功
        """
        try:
            logger.info(f"开始导入文档: {file_name} -> {index_name}")
            
            documents = self.parse_document(file_path)
            if not documents:
                logger.warning(f"文档解析为空: {file_path}")
                return False

            processed_documents = self.process_document_chunks(
                documents, file_name, index_name
            )
            if not processed_documents:
                logger.warning(f"文档处理失败: {file_path}")
                return False

            errors = self.insert_to_es(processed_documents, index_name)
            if errors:
                logger.warning(f"插入ES时有错误: {file_name}")
                return False

            logger.info(f"文档导入成功: {file_name}")
            return True

        except Exception as e:
            logger.error(f"文档导入失败: {file_name}, 错误: {e}")
            return False

    def import_documents_batch(
        self, file_paths: List[str], index_name: str
    ) -> Dict[str, bool]:
        """
        批量导入多个文档
        
        Args:
            file_paths: 文件路径列表
            index_name: ES索引名称
            
        Returns:
            每个文件的导入结果 {file_path: success}
        """
        results = {}
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            try:
                success = self.import_document(file_path, file_name, index_name)
                results[file_path] = success
            except Exception as e:
                logger.error(f"导入文档失败: {file_path}, 错误: {e}")
                results[file_path] = False
        
        return results


_document_service: DocumentService = None


def get_document_service() -> DocumentService:
    """获取全局DocumentService实例"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
