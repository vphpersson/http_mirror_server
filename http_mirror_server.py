#!/usr/bin/env python

from logging import Logger, getLogger
from asyncio import run as asyncio_run, start_unix_server
from typing import NoReturn, Type
from functools import partial
from logging.handlers import TimedRotatingFileHandler
from logging import INFO, StreamHandler

from ecs_tools_py import make_log_handler

from http_mirror_server import handle
from http_mirror_server.cli import HTTPMirrorServerArgumentParser
from http_mirror_server.environ import parse_environment

LOG: Logger = getLogger(__name__)


async def main() -> NoReturn:
    args: Type[HTTPMirrorServerArgumentParser.Namespace] = HTTPMirrorServerArgumentParser().parse_args()
    parse_environment(namespace=args)

    provider_name = 'HTTP Mirror Server'

    if args.log_directory:
        log_handler = make_log_handler(
            base_class=TimedRotatingFileHandler,
            provider_name=provider_name
        )(filename=(args.log_directory / 'http_mirror_server.log'), when='D')
    else:
        log_handler = StreamHandler()

    LOG.addHandler(hdlr=log_handler)
    LOG.setLevel(level=INFO)

    from http_mirror_server import LOG as HTTP_MIRROR_SERVER_LOG

    HTTP_MIRROR_SERVER_LOG.addHandler(hdlr=log_handler)
    HTTP_MIRROR_SERVER_LOG.setLevel(level=INFO)

    start_server_options = dict(
        client_connected_cb=partial(handle, public_suffix_list_trie=args.public_suffix_list_trie),
        path=str(args.socket_path)
    )
    async with await start_unix_server(**start_server_options) as http_server:
        LOG.info(msg=f'Running the server with the UNIX domain socket path "{args.socket_path}"...')
        args.socket_path.chmod(0o766)
        await http_server.serve_forever()


if __name__ == '__main__':
    asyncio_run(main())
