import asyncio

# --------------- Relay TCP Server Protocol class ---------------


class RelayServerProtocol(asyncio.Protocol):
    def __init__(self, relay):
        self.relay = relay

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
        print('Data received: {!r}'.format(message))

        if message.split('\n')[0] == 'open':
            self.relay.send_pulse(50)

        # print('Send: {!r}'.format(message))
        # self.transport.write(data)

        print('Close the client socket')
        self.transport.close()
