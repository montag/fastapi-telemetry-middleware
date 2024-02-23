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

### Usage

```python
from fastapi import FastAPI
from fastapi_telemetry_middleware.telemetry_middleware import FastapiTelemetryMiddleware

app = FastAPI()
app.add_middleware(FastapiTelemetryMiddleware, app_name="my_fastapi_app")
```

The builtin metrics can be turned off via 
```python
app.add_middleware(..., enable_metrics=False)
```