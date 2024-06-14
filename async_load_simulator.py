import asyncio

class AsyncLoadSimulator:
    def __init__(self, host='127.0.0.1', port=5025):
        self.host = host
        self.port = port
        self.commands = {
            "*IDN?": "Load Simulator, Model LS100, Serial 1234, Firmware 1.0",
            "SET:VALUE": "Load value set",
            "CURR?": "12",
            "VOLT?": "14",
            "POW?": "28"
        }

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connection from {addr}")

        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode().strip()
            print(f"Received command: {message}")

            response = self.commands.get(message, "ERROR: Unknown command")
            writer.write((response + '\n').encode())
            await writer.drain()

        print(f"Connection closed from {addr}")
        writer.close()
        await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = server.sockets[0].getsockname()
        print(f"Load Simulator started on {addr}")

        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    simulator = AsyncLoadSimulator()
    try:
        asyncio.run(simulator.start())
    except KeyboardInterrupt:
        print("Load Simulator stopped")
