# Curses Demo

A demonstration of the use of curses with sockets.

* `client.py` -- The client program.
    * `interface.py` -- Provides the `curses` interface to the client.
    * `backend.py` -- Provides the `sockets` backend to the client.
* `server.py` -- A demo Echo server. Runs on `localhost` port `1234`.

## Usage

```
usage: client.py [-h] addr port

Curses-based socket client.

positional arguments:
  addr        The IP address of the server.
  port        The port on which the server listens.

optional arguments:
  -h, --help  show this help message and exit
```

## Notes

This can be used as a rudimentary MUD client, but it doesn't (yet) have color support.
