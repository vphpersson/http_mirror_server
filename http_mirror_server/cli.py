from argparse import FileType, Action, ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter
from typing import Type
from pathlib import Path
from io import TextIOWrapper

from typed_argument_parser import TypedArgumentParser
from public_suffix.structures.public_suffix_list_trie import PublicSuffixListTrie


class HTTPMirrorServerArgumentParser(TypedArgumentParser):

    class Namespace:
        log_directory: Path
        host: str
        port: int
        public_suffix_list_path: str | None
        public_suffix_list_trie: PublicSuffixListTrie | None

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **(
                dict(
                    description='Run an HTTP server that handles mirrored HTTP requests and logs them.',
                    formatter_class=ArgumentDefaultsHelpFormatter
                ) | kwargs
            )
        )

        self.add_argument(
            '--host',
            help='The host address on which to listen.',
            default='localhost'
        )

        self.add_argument(
            '--port',
            help='The port on which to listen.',
            default=8080
        )

        self.add_argument(
            '--log-directory',
            help='The path of the directory where to write log files.'
        )

        self.add_argument(
            '--public-suffix-list-path',
            help='The file path of public suffix list file with which to parse HTTP paths.',
            type=FileType(mode='r'),
            action=self._ParsePublicSuffixListPathAction,
            default=None
        )

    def parse_args(self, *args, **kwargs) -> Type[Namespace]:
        namespace: Type[Namespace] = super().parse_args(*args, **kwargs)
        setattr(namespace, 'public_suffix_list_trie', getattr(namespace, 'public_suffix_list_trie', None))
        return namespace

    class _ParsePublicSuffixListPathAction(Action):
        def __call__(
            self,
            parser: ArgumentParser,
            namespace: Namespace,
            public_suffix_list_path: TextIOWrapper | None,
            option_string: str | None = None
        ):
            public_suffix_list_trie: PublicSuffixListTrie | None = (
                PublicSuffixListTrie.from_public_suffix_list_file(public_suffix_list_path) if public_suffix_list_path
                else None
            )

            setattr(namespace, 'public_suffix_list_trie', public_suffix_list_trie)

    class _CheckLogDirectoryAction(Action):
        def __call__(
            self,
            parser: ArgumentParser,
            namespace: Namespace,
            log_directory: str,
            option_string: str | None = None
        ):

            if (log_directory_path := Path(log_directory)).exists():
                setattr(namespace, 'log_directory_path', log_directory_path)
            else:
                parser.error(message='The specified log directory does not exist.')


