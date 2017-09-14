import asyncio
from concurrent import futures

listeners = {}


def on(prefix, handler, loop=None):
    loop = loop or asyncio.get_event_loop()

    assert callable(handler) or 'Handler must be a callable'

    listener = (
        prefix,
        handler,
        loop
    )

    if listener in listeners:
        raise RuntimeError('Listener already exists')

    listeners[listener] = []

    async def unsubscribe():
        tasks = listeners.pop(listener)
        await asyncio.gather(*tasks, loop=loop)

    return unsubscribe


def emit(name, payload):
    for listener, tasks in listeners.items():
        prefix, handler, loop = listener
        if not name.startswith(prefix):
            continue

        if asyncio.iscoroutinefunction(handler):
            future = asyncio.run_coroutine_threadsafe(handler(payload), loop)
            task = loop.run_in_executor(
                None,
                future.result
            )
            tasks.append(task)
        else:
            handler(payload)
