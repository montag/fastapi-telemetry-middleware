# Fastapi-telemetry-middleware

This is a pure-ASGI middleware that adds Prometheus metrics and OpenTelemetry traces to fastapi routes automatically.

This middleware will add trace exemplars to the gathered metrics for cross-referencing in your observability platform. 

This middleware was inspired by:

* [Fastapi-observability](https://github.com/Blueswen/fastapi-observability) 
* [Starlette-Prometheus](https://github.com/perdy/starlette-prometheus/tree/master)

### Requirements

* Python 3.10+
* Starlette 0.27.0+
* Python-client 0.19.0+

Note: OpenTelemetry for Python should be installed in your client app along with the desired exporter. 

See: https://opentelemetry.io/docs/languages/python/

### Installation

To install locally run:

```Bash
poetry install
```

### Example Usage 
This example uses the Otel exporter to push to an Otel collector for traces, and Prometheus Client for metrics scraped by Prom and send to Mimir.

```python
from fastapi import FastAPI
from fastapi_telemetry_middleware.telemetry_middleware import FastapiTelemetryMiddleware

app = FastAPI()

app.add_middleware(
    FastapiTelemetryMiddleware,
    app_name=settings.PROJECT_NAME,
    enable_metrics=True)

setup_tracing(app=app,
              app_name=settings.PROJECT_NAME,
              otlp_endpoint=COLLECTOR)

setup_metrics(app, app_name=settings.PROJECT_NAME)
```

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from prometheus_client import make_asgi_app

from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider

from opentelemetry import trace


def setup_tracing(app: FastAPI, app_name: str = 'default_app', otlp_endpoint: str = 'http://localhost:4318'):
    resource = Resource(attributes={
        SERVICE_NAME: app_name

    })
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)
    exporter = OTLPSpanExporter(endpoint=f"${otlp_endpoint}/v1/traces")
    span_processor = BatchSpanProcessor(exporter)
    trace_provider.add_span_processor(span_processor)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider)
    

def setup_metrics(app: FastAPI, app_name: str = 'default_app'):
    resource = Resource(attributes={
        SERVICE_NAME: app_name
    })
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    reader = PrometheusMetricReader()
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    set_meter_provider(provider)
```
The builtin metrics can be turned off via
```python
app.add_middleware(..., enable_metrics=False)
```

### Note
If using a Prometheus client metrics endpoint in a public app, be sure to secure that endpoint.

### TODO
Eventually, I'll switch the metrics to Otel from Prom. 

