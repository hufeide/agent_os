#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量记忆服务

实现独立的向量存储和语义检索。

作者: Agent OS Team
"""

import threading
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("Warning: numpy and sklearn not installed. Vector memory will use simple string matching.")


@dataclass
class MemoryItem:
    """
    记忆项
    
    存储在向量记忆中的单个项。
    """
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class VectorMemoryService:
    """
    向量记忆服务
    
    提供向量化的知识存储和语义检索。
    """
    
    def __init__(self, embedding_dim: int = 768):
        """
        初始化向量记忆服务
        
        Args:
            embedding_dim: 向量维度
        """
        self._memories: Dict[str, MemoryItem] = {}
        self._embedding_dim = embedding_dim
        self._lock = threading.RLock()
        self._total_access = 0
    
    def add(self, content: str, embedding: Optional[List[float]] = None,
           metadata: Dict[str, Any] = None) -> str:
        """
        添加记忆项
        
        Args:
            content: 内容
            embedding: 向量表示（可选）
            metadata: 元数据
            
        Returns:
            记忆ID
        """
        import uuid
        
        memory_id = str(uuid.uuid4())
        
        if embedding is None and HAS_EMBEDDINGS:
            embedding = self._create_embedding(content)
        
        memory = MemoryItem(
            id=memory_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._memories[memory_id] = memory
        
        return memory_id
    
    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """
        获取记忆项
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            记忆项，如果不存在返回None
        """
        with self._lock:
            memory = self._memories.get(memory_id)
            if memory:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                self._total_access += 1
            return memory
    
    def search(self, query: str, top_k: int = 5,
              embedding: Optional[List[float]] = None) -> List[Tuple[MemoryItem, float]]:
        """
        语义搜索
        
        Args:
            query: 查询内容
            top_k: 返回结果数量
            embedding: 查询向量（可选）
            
        Returns:
            (记忆项, 相似度) 列表，按相似度降序排列
        """
        if not HAS_EMBEDDINGS:
            return self._simple_search(query, top_k)
        
        if embedding is None:
            embedding = self._create_embedding(query)
        
        with self._lock:
            if not self._memories:
                return []
            
            similarities = []
            query_vec = np.array([embedding])
            
            for memory in self._memories.values():
                if memory.embedding is not None:
                    memory_vec = np.array([memory.embedding])
                    similarity = cosine_similarity(query_vec, memory_vec)[0][0]
                    similarities.append((memory, similarity))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
    
    def _simple_search(self, query: str, top_k: int) -> List[Tuple[MemoryItem, float]]:
        """
        简单搜索（当没有向量库时使用）
        
        Args:
            query: 查询内容
            top_k: 返回结果数量
            
        Returns:
            (记忆项, 相似度) 列表
        """
        query_lower = query.lower()
        
        with self._lock:
            similarities = []
            
            for memory in self._memories.values():
                content_lower = memory.content.lower()
                
                if query_lower in content_lower:
                    similarity = query_lower.count(query_lower) / len(content_lower)
                    similarities.append((memory, similarity))
                else:
                    words_query = set(query_lower.split())
                    words_content = set(content_lower.split())
                    intersection = words_query & words_content
                    if intersection:
                        similarity = len(intersection) / len(words_query)
                        similarities.append((memory, similarity))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
    
    def _create_embedding(self, text: str) -> List[float]:
        """
        创建文本向量（简单实现）
        
        Args:
            text: 文本
            
        Returns:
            向量表示
        """
        if not HAS_EMBEDDINGS:
            return None
        
        words = text.lower().split()
        word_count = len(words)
        
        if word_count == 0:
            return [0.0] * self._embedding_dim
        
        word_to_idx = {word: idx % self._embedding_dim for idx, word in enumerate(set(words))}
        embedding = np.zeros(self._embedding_dim)
        
        for word in words:
            idx = word_to_idx[word]
            embedding[idx] += 1.0
        
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def update(self, memory_id: str, content: Optional[str] = None,
              embedding: Optional[List[float]] = None,
              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新记忆项
        
        Args:
            memory_id: 记忆ID
            content: 新内容（可选）
            embedding: 新向量（可选）
            metadata: 新元数据（可选）
            
        Returns:
            是否成功
        """
        with self._lock:
            if memory_id not in self._memories:
                return False
            
            memory = self._memories[memory_id]
            
            if content is not None:
                memory.content = content
                if embedding is None and HAS_EMBEDDINGS:
                    memory.embedding = self._create_embedding(content)
            
            if embedding is not None:
                memory.embedding = embedding
            
            if metadata is not None:
                memory.metadata.update(metadata)
            
            return True
    
    def delete(self, memory_id: str) -> bool:
        """
        删除记忆项
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        with self._lock:
            if memory_id in self._memories:
                del self._memories[memory_id]
                return True
            return False
    
    def get_all(self) -> List[MemoryItem]:
        """
        获取所有记忆项
        
        Returns:
            记忆项列表
        """
        with self._lock:
            return list(self._memories.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        with self._lock:
            return {
                "total_memories": len(self._memories),
                "total_access": self._total_access,
                "embedding_dim": self._embedding_dim,
                "has_embeddings": HAS_EMBEDDINGS
            }
    
    def clear(self) -> None:
        """清空所有记忆"""
        with self._lock:
            self._memories.clear()
            self._total_access = 0
    
    def export(self) -> List[Dict[str, Any]]:
        """
        导出所有记忆
        
        Returns:
            记忆字典列表
        """
        with self._lock:
            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "embedding": m.embedding,
                    "metadata": m.metadata,
                    "created_at": m.created_at.isoformat(),
                    "access_count": m.access_count,
                    "last_accessed": m.last_accessed.isoformat() if m.last_accessed else None
                }
                for m in self._memories.values()
            ]
    
    def import_memories(self, memories: List[Dict[str, Any]]) -> int:
        """
        导入记忆
        
        Args:
            memories: 记忆字典列表
            
        Returns:
            导入的数量
        """
        count = 0
        
        with self._lock:
            for mem_dict in memories:
                try:
                    memory = MemoryItem(
                        id=mem_dict["id"],
                        content=mem_dict["content"],
                        embedding=mem_dict.get("embedding"),
                        metadata=mem_dict.get("metadata", {}),
                        access_count=mem_dict.get("access_count", 0)
                    )
                    
                    if "created_at" in mem_dict:
                        memory.created_at = datetime.fromisoformat(mem_dict["created_at"])
                    
                    if "last_accessed" in mem_dict and mem_dict["last_accessed"]:
                        memory.last_accessed = datetime.fromisoformat(mem_dict["last_accessed"])
                    
                    self._memories[memory.id] = memory
                    count += 1
                except Exception as e:
                    print(f"Error importing memory: {e}")
        
        return count