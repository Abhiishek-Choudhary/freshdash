import logging

import socketio
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, environ, auth):
    logger.info("Socket connected: %s", sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket disconnected: %s", sid)


@sio.on("subscribe:order")
async def subscribe_order(sid, data):
    order_id = data.get("orderId") or data.get("order_id")
    if order_id:
        await sio.enter_room(sid, f"order:{order_id}")


@sio.on("unsubscribe:order")
async def unsubscribe_order(sid, data):
    order_id = data.get("orderId") or data.get("order_id")
    if order_id:
        await sio.leave_room(sid, f"order:{order_id}")


def emit_order_update(order_id: str, status: str, message: str = ""):
    payload = {"orderId": order_id, "status": status}
    if message:
        payload["message"] = message
    event = f"order:{order_id}:update"
    room = f"order:{order_id}"
    try:
        async_to_sync(sio.emit)(event, payload, room=room)
    except Exception as exc:
        logger.warning("Socket emit failed: %s", exc)
