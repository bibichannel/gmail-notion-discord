import handles
import asyncio

async def call_async_function_every_three_minute():
    while True:
        await handles.handle()
        await asyncio.sleep(180)

if __name__ == '__main__':
    asyncio.run(call_async_function_every_three_minute())
