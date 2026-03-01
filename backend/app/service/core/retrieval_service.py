"""检索服务 - 封装RAG检索功能"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.app.service.core.rag.nlp.search_v2 import Dealer
from backend.app.service.core.rag.utils.rag_utils import ESConnection

logger = logging.getLogger(__name__)


class RetrievalService:
    """检索服务类，提供RAG检索功能"""

    def __init__(self):
        self.es_connection = None
        self.dealer = None

    def _get_es_connection(self) -> ESConnection:
        """获取ES连接实例（单例）"""
        if self.es_connection is None:
            self.es_connection = ESConnection()
        return self.es_connection

    def _get_dealer(self) -> Dealer:
        """获取Dealer实例（单例）"""
        if self.dealer is None:
            self.dealer = Dealer(dataStore=self._get_es_connection())
        return self.dealer

    def retrieve_content(
        self,
        question: str,
        index_names: str | List[str],
        page_size: int = 5,
        vector_similarity_weight: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        检索相关内容
        
        Args:
            question: 用户问题
            index_names: ES索引名称（字符串或列表）
            page_size: 返回结果数量
            vector_similarity_weight: 向量相似度权重
            
        Returns:
            检索结果列表，每个结果包含：
            - id: 序号
            - document_id: 文档ID
            - document_name: 文档名称
            - content_with_weight: 内容
            - similarity: 相似度
            - vector_similarity: 向量相似度
            - term_similarity: 词汇相似度
        """
        try:
            logger.info(f"开始检索，问题: {question[:50]}...")

            if isinstance(index_names, str):
                index_names = index_names.split(",")

            dealer = self._get_dealer()

            results = dealer.retrieval(
                question=question,
                embd_mdl=None,
                tenant_ids=index_names,
                kb_ids=None,
                vector_similarity_weight=vector_similarity_weight,
                page=1,
                page_size=page_size,
            )

            extracted_data = []

            for i, chunk in enumerate(results["chunks"], start=1):
                content_with_weight = chunk.get("content_with_weight", "N/A")
                doc_id = chunk.get("doc_id", "N/A")
                docnm = chunk.get("docnm_kwd", "N/A")
                docnm = docnm.split("/")[-1] if "/" in docnm else docnm

                message = {
                    "id": i,
                    "document_id": doc_id,
                    "document_name": docnm,
                    "content_with_weight": content_with_weight,
                    "similarity": chunk.get("similarity", 0.0),
                    "vector_similarity": chunk.get("vector_similarity", 0.0),
                    "term_similarity": chunk.get("term_similarity", 0.0),
                }

                extracted_data.append(message)

            logger.info(f"检索完成，共 {len(extracted_data)} 个结果")
            return extracted_data

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

    def format_retrieval_results(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化检索结果为文本
        
        Args:
            results: 检索结果列表
            
        Returns:
            格式化后的文本
        """
        if not results:
            return "未检索到相关内容。"

        lines = ["=== RAG检索结果 ===\n"]
        
        for result in results:
            lines.append(f"[{result['id']}] 文档: {result['document_name']}")
            lines.append(f"相似度: {result['similarity']:.3f}")
            lines.append(f"内容:\n{result['content_with_weight']}\n")
        
        return "\n".join(lines)

    def build_enhanced_task(
        self, original_task: str, retrieval_results: List[Dict[str, Any]]
    ) -> str:
        """
        构建增强后的任务描述
        
        Args:
            original_task: 原始任务
            retrieval_results: 检索结果列表
            
        Returns:
            增强后的任务描述
        """
        if not retrieval_results:
            return original_task

        formatted_results = self.format_retrieval_results(retrieval_results)
        
        enhanced_task = f"""{formatted_results}

任务：{original_task}

请基于以上检索结果回答任务。"""
        
        return enhanced_task


_retrieval_service: RetrievalService = None


def get_retrieval_service() -> RetrievalService:
    """获取全局RetrievalService实例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
