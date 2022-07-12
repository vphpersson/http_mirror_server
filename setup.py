from setuptools import setup, find_packages

setup(
    name='http_mirror_server',
    version='0.23',
    packages=find_packages(),
    install_requires=[
        'typed_argument_parser @ git+https://github.com/vphpersson/typed_argument_parser.git#egg=typed_argument_parser',
        'public_suffix @ git+https://github.com/vphpersson/public_suffix.git#egg=public_suffix',
        'ecs_py @ git+https://github.com/vphpersson/ecs_py.git#egg=ecs_py',
        'ecs_tools_py @ git+https://github.com/vphpersson/ecs_tools_py.git#egg=ecs_tools_py'
    ]
)
