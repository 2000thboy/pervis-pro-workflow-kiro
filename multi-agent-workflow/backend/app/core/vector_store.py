# -*- coding: utf-8 -*-
"""
向量数据库服务模块

提供语义搜索和相似度匹配功能，支持：
- ChromaDB 集成
- 文本向量化
- 相似度搜索
- 索引管理

Feature: multi-agent-workflow-core
Requirements: 3.4, 3.5
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


class VectorStoreProvider(Enum):
    """向量存储提供商"""
    CHROMA = "chroma"
    MOCK = "mock"  # 用于测试


@dataclass
class Document:
    """文档对象"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    @classmethod
    def create(cls, content: str, metadata: Optional[Dict[str, Any]] = None) -> "Document":
        """创建文档"""
        return cls(
            id=str(uuid4()),
            content=content,
            metadata=metadata or {}
        )


@dataclass
class SearchResult:
    """搜索结果"""
    document: Document
    score: float  # 相似度分数 (0-1, 越高越相似)
    distance: float  # 距离 (越小越相似)


@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    provider: VectorStoreProvider
    collection_name: str = "default"
    persist_directory: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    
    @classmethod
    def chroma(
        cls,
        collection_name: str = "default",
        persist_directory: Optional[str] = None
    ) -> "VectorStoreConfig":
        """创建ChromaDB配置"""
        return cls(
            provider=VectorStoreProvider.CHROMA,
            collection_name=collection_name,
            persist_directory=persist_directory
        )
    
    @classmethod
    def mock(cls, collection_name: str = "test") -> "VectorStoreConfig":
        """创建Mock配置"""
        return cls(
            provider=VectorStoreProvider.MOCK,
            collection_name=collection_name
        )


class BaseVectorStore(ABC):
    """向量存储基类"""
    
    def __init__(self, config: VectorStoreConfig):
        self.config = config
    
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """搜索相似文档"""
        pass
    
    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        pass
    
    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        pass
    
    @abstractmethod
    async def update_document(self, doc_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新文档"""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """获取文档数量"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """清空所有文档"""
        pass


class MockVectorStore(BaseVectorStore):
    """Mock向量存储（用于测试）"""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._documents: Dict[str, Document] = {}
    
    def _simple_similarity(self, query: str, content: str) -> float:
        """简单的相似度计算（基于词重叠）"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words or not content_words:
            return 0.0
        
        intersection = query_words & content_words
        union = query_words | content_words
        
        return len(intersection) / len(union) if union else 0.0
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档"""
        ids = []
        for doc in documents:
            self._documents[doc.id] = doc
            ids.append(doc.id)
        return ids
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """搜索相似文档"""
        results = []
        
        for doc in self._documents.values():
            # 应用元数据过滤
            if filter_metadata:
                match = all(
                    doc.metadata.get(k) == v
                    for k, v in filter_metadata.items()
                )
                if not match:
                    continue
            
            # 计算相似度
            similarity = self._simple_similarity(query, doc.content)
            distance = 1.0 - similarity
            
            results.append(SearchResult(
                document=doc,
                score=similarity,
                distance=distance
            ))
        
        # 按相似度排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return self._documents.get(doc_id)
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False
    
    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新文档"""
        if doc_id not in self._documents:
            return False
        
        doc = self._documents[doc_id]
        doc.content = content
        if metadata:
            doc.metadata.update(metadata)
        
        return True
    
    async def count(self) -> int:
        """获取文档数量"""
        return len(self._documents)
    
    async def clear(self) -> bool:
        """清空所有文档"""
        self._documents.clear()
        return True


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB向量存储"""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._client = None
        self._collection = None
        self._embedding_function = None
    
    def _get_client(self):
        """获取ChromaDB客户端"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                if self.config.persist_directory:
                    self._client = chromadb.PersistentClient(
                        path=self.config.persist_directory
                    )
                else:
                    self._client = chromadb.Client()
                    
            except ImportError:
                raise ImportError("请安装chromadb: pip install chromadb")
        
        return self._client
    
    def _get_collection(self):
        """获取集合"""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到ChromaDB"""
        collection = self._get_collection()
        
        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas
        )
        
        return ids
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """在ChromaDB中搜索"""
        collection = self._get_collection()
        
        where = filter_metadata if filter_metadata else None
        
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where
        )
        
        search_results = []
        
        if results and results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                doc = Document(
                    id=doc_id,
                    content=results['documents'][0][i] if results['documents'] else "",
                    metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                )
                
                distance = results['distances'][0][i] if results['distances'] else 0.0
                # 将距离转换为相似度分数 (cosine距离)
                score = 1.0 - distance
                
                search_results.append(SearchResult(
                    document=doc,
                    score=score,
                    distance=distance
                ))
        
        return search_results
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """从ChromaDB获取文档"""
        collection = self._get_collection()
        
        try:
            result = collection.get(ids=[doc_id])
            
            if result and result['ids']:
                return Document(
                    id=result['ids'][0],
                    content=result['documents'][0] if result['documents'] else "",
                    metadata=result['metadatas'][0] if result['metadatas'] else {}
                )
        except Exception:
            pass
        
        return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """从ChromaDB删除文档"""
        collection = self._get_collection()
        
        try:
            collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False
    
    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新ChromaDB中的文档"""
        collection = self._get_collection()
        
        try:
            collection.update(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata] if metadata else None
            )
            return True
        except Exception:
            return False
    
    async def count(self) -> int:
        """获取文档数量"""
        collection = self._get_collection()
        return collection.count()
    
    async def clear(self) -> bool:
        """清空集合"""
        client = self._get_client()
        
        try:
            client.delete_collection(self.config.collection_name)
            self._collection = None
            return True
        except Exception:
            return False


