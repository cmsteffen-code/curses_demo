"""Application backend."""

# This backend acts as a simple socket client, sending the data from the
# user and returning the data from the server.

from binascii import hexlify
import queue
import selectors
import socket
import string
import threading
import time


class Backend(threading.Thread):
    """Backend handler."""

    def __init__(self, input_queue, output_queue, addr, port):
        """Initialize the Backend handler."""
        threading.Thread.__init__(self)
        self.addr = addr
        self.port = port
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.selector = selectors.DefaultSelector()
        self.running = False

    def _connect(self):
        """Connect to the echo server."""
        try:
            sock = socket.socket()
            sock.settimeout(3)
            sock.connect((self.addr, self.port))
            sock.setblocking(False)
            self.selector.register(
                sock,
                selectors.EVENT_READ | selectors.EVENT_WRITE,
                self._handle_io
            )
            return True
        except (socket.gaierror, socket.timeout, ConnectionRefusedError):
            return False

    def _handle_io(self, sock, mask):
        """Handle input and output."""
        if mask & selectors.EVENT_WRITE:
            # Handle input from the user.
            try:
                input = self.input_queue.get_nowait()
                if input == ';quit':
                    self.running = False
                else:
                    sock.send(f"{input[:998]}\r\n".encode())
            except queue.Empty:
                pass
        if mask & selectors.EVENT_READ:
            # Handle output from the server.
            data = sock.recv(4096)
            if not data:
                self.running = False
            else:
                try:
                    data = data.decode()
                except UnicodeDecodeError:
                    output = str()
                    for byte in data:
                        output += (
                            chr(byte)
                            if byte in [ord(char) for char in string.printable]
                            else "\\x" + hexlify(bytes([byte])).decode()
                        )
                    data = output
                for line in data.split('\n'):
                    self.output_queue.put(line)
        if not self.running:
            self.selector.unregister(sock)

    def run(self):
        """Start the Backend handler."""
        self.running = self._connect()
        while self.running:
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
        self.output_queue.put(';quit')
