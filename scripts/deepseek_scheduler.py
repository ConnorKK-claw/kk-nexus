"""LLM API 调度器：限流器 + 优先级队列 + 自适应退避

通用调度器，适用于任何 LLM API 调用场景。
支持令牌桶限流、自适应退避、优先级调度和配额监控。

核心机制：
1. 令牌桶限流：滑动窗口限制 API 调用频率（可配置）
2. 自适应退避：429 时退避 max(Retry-After, base*2^retry)，上限可配置
3. 连续 429 检测：连续超限时暂停队列
4. 优先级调度：P0 > P1 > P2（根据场景自定义）
"""
import os
import time
import threading
import httpx
from collections import deque
from datetime import datetime
from pathlib import Path

# === 限流配置（根据你的 API 限制调整） ===
RATE_LIMIT_WINDOW = 600          # 滑动窗口大小（秒）
RATE_LIMIT_MAX_CALLS = 35        # 窗口内最大调用次数（建议预留余量）
MAX_RETRY = 3                    # 最大重试次数
BASE_BACKOFF = 60                # 基础退避（秒）
MAX_BACKOFF = 600                # 最大退避（秒）
CONSECUTIVE_429_PAUSE = 600      # 连续 429 暂停时长（秒）
CONSECUTIVE_429_THRESHOLD = 3    # 触发暂停的连续 429 次数

# === 优先级常量 ===
P0_CRITICAL = 0   # 高优先级（如决策/裁决节点）
P1_NORMAL = 1     # 普通优先级（如常规分析节点）
P2_LOW = 2        # 低优先级（如 RAG 合成/批量任务）


class LLMScheduler:
    """通用 LLM API 调度器（线程安全单例）"""

    def __init__(self, api_key="", base_url="https://api.openai.com/v1",
                 model="gpt-4o"):
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self._lock = threading.Lock()
        self._call_timestamps = deque()
        self._consecutive_429 = 0
        self._paused_until = 0.0
        self._client = httpx.Client(timeout=120)
        self._error_log = None

    def set_error_log(self, path: Path):
        """设置错误日志路径。"""
        self._error_log = path

    def _wait_for_quota(self):
        """等待限流窗口腾出配额，返回需等待的秒数。"""
        with self._lock:
            now = time.time()
            if now < self._paused_until:
                return self._paused_until - now
            cutoff = now - RATE_LIMIT_WINDOW
            while self._call_timestamps and self._call_timestamps[0] < cutoff:
                self._call_timestamps.popleft()
            if len(self._call_timestamps) >= RATE_LIMIT_MAX_CALLS:
                wait = self._call_timestamps[0] + RATE_LIMIT_WINDOW - now + 0.1
                return max(wait, 0)
            return 0

    def _record_call(self):
        with self._lock:
            self._call_timestamps.append(time.time())

    def _handle_429(self, retry_after=None):
        with self._lock:
            self._consecutive_429 += 1
            if self._consecutive_429 >= CONSECUTIVE_429_THRESHOLD:
                self._paused_until = time.time() + CONSECUTIVE_429_PAUSE
                self._log_error(f"连续 {self._consecutive_429} 次 429，暂停队列 {CONSECUTIVE_429_PAUSE}s")
                return CONSECUTIVE_429_PAUSE
            backoff = max(retry_after or BASE_BACKOFF,
                          BASE_BACKOFF * (2 ** (self._consecutive_429 - 1)))
            return min(backoff, MAX_BACKOFF)

    def _reset_429(self):
        with self._lock:
            self._consecutive_429 = 0

    def _log_error(self, msg):
        if self._error_log:
            try:
                self._error_log.parent.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry = f"\n- [{timestamp}] [scheduler] {msg}\n"
                with open(self._error_log, "a", encoding="utf-8") as f:
                    f.write(entry)
            except Exception:
                pass

    def call(self, messages, priority=P1_NORMAL, temperature=0.1, max_tokens=4096):
        """调用 LLM API（带限流 + 退避 + 重试）

        参数:
            messages: OpenAI 格式消息列表
            priority: 优先级 P0_CRITICAL / P1_NORMAL / P2_LOW
            temperature: 采样温度
            max_tokens: 最大生成 token 数

        返回:
            (success: bool, response_text_or_error: str)
        """
        for attempt in range(MAX_RETRY + 1):
            wait = self._wait_for_quota()
            if wait > 0:
                time.sleep(min(wait, MAX_BACKOFF))
            try:
                self._record_call()
                resp = self._client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    retry_after = int(retry_after) if retry_after else None
                    backoff = self._handle_429(retry_after)
                    if attempt < MAX_RETRY:
                        time.sleep(backoff)
                        continue
                    return False, f"429 Rate Limited（重试 {attempt} 次后仍失败）"
                resp.raise_for_status()
                data = resp.json()
                self._reset_429()
                return True, data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                self._log_error(f"HTTP {e.response.status_code}: {str(e)[:200]}")
                if attempt < MAX_RETRY:
                    time.sleep(BASE_BACKOFF)
                    continue
                return False, f"HTTP {e.response.status_code}: {str(e)[:200]}"
            except Exception as e:
                self._log_error(f"异常: {str(e)[:200]}")
                if attempt < MAX_RETRY:
                    time.sleep(BASE_BACKOFF)
                    continue
                return False, str(e)[:200]
        return False, "超过最大重试次数"

    def get_quota_status(self):
        """获取当前配额状态。"""
        with self._lock:
            now = time.time()
            cutoff = now - RATE_LIMIT_WINDOW
            while self._call_timestamps and self._call_timestamps[0] < cutoff:
                self._call_timestamps.popleft()
            used = len(self._call_timestamps)
            remaining = RATE_LIMIT_MAX_CALLS - used
            window_reset = (self._call_timestamps[0] + RATE_LIMIT_WINDOW - now
                            if self._call_timestamps else 0)
            paused = now < self._paused_until
            return {
                "used": used,
                "remaining": remaining,
                "max": RATE_LIMIT_MAX_CALLS,
                "window_reset_in": max(window_reset, 0),
                "paused": paused,
                "consecutive_429": self._consecutive_429,
            }


# === 全局单例 ===
_scheduler = None
_singleton_lock = threading.Lock()


def get_scheduler(api_key=None, base_url="https://api.deepseek.com/v1",
                  model="deepseek-chat"):
    """获取调度器单例（线程安全）

    API Key 优先级：参数 > 环境变量 LLM_API_KEY
    """
    global _scheduler
    if _scheduler is None:
        with _singleton_lock:
            if _scheduler is None:
                key = api_key or os.environ.get("LLM_API_KEY", "")
                _scheduler = LLMScheduler(key, base_url, model)
    return _scheduler


def reset_scheduler():
    """重置单例（用于测试）"""
    global _scheduler
    with _singleton_lock:
        _scheduler = None
