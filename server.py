#!/usr/bin/env python3
# Subprocess / Websockets Example
# Kevin McCarthy introduced me to asyncio subprocess interactions: https://kevinmccarthy.org/2016/07/25/streaming-subprocess-stdin-and-stdout-with-asyncio-in-python/
# Peter Majko educated me on using queues: https://stackoverflow.com/q/40723047
import asyncio
import websockets

# Path to Python 3.6+ executable (e.g.: /usr/local/bin/python)
PYTHON_PATH = 'python'

# WARNING: If you change server IP/port, make sure to update console-form.html to match
# IP address websockets server should bind to
WS_SERVER_IP = '127.0.0.1'

# Port websockets server should bind to
WS_SERVER_PORT = 8000


class Subprocess:
    def __init__(self):
        self.incoming = asyncio.Queue()
        self.outgoing = asyncio.Queue()

    def run_until_complete(self, command, loop):
        asyncio.set_event_loop(loop)
        asyncio.get_event_loop().run_until_complete(self.stream(command))

    async def read_stream(self, stream):
        line = await stream.readline()
        return line

    async def put_stdout(self, line):
        data = {'severity': 'INFO', 'message': line}
        await self.outgoing.put(data)

    async def put_stderr(self, line):
        data = {'severity': 'ERROR', 'message': line}
        await self.outgoing.put(data)

    async def get_stdin_message(self):
        data = await self.incoming.get()
        return '{}\n'.format(data).encode('utf-8')

    def communicate_stdin(self, message):
        self.process.stdin.write(message)

    async def stream(self, command):
        self.process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        while True:
            # Subprocess input task - sends to stdin
            consumer_task = asyncio.ensure_future(self.get_stdin_message())

            # Subprocess output task - stdout
            producer_task_stdout = asyncio.ensure_future(
                self.read_stream(self.process.stdout))

            # Subprocess output task - stderr
            producer_task_stderr = asyncio.ensure_future(
                self.read_stream(self.process.stderr))

            # Task control structure
            done, pending = await asyncio.wait(
                [consumer_task, producer_task_stdout, producer_task_stderr],
                return_when=asyncio.FIRST_COMPLETED)

            # Communicate stdin to subprocess
            if consumer_task in done:
                message = consumer_task.result()
                self.communicate_stdin(message)
            else:
                consumer_task.cancel()

            # Add subprocess stdout line to outgoing queue
            if producer_task_stdout in done:
                line = producer_task_stdout.result()
                await self.put_stdout(line)
            else:
                producer_task_stdout.cancel()

            # Add subprocess stderr line to outgoing queue
            if producer_task_stderr in done:
                line = producer_task_stderr.result()
                await self.put_stdout(line)
            else:
                producer_task_stderr.cancel()


class Interface:
    def __init__(self, websocket, subprocess):
        self.ws = websocket
        self.sp = subprocess
        self.incoming = asyncio.Queue()
        self.outgoing = asyncio.Queue()

    def process_ws_message(self, data):
        if type(data) == dict:
            message = f"{data['severity']}: {data['message'].decode('utf-8')}"
        else:
            message = data
        return message

    async def get_incoming(self):
        message = await self.ws.recv()

        # Process incoming data
        await self.incoming.put(message)

    async def get_outgoing(self):
        # Fetch data from sp outgoing queue
        data = await self.sp.outgoing.get()

        # Process outgoing data
        message = self.process_ws_message(data)

        # Add outgoing message to ws outgoing queue
        await self.outgoing.put(message)

    async def consume(self):
        # Receive incoming data
        data = await self.incoming.get()
        # Add data to sp incoming queue
        await self.sp.incoming.put(data)

    async def produce(self):
        message = await self.outgoing.get()
        await self.ws.send(message)


class WebsocketServer:
    def __init__(self, subprocess):
        self.subprocess = subprocess

    def run_until_complete(self, loop):
        asyncio.set_event_loop(loop)
        ws_server = websockets.serve(
            self.handler,
            WS_SERVER_IP,
            WS_SERVER_PORT)
        asyncio.get_event_loop().run_until_complete(ws_server)

    async def handler(self, websocket, path):
        interface = Interface(websocket, self.subprocess)
        while True:
            # Web socket input task - sends to subprocess incoming queue
            consumer_task = asyncio.ensure_future(interface.get_incoming())

            # Web socket output task - sends to websocket client
            producer_task = asyncio.ensure_future(interface.get_outgoing())

            # Task control structure
            done, pending = await asyncio.wait(
                [consumer_task, producer_task],
                return_when=asyncio.FIRST_COMPLETED)

            # Get input from web socket client
            if consumer_task in done:
                await interface.consume()
            else:
                consumer_task.cancel()

            # Send output to web socket client
            if producer_task in done:
                await interface.produce()
            else:
                producer_task.cancel()


def main():
    # Establish event loop
    loop = asyncio.get_event_loop()
    # Craft command for subprocess
    command = [
        PYTHON_PATH,
        '-u',
        'process.py'
    ]
    # Create subprocess object
    subprocess = Subprocess()

    # Create ws_server object, providing access to subprocess
    ws_server = WebsocketServer(subprocess)
    ws_server.run_until_complete(loop)

    # Run subprocess object
    subprocess.run_until_complete(command, loop)

    # Keep loop going FOREVER
    loop.run_forever()


if __name__ == '__main__':
    main()
