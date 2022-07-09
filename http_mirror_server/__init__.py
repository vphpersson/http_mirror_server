from logging import Logger, getLogger
from asyncio import StreamReader, StreamWriter
from socket import SocketKind, AddressFamily

from public_suffix.structures.public_suffix_list_trie import PublicSuffixListTrie
from ecs_py import Base, Source, Network
from ecs_tools_py import entry_from_http_request


LOG: Logger = getLogger(__name__)


async def handle(reader: StreamReader, writer: StreamWriter, public_suffix_list_trie: PublicSuffixListTrie | None):

    LOG.debug(msg='Handling a request...')

    try:
        while True:
            source_ip: str | None = None
            source_port: int | None = None

            peer_name = writer.get_extra_info(name='peername')

            if not peer_name:
                LOG.warning(msg='Unable to obtain the peer name of a connection.')
            else:
                source_ip, source_port = peer_name

            network_type: str | None = None
            network_transport: str | None = None
            network_iana_number: int | None = None

            if not (socket := writer.get_extra_info('socket')):
                LOG.warning(msg='Unable to obtain the socket of a connection.')
            else:
                network_iana_number = socket.proto

                match socket.family:
                    case AddressFamily.AF_INET:
                        network_type = 'ipv4'
                    case AddressFamily.AF_INET6:
                        network_type = 'ipv6'
                    case _:
                        LOG.warning(msg=f'Unexpected socket family: {socket.family}')

                match socket.type:
                    case SocketKind.SOCK_STREAM:
                        network_transport = 'tcp'
                    case SocketKind.SOCK_DGRAM:
                        network_transport = 'udp'
                    case _:
                        LOG.warning(msg=f'Unexpected socket type: {socket.type}')

            LOG.debug(msg='Reading the request line...')
            http_request_line = await reader.readline()

            LOG.debug(msg='Reading headers...')
            raw_headers = bytearray()
            while header_line_bytes := await reader.readline():
                raw_headers += header_line_bytes
                if not header_line_bytes.rstrip():
                    break

            LOG.debug(msg='Reading body...')
            body = await reader.read()
            writer.close()

            LOG.debug(msg='Building the ECS entry...')

            entry: Base = entry_from_http_request(
                raw_request_line=http_request_line,
                raw_headers=bytes(raw_headers),
                raw_body=body,
                use_host_header=True,
                use_forwarded_header=True,
                include_decompressed_body=True,
                public_suffix_list_trie=public_suffix_list_trie
            )

            if peer_name:
                source_entry: Source = entry.get_field_value(field_name='source', create_namespaces=True)
                source_entry.ip = source_entry.address = source_ip
                source_entry.port = source_port

            network_entry: Network = entry.get_field_value(field_name='network', create_namespaces=True)
            network_entry.direction = 'ingress'
            network_entry.type = network_type
            network_entry.transport = network_transport
            network_entry.iana_number = network_iana_number
            network_entry.protocol = 'http'

            LOG.info(
                msg='A mirrored HTTP request was handled.',
                extra=entry.to_dict() | dict(_ecs_logger_handler_options=dict(merge_extra=True))
            )

            break
    except:
        LOG.exception(msg='An unexpected error occurred when handing a mirrored HTTP request.')
