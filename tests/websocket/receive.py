import websockets
import asyncio


async def handler(websocket):
    async for message in websocket:
        print(message)


async def main():
    async with websockets.serve(handler, "localhost", 1337):
        await asyncio.Future()


asyncio.run(main())
