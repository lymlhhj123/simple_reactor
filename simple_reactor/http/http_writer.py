# coding: utf-8

from .form_data import FormData


class HttpHeaderWriter(object):

    def __init__(self, connection):

        self._conn = connection

    async def write(self, header):
        """write http header to server"""
        buffer = []
        for k, v in header.items():
            hdr = f"{k}: {v}\r\n"
            buffer.append(hdr.encode("ascii"))

        buffer.append(b"\r\n")

        protocol = self._conn.get_protocol()
        await protocol.write(b"".join(buffer))


class HttpBodyWriter(object):

    def __init__(self, connection):

        self._conn = connection
        self._protocol = self._conn.get_protocol()

    async def write(self, body, chunked=False):
        """write http body to server"""
        if chunked:
            await self._write_chunked_body(body)
        else:
            await self._protocol.write(body)

    async def _write_chunked_body(self, body):
        """write body as chunk data"""
        async for chunk in self._iter_chunk(body):
            if not chunk:
                break

            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")

            chunk_len = "{:x}".format(len(chunk)).encode("utf-8")
            await self._protocol.write(chunk_len)
            await self._protocol.write(b"\r\n")
            await self._protocol.write(chunk)
            await self._protocol.write(b"\r\n")

        # chunk end
        await self._protocol.write(b"0\r\n\r\n")

    async def _iter_chunk(self, body):
        """read a chunk of data"""
        if isinstance(body, FormData):
            boundary = body.boundary()
            async for field in body.iter_fields():
                chunk = [f"--{boundary}\r\n".encode("utf-8")]
                form_header = field.render_headers()
                chunk.append(form_header.encode("utf-8"))

                yield b"".join(chunk)

                data = field.data
                if hasattr(data, "read"):  # file object
                    async for chunk in self._iter_file_object(data):
                        yield chunk
                else:
                    yield data

            yield f"--{boundary}--\r\n".encode("utf-8")

        else:  # body has read() method
            async for chunk in self._iter_file_object(body):
                yield chunk

    @staticmethod
    async def _iter_file_object(f_obj):
        """async iter file like object"""
        while True:
            data = yield f_obj.read(4096)
            if not data:
                break

            yield data
