#!/usr/bin/env python

from logging import Logger, getLogger
from asyncio import run as asyncio_run, start_server
from typing import NoReturn, Type
from functools import partial
from logging.handlers import TimedRotatingFileHandler
from logging import INFO, DEBUG, StreamHandler

from ecs_tools_py import make_log_handler

from http_mirror_server import handle
from http_mirror_server.cli import HTTPMirrorServerArgumentParser

LOG: Logger = getLogger(__name__)


async def main() -> NoReturn:
    args: Type[HTTPMirrorServerArgumentParser.Namespace] = HTTPMirrorServerArgumentParser().parse_args()

    provider_name = 'HTTP Mirror Server'

    if args.log_directory:
        log_handler = make_log_handler(
            base_class=TimedRotatingFileHandler,
            provider_name=provider_name
        )(filename=(args.log_directory / 'http_mirror_server.log'), when='D')
    else:
        log_handler = StreamHandler()

    LOG.addHandler(hdlr=log_handler)
    LOG.setLevel(level=DEBUG)

    from http_mirror_server import LOG as HTTP_MIRROR_SERVER_LOG

    HTTP_MIRROR_SERVER_LOG.addHandler(hdlr=log_handler)
    HTTP_MIRROR_SERVER_LOG.setLevel(level=DEBUG)

    start_server_options = dict(
        client_connected_cb=partial(handle, public_suffix_list_trie=args.public_suffix_list_trie),
        host=args.host,
        port=args.port
    )
    async with await start_server(**start_server_options) as http_server:
        LOG.info(msg=f'Running server on host "{args.host}" on port "{args.port}"...')
        await http_server.serve_forever()


if __name__ == '__main__':
    asyncio_run(main())
