#!/usr/bin/env python3
"""Simple Echo server."""

import selectors
import signal
import socket
import sys
import time

class EchoServer:
    def __init__(self):
        """Initialize the echo server."""
        self.sel = selectors.DefaultSelector()
        self.active = False

    def _accept(self, sock, mask):
        conn, addr = sock.accept()  # Should be ready
        (ip, port) = addr
        print(f"[+] New connection: {ip}:{port}")
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self._read)

    def _halt(self, sig, frame):
        """Terminate gracefully."""
        self.active = False

    def _read(self, conn, mask):
        data = conn.recv(1000)
        if data:
            print(f"[>] Echo: {data.decode()}")
            conn.send(data)
        else:
            print(f"[x] Connection terminated.")
            self.sel.unregister(conn)
            conn.close()

    def run(self):
        signal.signal(signal.SIGINT, self._halt)
        signal.signal(signal.SIGQUIT, self._halt)
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", 1234))
        sock.listen(100)
        sock.setblocking(False)
        self.sel.register(sock, selectors.EVENT_READ, self._accept)
        self.active = True
        while self.active:
            events = self.sel.select(timeout=1)
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
            time.sleep(0.1)
        sock.close()


EchoServer().run()
