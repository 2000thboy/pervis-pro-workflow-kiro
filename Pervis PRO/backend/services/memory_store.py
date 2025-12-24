import os
from typing import List, Dict, Any, Optional

try:
    import chromadb
except Exception:
    chromadb = None

class MemoryStore:
    """
    向量记忆存储服务 (Vector Memory Store)
    Responsibility: 管理 AI 视觉特征向量的持久化存储与检索
    Backend: ChromaDB (Local Persisted)
    """
    
    def __init__(self):
        # 初始化存储路径
        self.persist_dir = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # 初始化 ChromaDB Client
        try:
            if chromadb is None:
                raise RuntimeError("ChromaDB 不可用")

            self.client = chromadb.PersistentClient(path=self.persist_dir)
            
            # 获取或创建集合 (Collection)
            # Collection Name: "visual_memory"
            # Distance Metric: "cosine" (余弦相似度)
            self.collection = self.client.get_or_create_collection(
                name="visual_memory",
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✅ 向量记忆库初始化成功: {self.persist_dir}")
            
        except Exception as e:
            print(f"❌ 向量记忆库初始化失败: {e}")
            self.client = None
            self.collection = None

    def add_memory(self, asset_id: str, vector: List[float], metadata: Dict[str, Any]):
        """
        添加/更新记忆
        :param asset_id: 唯一资产ID
        :param vector: 512维特征向量 (from CLIP)
        :param metadata: 关联元数据 (filename, timestamp, tags)
        """
        if not self.collection:
            return

        try:
            # ChromaDB 要求 ids, embeddings, metadatas 都是列表
            self.collection.upsert(
                ids=[asset_id],
                embeddings=[vector],
                metadatas=[metadata]
            )
            # print(f"📝 记忆已写入: {asset_id}")
            
        except Exception as e:
            print(f"❌ 记忆写入失败 ({asset_id}): {e}")

    def search_similar(self, query_vector: List[float], limit: int = 10) -> List[Dict]:
        """
        基于向量搜索相似内容
        :param query_vector: 查询向量
        :param limit: 返回数量
        :return: 结果列表
        """
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                include=["metadatas", "distances"]
            )
            
            # 格式化返回结果
            formatted_results = []
            if results and results['ids']:
                ids = results['ids'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for i in range(len(ids)):
                    formatted_results.append({
                        "id": ids[i],
                        "metadata": metadatas[i],
                        "score": 1 - distances[i]  # 转换为相似度分数 (Cosine Distance -> Similarity)
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 记忆检索失败: {e}")
            return []

    def get_stats(self) -> Dict:
        """获取记忆库统计信息"""
        if not self.collection:
            return {"count": 0, "status": "offline"}
            
        return {
            "count": self.collection.count(),
            "status": "online",
            "persist_dir": self.persist_dir
        }
