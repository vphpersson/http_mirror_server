from typing import Type, Final
from pathlib import Path
from os import environ as os_environ

from public_suffix.structures.public_suffix_list_trie import PublicSuffixListTrie

from http_mirror_server.cli import HTTPMirrorServerArgumentParser

ENVIRONMENT_PREFIX: Final[str] = 'HTTP_MIRROR_SERVER'


def parse_environment(namespace: Type[HTTPMirrorServerArgumentParser.Namespace]) -> None:

    namespace.socket_path = (
        Path(socket_path)
        if (socket_path := os_environ.get(f'{ENVIRONMENT_PREFIX}_SOCKET_PATH'))
        else namespace.socket_path
    )

    log_directory_str_path: str | None = os_environ.get(f'{ENVIRONMENT_PREFIX}_LOG_DIRECTORY')
    if log_directory_str_path is not None:
        if (log_directory_path := Path(log_directory_str_path)).exists():
            namespace.log_directory = log_directory_path
        else:
            raise ValueError('The specified log directory does not exist.')

    public_suffix_list_str_path: str | None = os_environ.get(f'{ENVIRONMENT_PREFIX}_PUBLIC_SUFFIX_LIST_PATH')
    if public_suffix_list_str_path is not None:
        namespace.public_suffix_list_trie = (
            PublicSuffixListTrie.from_public_suffix_list_file(file=Path(public_suffix_list_str_path))
        )
