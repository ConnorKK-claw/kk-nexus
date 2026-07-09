"""OTel 可观测性模块。纯本地 JSONL 输出，无外部 service。

P2-4: 为 LLM 调用提供全链路 trace，写入 ~/.kk-otel/trace.jsonl。
失败时降级为 no-op tracer，不影响主流程。
"""
import json
from pathlib import Path

# OTel 可选依赖：未安装时降级为 no-op
_otel_available = False
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult
    _otel_available = True
except ImportError:
    _otel_available = False


class JSONLSpanExporter(SpanExporter if _otel_available else object):
    """把 span 写入 JSONL 文件，纯本地。"""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, spans):
        with open(self.output_path, "a", encoding="utf-8") as f:
            for s in spans:
                try:
                    f.write(json.dumps({
                        "trace_id": f"{s.context.trace_id:032x}",
                        "span_id": f"{s.context.span_id:016x}",
                        "name": s.name,
                        "start": s.start_time,
                        "end": s.end_time,
                        "attrs": dict(s.attributes or {}),
                        "status": s.status.status_code.name,
                        "error": s.status.description,
                    }, ensure_ascii=False) + "\n")
                except Exception:
                    continue
        return SpanExportResult.SUCCESS if _otel_available else None

    def shutdown(self):
        pass


# No-op tracer fallback（OTel 未安装时使用）
class _NoOpSpan:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def set_attribute(self, key, value):
        pass

    def record_exception(self, exc):
        pass

    def add_event(self, name, attributes=None):
        pass


class _NoOpTracer:
    def start_as_current_span(self, name):
        return _NoOpSpan()


_tracer = None
_initialized = False


def get_tracer(name="kk-nexus"):
    """获取 tracer 单例。OTel 未安装时返回 no-op tracer。"""
    global _tracer, _initialized
    if _initialized:
        return _tracer
    _initialized = True
    if not _otel_available:
        _tracer = _NoOpTracer()
        return _tracer
    try:
        provider = TracerProvider()
        output = Path.home() / ".kk-otel" / "trace.jsonl"
        provider.add_span_processor(BatchSpanProcessor(JSONLSpanExporter(output)))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(name)
    except Exception as e:
        print(f"[WARN] OTel 初始化失败，降级 no-op: {e}")
        _tracer = _NoOpTracer()
    return _tracer
