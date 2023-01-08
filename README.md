# libreactor

------------

- based on reactor mode io event notify library, support tcp/udp.

## example

### tcp server example

```javascript
# coding: utf-8

from libreactor import ServerContext
from libreactor import StreamReceiver
from libreactor import EventLoop


class MyProtocol(StreamReceiver):

    def msg_received(self, msg):
	
        self.send_msg(msg)


class MyContext(ServerContext):

    stream_protocol_cls = MyProtocol


ev = EventLoop()

ctx = MyContext()
ctx.listen_tcp(9527, ev)

ev.loop()
```

### tcp client example
```javascript
# coding: utf-8

from libreactor import ClientContext
from libreactor import StreamReceiver
from libreactor import EventLoop


class MyProtocol(StreamReceiver):

    def __init__(self):

        super(MyProtocol, self).__init__()
        self.ops = 0
        self._end = False

    def msg_received(self, msg):

        if self._end:
            self.close_connection()
            return

        self.ops += 1
        self.send_msg(msg)

    def start_test(self):

        start_time = self.event_loop.time()

        self.event_loop.call_later(60, self._count_down, start_time)

    def _count_down(self, start_time):

        end_time = self.event_loop.time()
        self._end = True
        ops = self.ops / (end_time - start_time)
        self.ctx.logger().info(f"ops: {ops}")


class MyContext(ClientContext):

    stream_protocol_cls = MyProtocol


def on_established(protocol):

    protocol.start_test()

    protocol.send_msg(b"hello")


ev = EventLoop()

ctx = MyContext()
ctx.set_established_callback(on_established)
ctx.connect_tcp(("127.0.0.1", 9527), ev)

ev.loop()
```

### task example
```javascript
# coding: utf-8

from libreactor import EventLoop


def call_after_5_sec():

    print(f"done: {call_after_5_sec.__name__}")


def call_every_10_sec():

    print(f"done: {call_every_10_sec.__name__}")


def call_at_10_clock():

    print(f"done: {call_at_10_clock.__name__}")


def call_event_day_at_2_clock():

    print(f"done: {call_event_day_at_2_clock.__name__}")


def call_now():

    print(f"done: {call_now.__name__}")


ev = EventLoop()

ev.call_soon(call_now)

ev.call_later(5, call_after_5_sec)

ev.call_every(10, call_every_10_sec)

ev.call_at("10:00:00", call_at_10_clock)

ev.call_every_ex("02:00:00", call_event_day_at_2_clock)

ev.loop()
```