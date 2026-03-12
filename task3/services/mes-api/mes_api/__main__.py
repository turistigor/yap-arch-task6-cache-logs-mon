import asyncio as aio
import hashlib
import logging
import os
import random

from fastapi import FastAPI, status
from fastapi.logger import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel
from uvicorn import Config, Server

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s",
)
logger = logging.getLogger('mes-api')

host = os.environ.get('MES_API_HOST', '0.0.0.0')
port = os.environ.get('MES_API_PORT', 8001)
log_level = os.environ.get('MES_API_LOG_LEVEL', 'info')
otlp_collector_url = os.environ.get('OTLP_COLLECTOR_URL', 'jaeger:4317')

APP_NAME = 'MES API'
app = FastAPI(title=APP_NAME)

otlp_exporter = OTLPSpanExporter(endpoint=otlp_collector_url, insecure=True)
sp = BatchSpanProcessor(otlp_exporter)
resource=Resource.create({SERVICE_NAME: 'Price'})
tp = TracerProvider(resource=resource)
tp.add_span_processor(sp)

trace.set_tracer_provider(tp)

FastAPIInstrumentor.instrument_app(app)


class CreateOrderModel(BaseModel):
    order_id: str
    content: str


class OrderPriceModel(BaseModel):
    order_id: str
    price: float


@app.get('/healthcheck')
def healthcheck():
    return status.HTTP_200_OK


@app.post('/price')
async def calc_price(order: CreateOrderModel) -> OrderPriceModel:
    with trace.get_tracer(APP_NAME).start_as_current_span('Calc order price'):
        order_model_hash = hashlib.sha256(bytes(order.content, 'utf-8')).hexdigest()
        logger.info(
            f'Request received: calc order price ({order.order_id=}), '
            f'3D-model hash {order_model_hash}'
        )

        price = random.uniform(1.5, 5000.5)
        logger.info(f'Price calculated: {price} ({order.order_id=})')

        logger.info(f'Request processed ({order.order_id=})')
        return OrderPriceModel(order_id=order.order_id, price=price)


async def main():
    uvicorn_cfg = Config(app=app, host=host, port=port, log_level=log_level)
    server = Server(uvicorn_cfg)
    print(f'\n\n{host}---{port}\n\n')
    await server.serve()


if __name__ == '__main__':
    aio.run(main=main())
