import asyncio
import socket
import uvloop

from uvloop import _testbase as tb


class _TestSockets(tb.UVTestCase):

    async def recv_all(self, sock, nbytes):
        buf = []
        while len(buf) < nbytes:
            buf.append(await self.loop.sock_recv(sock, 1))
        return b''.join(buf)

    def test_socket_connect_recv_send(self):
        def srv_gen():
            yield tb.write(b'helo')
            data = yield tb.read(4)
            self.assertEqual(data, b'ehlo')
            yield tb.write(b'O')
            yield tb.write(b'K')

        async def client(sock, addr):
            await self.loop.sock_connect(sock, addr)
            data = await self.recv_all(sock, 4)
            self.assertEqual(data, b'helo')
            await self.loop.sock_sendall(sock, b'ehlo')
            data = await self.recv_all(sock, 2)
            self.assertEqual(data, b'OK')

        with tb.tcp_server(srv_gen) as srv:

            sock = socket.socket()
            with sock:
                sock.setblocking(False)
                self.loop.run_until_complete(client(sock, srv.addr))

    def test_socket_accept_recv_send(self):
        async def server():
            sock = socket.socket()
            sock.setblocking(False)

            with sock:
                sock.bind(('127.0.0.1', 0))
                sock.listen()

                fut = self.loop.run_in_executor(None, client,
                                                sock.getsockname())

                client_sock, _ = await self.loop.sock_accept(sock)

                with client_sock:
                    data = await self.recv_all(client_sock, 4)
                    self.assertEqual(data, b'aaaa')

                await fut

        def client(addr):
            sock = socket.socket()
            with sock:
                sock.connect(addr)
                sock.sendall(b'aaaa')

        self.loop.run_until_complete(server())


class TestUVSockets(_TestSockets, tb.UVTestCase):
    pass


class TestAIOSockets(_TestSockets, tb.AIOTestCase):
    pass