@dataclass
class AssetMatch:
    """素材匹配结果"""
    asset_id: str
    asset_name: str
    asset_type: str
    tags: List[str]
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorService:
    """
    向量搜索服务
    
    提供：
    - 文档索引管理
    - 语义搜索
    - 素材匹配
    - 标签向量化
    """
    
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        self.config = config or VectorStoreConfig.mock()
        self._store: Optional[BaseVectorStore] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化向量服务"""
        self._store = self._create_store()
        self._initialized = True
        logger.info(f"向量服务初始化完成: provider={self.config.provider.value}")
        return True
    
    def _create_store(self) -> BaseVectorStore:
        """创建向量存储"""
        if self.config.provider == VectorStoreProvider.CHROMA:
            return ChromaVectorStore(self.config)
        else:
            return MockVectorStore(self.config)
    
    @property
    def store(self) -> BaseVectorStore:
        """获取向量存储"""
        if self._store is None:
            self._store = self._create_store()
        return self._store
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    # === 文档管理 ===
    
    async def index_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        索引单个文档
        
        Args:
            content: 文档内容
            metadata: 元数据
            doc_id: 文档ID（可选）
        
        Returns:
            文档ID
        """
        doc = Document(
            id=doc_id or str(uuid4()),
            content=content,
            metadata=metadata or {}
        )
        
        ids = await self.store.add_documents([doc])
        return ids[0]
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        批量索引文档
        
        Args:
            documents: 文档列表，每个包含 content 和可选的 metadata
        
        Returns:
            文档ID列表
        """
        docs = []
        for doc_data in documents:
            doc = Document(
                id=doc_data.get("id", str(uuid4())),
                content=doc_data["content"],
                metadata=doc_data.get("metadata", {})
            )
            docs.append(doc)
        
        return await self.store.add_documents(docs)
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        语义搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
        
        Returns:
            搜索结果列表
        """
        return await self.store.search(query, top_k, filter_metadata)
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return await self.store.get_document(doc_id)
    
    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        return await self.store.delete_document(doc_id)
    
    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新文档"""
        return await self.store.update_document(doc_id, content, metadata)
    
    # === 素材索引和匹配 (Requirements 3.4, 3.5) ===
    
    async def index_asset(
        self,
        asset_id: str,
        asset_name: str,
        asset_type: str,
        tags: List[str],
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        索引素材
        
        Args:
            asset_id: 素材ID
            asset_name: 素材名称
            asset_type: 素材类型
            tags: 标签列表
            description: 描述
            metadata: 额外元数据
        
        Returns:
            文档ID
        """
        # 构建可搜索的内容
        content_parts = [asset_name, description]
        content_parts.extend(tags)
        content = " ".join(filter(None, content_parts))
        
        # 构建元数据
        doc_metadata = {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "asset_type": asset_type,
            "tags": ",".join(tags),
            **(metadata or {})
        }
        
        return await self.index_document(
            content=content,
            metadata=doc_metadata,
            doc_id=f"asset_{asset_id}"
        )
    
    async def index_assets(self, assets: List[Dict[str, Any]]) -> List[str]:
        """
        批量索引素材
        
        Args:
            assets: 素材列表
        
        Returns:
            文档ID列表
        """
        ids = []
        for asset in assets:
            doc_id = await self.index_asset(
                asset_id=asset["id"],
                asset_name=asset["name"],
                asset_type=asset.get("type", "unknown"),
                tags=asset.get("tags", []),
                description=asset.get("description", ""),
                metadata=asset.get("metadata")
            )
            ids.append(doc_id)
        return ids
    
    async def match_assets(
        self,
        query: str,
        asset_type: Optional[str] = None,
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[AssetMatch]:
        """
        匹配素材（Requirements 3.5）
        
        Args:
            query: 搜索查询（场景描述、关键词等）
            asset_type: 素材类型过滤
            top_k: 返回数量
            min_score: 最小相似度分数
        
        Returns:
            匹配的素材列表
        """
        filter_metadata = None
        if asset_type:
            filter_metadata = {"asset_type": asset_type}
        
        results = await self.search(query, top_k, filter_metadata)
        
        matches = []
        for result in results:
            if result.score < min_score:
                continue
            
            metadata = result.document.metadata
            
            # 解析标签
            tags_str = metadata.get("tags", "")
            tags = tags_str.split(",") if tags_str else []
            
            match = AssetMatch(
                asset_id=metadata.get("asset_id", result.document.id),
                asset_name=metadata.get("asset_name", ""),
                asset_type=metadata.get("asset_type", "unknown"),
                tags=tags,
                score=result.score,
                metadata={k: v for k, v in metadata.items() 
                         if k not in ["asset_id", "asset_name", "asset_type", "tags"]}
            )
            matches.append(match)
        
        return matches
    
    async def find_similar_assets(
        self,
        asset_id: str,
        top_k: int = 5
    ) -> List[AssetMatch]:
        """
        查找相似素材
        
        Args:
            asset_id: 参考素材ID
            top_k: 返回数量
        
        Returns:
            相似素材列表
        """
        doc = await self.get_document(f"asset_{asset_id}")
        if not doc:
            return []
        
        # 使用文档内容搜索相似素材
        results = await self.search(doc.content, top_k + 1)
        
        # 排除自身
        matches = []
        for result in results:
            if result.document.id == f"asset_{asset_id}":
                continue
            
            metadata = result.document.metadata
            tags_str = metadata.get("tags", "")
            tags = tags_str.split(",") if tags_str else []
            
            match = AssetMatch(
                asset_id=metadata.get("asset_id", result.document.id),
                asset_name=metadata.get("asset_name", ""),
                asset_type=metadata.get("asset_type", "unknown"),
                tags=tags,
                score=result.score,
                metadata={}
            )
            matches.append(match)
            
            if len(matches) >= top_k:
                break
        
        return matches
    
    # === 场景搜索词条生成 (Requirements 3.4) ===
    
    async def generate_scene_search_terms(
        self,
        scene_description: str,
        existing_tags: Optional[List[str]] = None
    ) -> List[str]:
        """
        生成场景搜索词条
        
        Args:
            scene_description: 场景描述
            existing_tags: 已有标签（用于扩展）
        
        Returns:
            搜索词条列表
        """
        # 基础分词
        terms = scene_description.split()
        
        # 添加已有标签
        if existing_tags:
            terms.extend(existing_tags)
        
        # 去重并过滤空值
        unique_terms = list(set(filter(None, terms)))
        
        return unique_terms
    
    # === 统计和管理 ===
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        count = await self.store.count()
        
        return {
            "provider": self.config.provider.value,
            "collection_name": self.config.collection_name,
            "document_count": count,
            "initialized": self._initialized
        }
    
    async def clear(self) -> bool:
        """清空所有数据"""
        return await self.store.clear()


# 全局向量服务实例
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """获取全局向量服务实例"""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service


def set_vector_service(service: VectorService):
    """设置全局向量服务实例"""
    global _vector_service
    _vector_service = service
