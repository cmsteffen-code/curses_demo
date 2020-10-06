#!/usr/bin/env python3

"""Curses-based socket client."""

import argparse
from backend import Backend
from interface import UserInterface

if __name__ == "__main__":
    # Get required information.
    parser = argparse.ArgumentParser(
        description="Curses-based socket client.",
    )
    parser.add_argument("addr", type=str, help="The IP address of the server.")
    parser.add_argument("port", type=int, help="The port on which the server listens.")
    args = parser.parse_args()
    # Initialize the interface.
    iface = UserInterface()
    (input_queue, output_queue) = iface.get_io()
    # Spawn the socket client.
    socket_client = Backend(
        input_queue, output_queue, args.addr, args.port
    )
    socket_client.start()
    iface.launch()
    input_queue.put(";quit")
    socket_client.join()
