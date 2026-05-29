"""抓取运行日志：记录每次 run.py 各来源的成败、数量、卡住的步骤，

写入 news.db 的 run_logs 表（随 news.db 一起被 Actions 提交），
由 generate.py 读出渲染到网页「抓取日志」弹窗。

设计要点：
- run.py 全程 try/finally 调用 RunLog.save()，即使中途异常也能留下部分日志。
- 步骤命名与网页展示一致：后端连接 / 抓取 / AI 处理 / 完成。
"""
import json
import time
from datetime import datetime, timezone, timedelta

from storage import get_conn

_BJ_TZ = timezone(timedelta(hours=8))

# 步骤常量（卡在哪一步）
STEP_BACKEND = '后端连接'
STEP_FETCH   = '抓取'
STEP_PROCESS = 'AI 处理'
STEP_DONE    = '完成'

KEEP_RUNS = 30  # run_logs 表只保留最近 N 次


class SourceStat:
    """单个来源类别在一次运行中的统计。"""
    def __init__(self, name):
        self.name = name
        self.status = 'ok'        # ok | fail | empty
        self.step = STEP_DONE
        self.fetched = 0          # 原始抓取条数
        self.new = 0              # 去重后新处理条数
        self.kept = 0             # 通过相关度阈值（收录）条数
        self.dup = 0             # 已存在跳过条数
        self.proc_fail = 0        # AI 处理失败条数
        self.note = ''

    def to_dict(self):
        return {
            'name': self.name, 'status': self.status, 'step': self.step,
            'fetched': self.fetched, 'new': self.new, 'kept': self.kept,
            'dup': self.dup, 'proc_fail': self.proc_fail, 'note': self.note,
        }


class RunLog:
    def __init__(self):
        self._start = time.time()
        self.backends = {}        # name -> {'ok': bool, 'detail': str}
        self.sources = {}         # name -> SourceStat
        self.fatal = ''           # 致命异常信息（run.py 整体崩溃时）

    def backend(self, name, ok, detail=''):
        self.backends[name] = {'ok': bool(ok), 'detail': detail}

    def src(self, name) -> SourceStat:
        return self.sources.setdefault(name, SourceStat(name))

    def fail_source(self, name, step, note=''):
        s = self.src(name)
        s.status = 'fail'
        s.step = step
        if note:
            s.note = note

    def to_payload(self):
        now = datetime.now(timezone.utc)
        return {
            'run_at': now.isoformat(),
            'run_at_bj': now.astimezone(_BJ_TZ).strftime('%Y-%m-%d %H:%M'),
            'duration_sec': int(time.time() - self._start),
            'fatal': self.fatal,
            'backends': self.backends,
            'sources': [self.sources[k].to_dict() for k in self.sources],
        }

    def save(self):
        payload = self.to_payload()
        conn = get_conn()
        try:
            conn.execute('''CREATE TABLE IF NOT EXISTS run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT,
                payload TEXT
            )''')
            conn.execute('INSERT INTO run_logs (run_at, payload) VALUES (?, ?)',
                         (payload['run_at'], json.dumps(payload, ensure_ascii=False)))
            # 只保留最近 KEEP_RUNS 次
            conn.execute('''DELETE FROM run_logs WHERE id NOT IN
                (SELECT id FROM run_logs ORDER BY id DESC LIMIT ?)''', (KEEP_RUNS,))
            conn.commit()
        finally:
            conn.close()
        return payload


def load_recent(n=7):
    """返回最近 n 次运行日志（payload dict 列表，最新在前）。表不存在时返回 []。"""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT payload FROM run_logs ORDER BY id DESC LIMIT ?', (n,)
        ).fetchall()
    except Exception:
        return []
    finally:
        conn.close()
    out = []
    for r in rows:
        try:
            out.append(json.loads(r['payload']))
        except Exception:
            pass
    return out
