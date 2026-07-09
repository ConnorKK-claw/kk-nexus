"""统一 LLM 调用客户端：限流 + OTel trace + 复用 LLM 调度器。

P2-4: 收口 6 处 LLM 调用点，统一限流复用 + OTel trace 全链路追踪。
直接复用 LLMScheduler.call() 的完整限流+429+重试逻辑，
外层包 OTel span 记录 latency/status/error。

用法:
    from llm_client import call_llm
    content, usage = call_llm(
        messages=[{"role": "user", "content": "你好"}],
        trace_name="txtai_query.rag_synthesis",
    )
"""
import os
import sys
import time
from pathlib import Path

# 确保能导入同目录模块
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from otel_obs import get_tracer
from deepseek_scheduler import get_scheduler, P0_CRITICAL, P1_NORMAL, P2_LOW

DEFAULT_MODEL = "deepseek-chat"  # 或其他模型名


def call_llm(messages, model=DEFAULT_MODEL, priority=P2_LOW,
             temperature=0.1, max_tokens=4096, trace_name="llm_call"):
    """统一 LLM 调用入口。

    复用 deepseek_scheduler 的限流+429+重试逻辑，外层包 OTel span。

    Args:
        messages: OpenAI 格式消息列表 [{"role": ..., "content": ...}]
        model: 模型名（默认 deepseek-v4-flash，实际由 scheduler 单例决定）
        priority: 优先级 P0_CRITICAL / P1_NORMAL / P2_LOW（默认 P2_LOW，RAG 场景）
        temperature: 采样温度
        max_tokens: 最大生成 token 数
        trace_name: OTel span 名称（建议格式: 模块.场景）

    Returns:
        (content: str, usage: dict) — usage 可能为空 dict（scheduler 不返回 usage）

    Raises:
        RuntimeError: LLM 调用失败（重试耗尽）
    """
    tracer = get_tracer()
    scheduler = get_scheduler()
    t0 = time.time()

    with tracer.start_as_current_span(trace_name) as span:
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.priority", priority)
        span.set_attribute("llm.message_count", len(messages))
        span.set_attribute("llm.temperature", temperature)
        span.set_attribute("llm.max_tokens", max_tokens)

        try:
            success, result = scheduler.call(
                messages, priority=priority,
                temperature=temperature, max_tokens=max_tokens,
            )
            latency_ms = int((time.time() - t0) * 1000)
            span.set_attribute("llm.latency_ms", latency_ms)

            if success:
                span.set_attribute("llm.status", "ok")
                return result, {}
            else:
                span.set_attribute("llm.status", "error")
                span.record_exception(RuntimeError(result))
                raise RuntimeError(f"LLM 调用失败: {result}")
        except RuntimeError:
            raise
        except Exception as e:
            span.set_attribute("llm.status", "error")
            span.record_exception(e)
            raise RuntimeError(f"LLM 调用异常: {e}")


def get_quota_status():
    """获取当前 DeepSeek API 配额状态（透传 scheduler）。"""
    return get_scheduler().get_quota_status()

