# simple reactor

- io event notify library based on reactor mode, support epoll and select.
- current only support linux, kernel >= 4.14.
- python >= 3.8.5.
- support tcp, unix, udp, http/1.1 client.
- support coroutine, completely compatible with asyncio.


## example

### echo server

[echo server](example/echo/echo_server.py)

### echo client

[echo client](example/echo/echo_client.py)


### coroutine
####
[coroutine](example/coroutine/coroutine.py)

####
[lock](example/coroutine/lock.py)

####
[condition](example/coroutine/cond.py)

####
[queue](example/coroutine/queues.py)
