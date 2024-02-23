import time

from opentelemetry import trace
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware import _MiddlewareClass
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp, Receive, Scope, Send

APP_INFO = Gauge("fastapi_app_info", "App info", ["app_name"])
REQUESTS_COUNTER = Counter(
    "fastapi_requests_total", "Total count of requests by method and path.", ["method", "path", "app_name"]
)
RESPONSES = Counter(
    "fastapi_responses_total",
    "Total count of responses by method, path and status codes.",
    ["method", "path", "status_code", "app_name"],
)
REQUESTS_PROCESSING_TIME = Histogram(
    "fastapi_requests_duration_seconds",
    "Histogram of requests processing time by path (in seconds)",
    ["method", "path", "app_name"],
)
EXCEPTIONS = Counter(
    "fastapi_exceptions_total",
    "Total count of exceptions raised by path and exception type",
    ["method", "path", "exception_type", "app_name"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "fastapi_requests_in_progress",
    "Gauge of requests by method and path currently being processed",
    ["method", "path", "app_name"],
)


class FastapiTelemetryMiddleware(_MiddlewareClass):
    """Metrics and Tracing Middleware for ASGI applications

    Args:
        app (ASGI application): ASGI application
        app_name (str): the name of the application
        enable_metrics (bool): enable endpoint metrics capture
    """

    def __init__(self, app: ASGIApp, app_name: str = "fastapi_app", enable_metrics: bool = True) -> None:
        self.app = app
        self.app_name = app_name
        self.enable_metrics = enable_metrics
        if self.enable_metrics:
            APP_INFO.labels(app_name=self.app_name).inc()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        type = scope["type"]
        if type != "http":  # pragma: no cover
            await self.app(scope, receive, send)
            return

        response_status = None

        def send_wrapper(response):
            nonlocal response_status
            if response["type"] == "http.response.start":
                response_status = response["status"]
            return send(response)

        method = scope["method"]
        path = scope["path"]
        if self.enable_metrics:
            REQUESTS_IN_PROGRESS.labels(method=method, path=path, app_name=self.app_name).inc()
            REQUESTS_COUNTER.labels(method=method, path=path, app_name=self.app_name).inc()
        start_time = time.perf_counter()

        try:
            await self.app(scope, receive, send_wrapper)

        except BaseException as e:
            response_status = HTTP_500_INTERNAL_SERVER_ERROR
            if self.enable_metrics:
                EXCEPTIONS.labels(
                    method=method, path=path, exception_type=type(e).__name__, app_name=self.app_name
                ).inc()
            raise e from None

        else:
            end_time = time.perf_counter()
            span = trace.get_current_span()
            trace_id = trace.format_trace_id(span.get_span_context().trace_id)
            if self.enable_metrics:
                REQUESTS_PROCESSING_TIME.labels(method=method, path=path, app_name=self.app_name).observe(
                    end_time - start_time, exemplar={"TraceID": trace_id}
                )

        finally:
            if self.enable_metrics:
                RESPONSES.labels(method=method, path=path, status_code=response_status, app_name=self.app_name).inc()
                REQUESTS_IN_PROGRESS.labels(method=method, path=path, app_name=self.app_name).dec()
