import asyncio
from itertools import cycle

import httpx


loop = asyncio.new_event_loop()
futures = {}


async def send_message(token, chat_id, delay, message_pool, proxy):
    proxy_data = None
    if proxy:
        proxy_adress, proxy_port, proxy_login, proxy_pwd = proxy.split(':')
        proxy_data = f'http://{proxy_login}:{proxy_pwd}@{proxy_adress}:{proxy_port}'
    message_pool = cycle(message_pool)
    async with httpx.AsyncClient(proxies=proxy_data) as client:
        for message in message_pool:
            try:
                client.headers.update({'authorization': token})
                payload = {'content': message}
                await client.post(f'https://discordapp.com/api/v9/channels/{chat_id}/messages',
                                  json=payload)
                await asyncio.sleep(float(delay))

            except asyncio.CancelledError:
                break
