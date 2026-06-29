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


# ── Dynamic Knowledge Embedding Store ──

class DynamicKnowledgeEmbeddingStore:
    """动态知识向量存储：对 dynamic_knowledge 中每条记录做嵌入，实现语义检索

    每章保存后增量构建新条目的向量，agent 运行时用当前章节上下文做查询，
    只取回最相关的 top-K 条动态知识，避免 200+ 章后上下文爆炸。
    """

    EMBEDDING_FILENAME = "dynamic_knowledge_embeddings.json"

    def __init__(self, novel_dir: str, embedding_service: EmbeddingService):
        self.novel_dir = novel_dir
        self.service = embedding_service
        self.filepath = os.path.join(novel_dir, self.EMBEDDING_FILENAME)

    # ── 存储 ──

    def load(self) -> Dict[str, Dict[str, Any]]:
        """加载已存储的动态知识向量，返回 {doc_id: {embedding, type, chapter, text, importance}}"""
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[DynEmbedStore] load error: {e}")
            return {}

    def save(self, records: Dict[str, Dict[str, Any]]):
        """保存动态知识向量"""
        try:
            os.makedirs(self.novel_dir, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[DynEmbedStore] save error: {e}")

    # ── 文档构建 ──

    def _docs_from_dynamic_knowledge(self, dk: Dict[str, Any],
                                      only_chapter: int = None) -> List[Dict[str, Any]]:
        """从 dynamic_knowledge 中提取可嵌入的文档列表

        Args:
            dk: 完整的 dynamic_knowledge dict
            only_chapter: 仅提取指定章节的文档（增量构建时用），None 表示全量构建

        Returns:
            [{"id": "...", "type": "...", "chapter": N, "text": "...", "importance": "..."}, ...]
        """
        docs = []

        # 角色发展轨迹
        char_evo = dk.get("character_evolution", {})
        for name, records in char_evo.items():
            for r in records:
                ch = r.get("chapter_number", 0)
                if only_chapter is not None and ch != only_chapter:
                    continue
                desc = r.get("description", "")
                if desc:
                    docs.append({
                        "id": f"char_evo_{name}_ch{ch}",
                        "type": "character_evolution",
                        "chapter": ch,
                        "text": f"第{ch}章 {name}的角色发展: {desc[:300]}",
                        "importance": "high"
                    })

        # 情节时间线
        plot_timeline = dk.get("plot_timeline", [])
        for i, ev in enumerate(plot_timeline):
            ch = ev.get("chapter_number", 0)
            if only_chapter is not None and ch != only_chapter:
                continue
            desc = ev.get("description", "")
            if desc:
                docs.append({
                    "id": f"plot_ch{ch}_{i}",
                    "type": "plot_event",
                    "chapter": ch,
                    "text": f"第{ch}章 情节事件[{ev.get('event_type', 'plot')}]: {desc[:300]}",
                    "importance": ev.get("importance", "medium")
                })

        # 伏笔追踪
        foreshadowing = dk.get("foreshadowing_tracking", {})
        for ftype, flist in foreshadowing.items():
            for i, f in enumerate(flist):
                ch = f.get("chapter_number", 0)
                if only_chapter is not None and ch != only_chapter:
                    continue
                content = f.get("content", "")
                if content:
                    docs.append({
                        "id": f"foreshadow_{ftype}_ch{ch}_{i}",
                        "type": "foreshadowing",
                        "chapter": ch,
                        "text": f"第{ch}章 伏笔[{ftype}]: {content[:300]}",
                        "importance": f.get("importance", "medium"),
                        "status": f.get("status", "active")
                    })

        # 世界观变化
        world_changes = dk.get("world_changes", [])
        for i, wc in enumerate(world_changes):
            ch = wc.get("chapter_number", 0)
            if only_chapter is not None and ch != only_chapter:
                continue
            desc = wc.get("description", "")
            if desc:
                docs.append({
                    "id": f"world_ch{ch}_{i}",
                    "type": "world_change",
                    "chapter": ch,
                    "text": f"第{ch}章 世界观揭示[{wc.get('change_type', 'world')}]: {desc[:300]}",
                    "importance": "high"
                })

        # 章节摘要
        ch_summaries = dk.get("chapter_summaries", {})
        for ch_str, s in ch_summaries.items():
            ch = int(ch_str)
            if only_chapter is not None and ch != only_chapter:
                continue
            summary = s.get("summary", "")
            title = s.get("title", "")
            if summary:
                docs.append({
                    "id": f"summary_ch{ch}",
                    "type": "chapter_summary",
                    "chapter": ch,
                    "text": f"第{ch}章《{title}》: {summary[:300]}",
                    "importance": "high"
                })

        return docs

    # ── 构建/更新 ──

    def build_all_from_dynamic_knowledge(self, dk: Dict[str, Any]):
        """全量重建所有动态知识向量（用于首次初始化或数据修复）"""
        if not self.service.is_available:
            print("[DynEmbedStore] embedding service unavailable, skip")
            return

        docs = self._docs_from_dynamic_knowledge(dk)
        if not docs:
            print("[DynEmbedStore] no docs to embed")
            return

        texts = [d["text"] for d in docs]
        vectors = self.service.batch_embed(texts)
        records = self.load()
        new_count = 0

        for doc, vec in zip(docs, vectors):
            if vec:
                records[doc["id"]] = {
                    "embedding": vec,
                    "type": doc["type"],
                    "chapter": doc["chapter"],
                    "text": doc["text"],
                    "importance": doc.get("importance", "medium"),
                    "status": doc.get("status", "active")
                }
                new_count += 1

        self.save(records)
        print(f"[DynEmbedStore] built {new_count}/{len(docs)} vectors (total: {len(records)})")

    def build_for_chapter(self, chapter_number: int, dk: Dict[str, Any]):
        """增量构建指定章节的动态知识向量"""
        if not self.service.is_available:
            return

        docs = self._docs_from_dynamic_knowledge(dk, only_chapter=chapter_number)
        if not docs:
            return

        texts = [d["text"] for d in docs]
        vectors = self.service.batch_embed(texts)
        records = self.load()
        new_count = 0

        for doc, vec in zip(docs, vectors):
            if vec:
                records[doc["id"]] = {
                    "embedding": vec,
                    "type": doc["type"],
                    "chapter": doc["chapter"],
                    "text": doc["text"],
                    "importance": doc.get("importance", "medium"),
                    "status": doc.get("status", "active")
                }
                new_count += 1

        self.save(records)
        print(f"[DynEmbedStore] ch{chapter_number}: {new_count}/{len(docs)} vectors (total: {len(records)})")

    # ── 检索 ──

    def search(self, query: str, top_k: int = 15, min_score: float = 0.4,
               exclude_chapter: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """用 query 搜索最相关的动态知识条目，按类型分组返回

        Args:
            query: 查询文本（当前章节摘要/剧情方向）
            top_k: 最多返回条目数
            min_score: 最低相似度阈值
            exclude_chapter: 排除的章节号（通常是当前章，避免检索到刚写入的内容）

        Returns:
            {
                "character_evolution": [{text, chapter, score}, ...],
                "plot_events": [...],
                "foreshadowing": [...],
                "world_changes": [...],
                "chapter_summaries": [...]
            }
        """
        records = self.load()
        if not records:
            return {}

        query_vec = self.service.embed(query)
        if not query_vec:
            return {}

        # 构建候选向量
        candidates = {}
        for doc_id, doc in records.items():
            if exclude_chapter is not None and doc.get("chapter") == exclude_chapter:
                continue
            vec = doc.get("embedding")
            if vec:
                candidates[doc_id] = vec

        if not candidates:
            return {}

        # 逐个打分
        scored = []
        for doc_id, vec in candidates.items():
            score = self.service.cosine_similarity(query_vec, vec)
            if score >= min_score:
                scored.append((doc_id, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_k]

        # 按类型分组
        result = {
            "character_evolution": [],
            "plot_events": [],
            "foreshadowing": [],
            "world_changes": [],
            "chapter_summaries": []
        }

        for doc_id, score in top:
            doc = records[doc_id]
            item = {
                "text": doc.get("text", ""),
                "chapter": doc.get("chapter", 0),
                "score": round(score, 4),
                "importance": doc.get("importance", "medium")
            }
            dtype = doc.get("type", "")
            if dtype in result:
                result[dtype].append(item)

        return {k: v for k, v in result.items() if v}  # 去掉空列表
