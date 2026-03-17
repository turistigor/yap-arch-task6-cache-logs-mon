import asyncio as aio
import logging
import os

from httpx import AsyncClient, Response
from fastapi import FastAPI, HTTPException, Request, status
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from pydantic import BaseModel
from uvicorn import Config, Server
from uuid import UUID, uuid4

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s",
)
logger = logging.getLogger('shop-api')

host = os.environ.get('SHOP_API_HOST', '0.0.0.0')
port = os.environ.get('SHOP_API_PORT', 8000)
log_level = os.environ.get('SHOP_API_LOG_LEVEL', 'info')
mes_url = os.environ.get('MES_API_URL', 'http://127.0.0.1:8001')
otlp_collector_url = os.environ.get('OTLP_COLLECTOR_URL', 'jaeger:4317')

APP_NAME = 'Shop API'
app = FastAPI(title=APP_NAME)
app.state.mes_url = mes_url


otlp_exporter = OTLPSpanExporter(endpoint=otlp_collector_url, insecure=True)
sp = BatchSpanProcessor(otlp_exporter)
resource=Resource.create({SERVICE_NAME: 'Order'})
tp = TracerProvider(resource=resource)
tp.add_span_processor(sp)

trace.set_tracer_provider(tp)

FastAPIInstrumentor().instrument_app(app)
HTTPXClientInstrumentor().instrument()


class CreateOrderModel(BaseModel):
    user_id: int
    descr: str
    content: bytes


class CreateOrderRespModel(BaseModel):
    order_id: str
    user_id: int
    price: float


class CalcPriceModel(BaseModel):
    order_id: str
    content: str


@app.get('/healthcheck')
def healthcheck():
    return status.HTTP_200_OK


@app.post('/order')
async def create_order(order: CreateOrderModel, request: Request) -> CreateOrderRespModel:
    with trace.get_tracer(APP_NAME).start_as_current_span('Create order'):
        logger.info(f'Request received: create order ({order.user_id=}, {order.descr=})')

        order_id = uuid4()
        logger.info(f'Order created: {order_id}')

        base_url = request.app.state.mes_url
        with trace.get_tracer(APP_NAME).start_as_current_span('Get order price'):
            async with AsyncClient(base_url=base_url) as client:
                logger.info(f'Price calculation request sent {order_id=}')
                resp = await _send_calc_order_price(client, order_id, order.content)
                logger.info(f'Price calculation response ({order_id=}): {resp.status_code}')

        resp_data = resp.json()
        price = resp_data['price']

        logger.info(f'Request processed ({order.user_id=}, {order.descr=}, {order_id=}) ')
        return CreateOrderRespModel(order_id=str(order_id), user_id=order.user_id, price=price)


async def _send_calc_order_price(client: AsyncClient, order_id: UUID, content: str) -> Response:
    body = CalcPriceModel(order_id=str(order_id), content=content).model_dump()

    try:
        return await client.post('/price', json=body)
    except Exception as e:
        logger.error(f'MES request error: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'MES request error: {str(e)}',
        )


async def main():
    uvicorn_cfg = Config(app=app, host=host, port=port, log_level=log_level)
    server = Server(uvicorn_cfg)

    await server.serve()


if __name__ == '__main__':
    aio.run(main=main())
