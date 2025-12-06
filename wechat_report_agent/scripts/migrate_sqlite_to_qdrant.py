#!/usr/bin/env python3
"""
migrate_sqlite_to_qdrant.py

一个小工具，用于将本地 `prompt_templates.db`（作为 SQLite 回退）中的 `collected_article` 行
迁移到 Qdrant 集合中。

功能：
- 从 SQLite 读取行并为每行拼接文本。
- 使用 sentence-transformers 计算向量嵌入（默认模型为 `all-MiniLM-L6-v2`）。
- 创建或重建 Qdrant 集合，并将向量及其元数据 upsert 到集合中。

用法（示例）：
    python migrate_sqlite_to_qdrant.py --db /path/to/prompt_templates.db \
            --qdrant http://localhost:6333 --collection collected_articles --overwrite

依赖：
    pip install qdrant-client sentence-transformers

如果未安装 sentence-transformers，脚本会提示如何安装。
"""
from __future__ import annotations
import os
import sys
import argparse
import sqlite3
from typing import List, Dict


def parse_args():
    p = argparse.ArgumentParser(description='将 collected_article 从 SQLite 迁移到 Qdrant')
    p.add_argument('--db', default=None, help='SQLite 数据库路径（默认使用本文件旁的 prompt_templates.db）')
    p.add_argument('--qdrant', default=os.environ.get('QDRANT_URL', 'http://localhost:6333'), help='Qdrant 服务地址')
    p.add_argument('--api-key', default=os.environ.get('QDRANT_API_KEY'), help='Qdrant API 密钥（可选）')
    p.add_argument('--collection', default='collected_articles', help='Qdrant 集合名称')
    p.add_argument('--model', default='all-MiniLM-L6-v2', help='sentence-transformers 模型名称')
    p.add_argument('--batch', type=int, default=64, help='批量 upsert 的批次大小')
    p.add_argument('--overwrite', action='store_true', help='重新创建集合（会删除已有数据）')
    return p.parse_args()


def find_default_db():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base, 'prompt_templates.db'),
        os.path.join(base, 'instance', 'prompt_templates.db'),
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.getsize(p) > 0:
            return p
    return candidates[0]


def load_articles(db_path: str) -> List[Dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT id, title, content, date, summary, source, create_time FROM collected_article')
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def embed_texts(texts: List[str], model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print('ERROR: sentence-transformers not available.', file=sys.stderr)
        print('Install with: pip install sentence-transformers', file=sys.stderr)
        raise
    model = SentenceTransformer(model_name)
    # 返回 numpy 数组列表
    embs = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embs


def main():
    args = parse_args()
    db_path = args.db or find_default_db()
    print('使用数据库：', db_path)
    if not os.path.exists(db_path):
        print('未找到数据库文件：', db_path, file=sys.stderr)
        sys.exit(2)

    rows = load_articles(db_path)
    print(f'从 collected_article 表加载到 {len(rows)} 条记录')
    if not rows:
        print('没有需要迁移的记录，退出。')
        return

    texts = []
    ids = []
    metas = []
    for r in rows:
        tid = r.get('id')
        title = r.get('title') or r.get('name') or ''
        content = r.get('content') or ''
        date = r.get('date') or r.get('create_time') or ''
        txt = f"{title}\n{date}\n{content}"
        texts.append(txt)
        ids.append(int(tid))
        metas.append({'title': title, 'date': date, 'source': r.get('source'), 'summary': r.get('summary')})

    print('使用模型计算嵌入：', args.model)
    try:
        embs = embed_texts(texts, args.model)
    except Exception as e:
        print('计算嵌入失败：', e, file=sys.stderr)
        sys.exit(3)

    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance, PointStruct
    except Exception as e:
        print('错误：未安装 qdrant-client 或导入失败。', file=sys.stderr)
        print('安装方法：pip install qdrant-client', file=sys.stderr)
        raise

    client = QdrantClient(url=args.qdrant, api_key=args.api_key)

    dim = len(embs[0])
    if args.overwrite:
        print('重新创建集合（将覆盖原有数据）：', args.collection)
        client.recreate_collection(collection_name=args.collection, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
    else:
        # 若集合不存在则创建
        try:
            client.get_collection(args.collection)
            print('集合已存在：', args.collection)
        except Exception:
            print('正在创建集合：', args.collection)
            client.recreate_collection(collection_name=args.collection, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))

    # 分批 upsert
    batch = args.batch
    from qdrant_client.models import PointStruct
    for i in range(0, len(ids), batch):
        chunk_ids = ids[i:i+batch]
        chunk_embs = embs[i:i+batch]
        chunk_meta = metas[i:i+batch]
        points = [PointStruct(id=int(_id), vector=vec.tolist() if hasattr(vec, 'tolist') else list(vec), payload=meta)
                  for _id, vec, meta in zip(chunk_ids, chunk_embs, chunk_meta)]
    resp = client.upsert(collection_name=args.collection, points=points)
    print(f'已 upsert {len(points)} 条向量，结果：', getattr(resp, 'status', 'ok'))

    print('迁移完成。已迁移', len(ids), '条记录到集合', args.collection)


if __name__ == '__main__':
    main()
