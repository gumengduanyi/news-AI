import os
import sqlite3
import logging

logger = logging.getLogger('backend.db')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH_CANDIDATES = [
    os.path.join(BASE_DIR, 'prompt_templates.db'),
    os.path.join(BASE_DIR, 'instance', 'prompt_templates.db'),
    os.path.join(BASE_DIR, '..', 'instance', 'prompt_templates.db'),
]


def _choose_db_path():
    for p in DB_PATH_CANDIDATES:
        if os.path.exists(p) and os.path.getsize(p) > 0:
            return p
    return os.path.join(BASE_DIR, 'prompt_templates.db')


_DB_PATH = _choose_db_path()


def get_db_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db_if_needed():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS prompt_template (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT
    );
    ''')
    try:
        c.execute("PRAGMA table_info(prompt_template)")
        cols = [r[1] for r in c.fetchall()]
        if 'title' not in cols and 'name' in cols:
            logger.info("prompt_template 表缺失 'title' 列，检测到旧列 'name'，开始添加并迁移数据")
            c.execute("ALTER TABLE prompt_template ADD COLUMN title TEXT")
            c.execute("UPDATE prompt_template SET title = name WHERE title IS NULL OR title = ''")
            conn.commit()
            logger.info("prompt_template 表列迁移完成：name -> title")
    except Exception as e:
        logger.exception('尝试迁移 prompt_template 表结构时出错：%s', e)

    c.execute('''
    CREATE TABLE IF NOT EXISTS collected_article (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT,
        title TEXT,
        date TEXT,
        content TEXT
    );
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS collect_task (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        meta TEXT
    );
    ''')
    conn.commit()
    conn.close()


def row_to_dict(row: sqlite3.Row):
    if row is None:
        return {}
    d = {k: row[k] for k in row.keys()}
    if 'name' in d and 'title' not in d:
        d['title'] = d['name']
    return d
