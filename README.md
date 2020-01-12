# Subprocess / Websockets Example

A very simple example of how an asyncio subprocess can be spawned with an interface provided by the websockets module.

- **server.py:** Script that runs the websockets server and subprocess
- **process.py:** Process spawned by subprocess call in server.py (sends timestamp to stdout at regular interval; echos lines received on stdin)
- **console-form.html:** HTML document that acts as a client interface

Modify python path, IP, and port settings in server.py. Update console-form.html to match connection settings (ws://127.0.0.1:8000 by default). Execute server.py and open console-form.html in a web browser that supports web socket connections. Observe that process stdout is presented in the textarea, and the process receives and handles user input submitted by the form.

This could be useful as an early base for browser based exposure of a process running on a server. Synchronized output still needs to be implemented. If multiple clients connect, any client can interact with the process, and stdout will "randomly" return to one of the connected websockets clients. Hints on synchronization can be found [here](https://websockets.readthedocs.io/en/stable/intro.html#synchronization-example)

Developed using Python 3.8.1 - untested on other versions
