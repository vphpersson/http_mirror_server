from logging import Logger, getLogger
from typing import TypedDict
from asyncio import StreamReader, StreamWriter
from json import loads as json_loads
from base64 import b64decode
from datetime import datetime

from public_suffix.structures.public_suffix_list_trie import PublicSuffixListTrie
from ecs_py import Base, Source, Event, Destination, Network
from ecs_tools_py import entry_from_http_message, merge_ecs_entries

from http_lib.structures.message import Request as HTTPRequest, Response as HTTPResponse, StatusLine


LOG: Logger = getLogger(__name__)


class HTTPMirrorRequest(TypedDict):
    raw_base64: str
    time: float


class HTTPMirrorResponse(TypedDict):
    headers: dict[str, str | list[str]]
    body_base64: str
    duration: str
    status: int


class HTTPMirrorEntry(TypedDict):
    server_addr: str
    server_port: str
    remote_addr: str
    remote_port: str
    scheme: str
    request: HTTPMirrorRequest
    response: HTTPMirrorResponse


async def handle(reader: StreamReader, writer: StreamWriter, public_suffix_list_trie: PublicSuffixListTrie | None):
    while True:
        try:
            http_mirror_entry_line = await reader.readline()
        except:
            LOG.exception(msg='An unexpected error occurred when attempting to read a line.')
            continue

        if not http_mirror_entry_line:
            LOG.error(msg='The handle loop ended because of an empty entry line.')
            break

        try:
            http_mirror_entry: HTTPMirrorEntry = json_loads(http_mirror_entry_line.decode())

            request_raw: bytes = b64decode(http_mirror_entry['request']['raw_base64'])
            response_body_raw: bytes = b64decode(http_mirror_entry['response']['body_base64'])

            response_headers_list: list[tuple[str, str]] = []
            for header_name, header_value in http_mirror_entry['response']['headers'].items():
                if isinstance(header_value, list):
                    for header_list_value in header_value:
                        response_headers_list.append((header_name, header_list_value))
                else:
                    response_headers_list.append((header_name, header_value))

            entry: Base = merge_ecs_entries(
                entry_from_http_message(
                    http_message=HTTPRequest.from_bytes(data=request_raw, store_raw=True),
                    include_decompressed_body=True,
                    use_host_header=True,
                    use_forwarded_header=True,
                    public_suffix_list_trie=public_suffix_list_trie
                ),
                entry_from_http_message(
                    http_message=HTTPResponse(
                        start_line=StatusLine(status_code=http_mirror_entry['response']['status']),
                        headers=response_headers_list,
                        body=memoryview(response_body_raw)
                    )
                ),
                Base(
                    destination=Destination(
                        ip=http_mirror_entry['server_addr'],
                        port=int(http_mirror_entry['server_port'])
                    ),
                    source=Source(
                        address=http_mirror_entry['remote_addr'],
                        ip=http_mirror_entry['remote_addr'],
                        port=int(http_mirror_entry['remote_port'])
                    ),
                    network=Network(
                        transport='tcp',
                        protocol=http_mirror_entry['scheme']
                    )
                )
            )

            request_timestamp: float = http_mirror_entry['request']['time']

            duration: float | None = None
            response_datetime: datetime | None = None

            duration_str: str | None = http_mirror_entry['response'].get('duration')
            if duration_str:
                duration = float(duration_str)
                response_datetime = datetime.fromtimestamp(request_timestamp + duration).astimezone()

            entry.event = Event(
                start=datetime.fromtimestamp(request_timestamp).astimezone(),
                duration=duration,
                end=response_datetime
            )

            LOG.info(
                msg='A mirrored HTTP request-response pair was handled.',
                extra=dict(entry) | dict(_ecs_logger_handler_options=dict(merge_extra=True))
            )
        except:
            LOG.exception(msg='An unexpected error occurred when attempting to parse a line.')
