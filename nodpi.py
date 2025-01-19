import asyncio
from random import randint
from logging import getLogger, basicConfig, DEBUG


log = getLogger(__name__)
basicConfig(level=DEBUG)
BLOCKED = [line.rstrip().encode() for line in open('blacklist.txt', 'r', encoding='utf-8')]
TASKS = []


async def pipe(reader, writer):

    while not reader.at_eof() and not writer.is_closing():
        try:
            writer.write(await reader.read(1500))
            await writer.drain()
        except:
            break

    writer.close()


async def fragemtn_data(local_reader, remote_writer):

    head = await local_reader.read(5)
    data = await local_reader.read(1500)
    parts = []

    if all([data.find(site) == -1 for site in BLOCKED]):
        remote_writer.write(head + data)
        await remote_writer.drain()

        return

    while data:
        part_len = randint(1, len(data))
        parts.append(bytes.fromhex("1603") + bytes([randint(0, 255)]) + int(
            part_len).to_bytes(2, byteorder='big') + data[0:part_len])

        data = data[part_len:]

    remote_writer.write(b''.join(parts))
    await remote_writer.drain()


async def new_conn(local_reader, local_writer):
    http_data = await local_reader.read(1500)
    log.debug(http_data)
    try:
        type, target = http_data.split(b"\r\n")[0].split(b" ")[0:2]
        host, port = target.split(b":")
    except:
        local_writer.close()
        return

    if type != b"CONNECT":
        local_writer.close()
        return

    local_writer.write(b'HTTP/1.1 200 OK\n\n')
    await local_writer.drain()

    try:
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
    except:
        local_writer.close()
        return

    if port == b'443':
        await fragemtn_data(local_reader, remote_writer)

    TASKS.append(asyncio.create_task(pipe(local_reader, remote_writer)))
    TASKS.append(asyncio.create_task(pipe(remote_reader, local_writer)))


async def main(host, port):
    server = await asyncio.start_server(new_conn, host, port)
    log.info('HTTP-proxy started')
    await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main(host='127.0.0.1', port=8881))
