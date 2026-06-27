"""
向量嵌入服务：封装智谱 Embedding API，为章节语义检索提供支撑
"""
import json
import os
import hashlib
import requests
from typing import Dict, List, Optional, Any
import config


class EmbeddingService:
    """向量嵌入服务：文本转向量 + 相似度检索"""

    def __init__(self):
        self.api_key = config.EMBEDDING_API_KEY
        self.base_url = config.EMBEDDING_BASE_URL
        self.model = config.EMBEDDING_MODEL
        self._cache = {}  # 内存缓存：文本hash → 向量，避免重复请求

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def embed(self, text: str) -> Optional[List[float]]:
        """将单个文本转为向量"""
        if not self.is_available:
            return None
        if not text or not text.strip():
            return None

        cache_key = hashlib.md5(text.encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            resp = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": text
                },
                timeout=30
            )
            if resp.status_code != 200:
                print(f"[Embedding] API error {resp.status_code}: {resp.text[:200]}")
                return None

            data = resp.json()
            vector = data.get("data", [{}])[0].get("embedding")
            if vector:
                self._cache[cache_key] = vector
            return vector
        except Exception as e:
            print(f"[Embedding] request error: {e}")
            return None

    def batch_embed(self, texts: List[str]) -> List[Optional[List[float]]]:
        """批量文本转向量（逐个请求，避免单次长度超限）"""
        return [self.embed(t) for t in texts]

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """余弦相似度"""
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x ** 2 for x in a) ** 0.5
        norm_b = sum(x ** 2 for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search_similar(self, query: str, candidates: Dict[int, List[float]],
                       top_k: int = 5, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """在候选向量中搜索与 query 最相似的 top_k 项

        Args:
            query: 查询文本
            candidates: {chapter_number: embedding_vector}
            top_k: 返回条数
            min_score: 最低相似度阈值

        Returns:
            [{"chapter_number": N, "score": 0.85}, ...] 按相似度降序
        """
        query_vec = self.embed(query)
        if not query_vec:
            return []

        scored = []
        for ch_num, vec in candidates.items():
            score = self.cosine_similarity(query_vec, vec)
            if score >= min_score:
                scored.append({"chapter_number": ch_num, "score": round(score, 4)})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class ChapterEmbeddingStore:
    """章节向量存储：把 embedding 向量持久化到小说数据目录"""

    EMBEDDING_FILENAME = "chapter_embeddings.json"

    def __init__(self, novel_dir: str, embedding_service: EmbeddingService):
        self.novel_dir = novel_dir
        self.service = embedding_service
        self.filepath = os.path.join(novel_dir, self.EMBEDDING_FILENAME)

    def load(self) -> Dict[int, List[float]]:
        """加载已存储的章节向量，返回 {chapter_number: embedding}"""
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # key 从字符串转回 int
            return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"[EmbeddingStore] load error: {e}")
            return {}

    def save(self, embeddings: Dict[int, List[float]]):
        """保存章节向量"""
        try:
            os.makedirs(self.novel_dir, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({str(k): v for k, v in embeddings.items()}, f, ensure_ascii=False)
        except Exception as e:
            print(f"[EmbeddingStore] save error: {e}")

    def build_embedding_for_chapter(self, chapter_number: int, chapter_data: Dict[str, Any]):
        """为一章构建向量（摘要 + 关键事件合成一段文本），追加到存储"""
        parts = []
        title = chapter_data.get("title", "")
        summary = chapter_data.get("summary", "")
        key_events = chapter_data.get("key_events", [])

        if title:
            parts.append(f"标题：{title}")
        if summary:
            parts.append(f"概要：{summary}")
        if key_events:
            parts.append("关键事件：" + "；".join(key_events))

        text = "\n".join(parts)
        if not text.strip():
            return

        vec = self.service.embed(text)
        if vec:
            all_embeddings = self.load()
            all_embeddings[chapter_number] = vec
            self.save(all_embeddings)
            print(f"[EmbeddingStore] 第{chapter_number}章向量已保存，维度={len(vec)}")

    def backfill_chapters(self, existing_chapters: List[Dict[str, Any]]):
        """回填所有缺失向量的章节（在每次检索前调用，确保历史章节有向量）

        Args:
            existing_chapters: 所有已知章节数据，每项需含 chapter_number, title, summary, key_events
        """
        current_embeddings = self.load()
        backfilled = 0
        for ch in existing_chapters:
            ch_num = ch.get("chapter_number")
            if ch_num is None:
                continue
            if ch_num in current_embeddings:
                continue  # 已有向量，跳过
            self.build_embedding_for_chapter(ch_num, ch)
            backfilled += 1
        if backfilled:
            print(f"[EmbeddingStore] 回填了 {backfilled} 个缺失的章节向量")

    def search_relevant_chapters(self, query: str, current_chapter: int,
                                  top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索与 query 最相关的前 N 章（排除当前章）"""
        candidates = self.load()
        if not candidates:
            return []
        if current_chapter in candidates:
            del candidates[current_chapter]
        if not candidates:
            return []
        return self.service.search_similar(query, candidates, top_k=top_k)
