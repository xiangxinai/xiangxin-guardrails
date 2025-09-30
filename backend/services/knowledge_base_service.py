"""
代答知识库服务
使用FAISS进行向量搜索，支持问答对的向量化存储和检索
现在使用OpenAI API进行向量化而不是本地模型
"""
import os
import json
import pickle
import logging
import uuid
from typing import List, Optional, Dict, Tuple, Any
from pathlib import Path

import faiss
import numpy as np
from openai import OpenAI
from sqlalchemy.orm import Session

from database.models import KnowledgeBase, User
from config import settings

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self):
        self.client = None
        self.vector_dimension = settings.embedding_model_dimension  # 嵌入向量维度
        self.similarity_threshold = settings.embedding_similarity_threshold  # 相似度阈值
        self.max_results = settings.embedding_max_results  # 最大返回结果数

        # 设置存储路径
        self.storage_path = Path(settings.data_dir) / "knowledge_bases"
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_client(self) -> OpenAI:
        """懒加载OpenAI客户端"""
        if self.client is None:
            try:
                self.client = OpenAI(
                    api_key=settings.embedding_api_key,
                    base_url=settings.embedding_api_base_url,
                )
                logger.info(f"OpenAI embedding client initialized with base_url: {settings.embedding_api_base_url}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI embedding client: {e}")
                raise
        return self.client

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本的嵌入向量（逐个处理，避免服务端OOM）"""
        if not texts:
            return []
            
        try:
            client = self._get_client()
            all_embeddings = []
            
            logger.info(f"Processing {len(texts)} texts one by one to avoid server OOM")
            
            for i, text in enumerate(texts):
                logger.info(f"Processing text {i+1}/{len(texts)}")
                
                response = client.embeddings.create(
                    input=[text],  # 每次只传入一个文本
                    model=settings.embedding_model_name
                )
                
                embedding = response.data[0].embedding
                all_embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:  # 每10个记录一次进度
                    logger.info(f"Completed {i+1}/{len(texts)} texts")
            
            logger.info(f"Generated embeddings for all {len(texts)} texts")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            raise

    def parse_jsonl_file(self, file_content: bytes) -> List[Dict[str, str]]:
        """
        解析JSONL文件内容
        Args:
            file_content: 文件字节内容
        Returns:
            问答对列表
        """
        qa_pairs = []
        try:
            content_str = file_content.decode('utf-8')
            lines = content_str.strip().split('\n')

            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue

                try:
                    qa_data = json.loads(line)

                    # 验证必需字段
                    if not all(key in qa_data for key in ['questionid', 'question', 'answer']):
                        logger.warning(f"Line {line_num}: Missing required fields (questionid, question, answer)")
                        continue

                    # 验证字段类型
                    if not all(isinstance(qa_data[key], str) for key in ['questionid', 'question', 'answer']):
                        logger.warning(f"Line {line_num}: All fields must be strings")
                        continue

                    # 验证内容不为空
                    if not qa_data['question'].strip() or not qa_data['answer'].strip():
                        logger.warning(f"Line {line_num}: Question and answer cannot be empty")
                        continue

                    qa_pairs.append({
                        'questionid': qa_data['questionid'].strip(),
                        'question': qa_data['question'].strip(),
                        'answer': qa_data['answer'].strip()
                    })

                except json.JSONDecodeError as e:
                    logger.warning(f"Line {line_num}: Invalid JSON format - {e}")
                    continue

        except UnicodeDecodeError as e:
            raise ValueError(f"File encoding error: {e}")

        if not qa_pairs:
            raise ValueError("No valid QA pairs found in the file")

        logger.info(f"Parsed {len(qa_pairs)} QA pairs from JSONL file")
        return qa_pairs

    def create_vector_index(self, qa_pairs: List[Dict[str, str]], knowledge_base_id: int) -> str:
        """
        创建FAISS向量索引
        Args:
            qa_pairs: 问答对列表
            knowledge_base_id: 知识库ID
        Returns:
            向量文件路径
        """
        try:
            # 提取问题文本
            questions = [qa['question'] for qa in qa_pairs]

            # 生成向量
            logger.info(f"Generating embeddings for {len(questions)} questions...")
            embeddings = self._get_embeddings(questions)
            vectors = np.array(embeddings, dtype=np.float32)

            # 创建FAISS索引
            index = faiss.IndexFlatIP(self.vector_dimension)  # 使用内积相似度

            # 归一化向量（用于余弦相似度）
            faiss.normalize_L2(vectors)

            # 添加向量到索引
            index.add(vectors)

            # 保存索引和元数据
            vector_file_path = self.storage_path / f"kb_{knowledge_base_id}_vectors.pkl"

            vector_data = {
                'index': faiss.serialize_index(index),
                'qa_pairs': qa_pairs,
                'vector_dimension': self.vector_dimension,
                'total_pairs': len(qa_pairs)
            }

            with open(vector_file_path, 'wb') as f:
                pickle.dump(vector_data, f)

            logger.info(f"Vector index created successfully: {vector_file_path}")
            return str(vector_file_path)

        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            raise

    def search_similar_questions(self, query: str, knowledge_base_id: int, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        搜索相似问题
        Args:
            query: 查询问题
            knowledge_base_id: 知识库ID
            top_k: 返回结果数量
        Returns:
            相似问题列表，包含问题、答案和相似度分数
        """
        if top_k is None:
            top_k = self.max_results

        try:
            vector_file_path = self.storage_path / f"kb_{knowledge_base_id}_vectors.pkl"

            if not vector_file_path.exists():
                logger.warning(f"Vector file not found: {vector_file_path}")
                return []

            # 加载向量数据
            with open(vector_file_path, 'rb') as f:
                vector_data = pickle.load(f)

            # 反序列化FAISS索引
            index = faiss.deserialize_index(vector_data['index'])
            qa_pairs = vector_data['qa_pairs']

            # 对查询向量化
            query_embeddings = self._get_embeddings([query])
            query_vector = np.array(query_embeddings, dtype=np.float32)
            faiss.normalize_L2(query_vector)

            # 搜索相似向量
            scores, indices = index.search(query_vector, min(top_k, len(qa_pairs)))

            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0 and score >= self.similarity_threshold:
                    qa_pair = qa_pairs[idx]
                    results.append({
                        'questionid': qa_pair['questionid'],
                        'question': qa_pair['question'],
                        'answer': qa_pair['answer'],
                        'similarity_score': float(score),
                        'rank': i + 1
                    })

            logger.info(f"Found {len(results)} similar questions for query: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Failed to search similar questions: {e}")
            return []

    def save_original_file(self, file_content: bytes, knowledge_base_id: int, original_filename: str = None) -> str:
        """
        保存原始JSONL文件
        Args:
            file_content: 文件内容
            knowledge_base_id: 知识库ID
            original_filename: 原始文件名（可选）
        Returns:
            文件路径
        """
        # 如果提供了原始文件名，使用它；否则使用默认命名
        if original_filename:
            file_path = self.storage_path / f"kb_{knowledge_base_id}_{original_filename}"
        else:
            file_path = self.storage_path / f"kb_{knowledge_base_id}_original.jsonl"

        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"Original file saved: {file_path}")
        return str(file_path)

    def delete_knowledge_base_files(self, knowledge_base_id: int) -> None:
        """
        删除知识库相关文件
        Args:
            knowledge_base_id: 知识库ID
        """
        try:
            # 删除所有匹配的原始文件（支持新旧命名格式）
            import glob
            pattern = str(self.storage_path / f"kb_{knowledge_base_id}_*.jsonl")
            original_files = glob.glob(pattern)
            for file_path in original_files:
                os.unlink(file_path)
                logger.info(f"Deleted original file: {file_path}")
            
            # 如果没有找到新格式的文件，尝试删除旧格式的文件
            if not original_files:
                original_file = self.storage_path / f"kb_{knowledge_base_id}_original.jsonl"
                if original_file.exists():
                    original_file.unlink()
                    logger.info(f"Deleted original file: {original_file}")

            # 删除向量文件
            vector_file = self.storage_path / f"kb_{knowledge_base_id}_vectors.pkl"
            if vector_file.exists():
                vector_file.unlink()
                logger.info(f"Deleted vector file: {vector_file}")

        except Exception as e:
            logger.error(f"Failed to delete knowledge base files: {e}")
            raise

    def get_file_info(self, knowledge_base_id: int) -> Dict[str, Any]:
        """
        获取知识库文件信息
        Args:
            knowledge_base_id: 知识库ID
        Returns:
            文件信息字典
        """
        info = {
            'original_file_exists': False,
            'vector_file_exists': False,
            'original_file_size': 0,
            'vector_file_size': 0,
            'total_qa_pairs': 0
        }

        try:
            # 检查原始文件（支持新旧命名格式）
            import glob
            pattern = str(self.storage_path / f"kb_{knowledge_base_id}_*.jsonl")
            original_files = glob.glob(pattern)
            
            if original_files:
                # 使用第一个找到的文件
                original_file = Path(original_files[0])
                info['original_file_exists'] = True
                info['original_file_size'] = original_file.stat().st_size
            else:
                # 尝试旧格式
                original_file = self.storage_path / f"kb_{knowledge_base_id}_original.jsonl"
                if original_file.exists():
                    info['original_file_exists'] = True
                    info['original_file_size'] = original_file.stat().st_size

            # 检查向量文件
            vector_file = self.storage_path / f"kb_{knowledge_base_id}_vectors.pkl"
            if vector_file.exists():
                info['vector_file_exists'] = True
                info['vector_file_size'] = vector_file.stat().st_size

                # 获取问答对数量
                with open(vector_file, 'rb') as f:
                    vector_data = pickle.load(f)
                    info['total_qa_pairs'] = vector_data.get('total_pairs', 0)

        except Exception as e:
            logger.error(f"Failed to get file info: {e}")

        return info

# 全局实例
knowledge_base_service = KnowledgeBaseService()