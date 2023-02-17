# libreactor

- io event notify library based on reactor mode, support epoll and select.
- current only support linux, kernel >= 4.14.
- python >= 3.8.5.
- support tcp udp, not support unix domain for now.
- not support dns resolver for now.

## install

coming soon

## example

### echo server

[echo server](example/echo/echo_server.py)

### echo client

[echo client](example/echo/echo_client.py)

### msg server

[msg server](example/msg/msg_server.py)

### msg client

[msg client](example/msg/msg_client.py)

### task

[task](example/task/task.py)

## context

one client one context, one server one context.
