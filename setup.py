
from distutils.core import setup

setup(
    name="alamatic",
    version="0.0.1",
    description="Programming language for embedded applications",
    packages=['alamatic','alamatic.ast','alamatic.types'],
    requires=['plex(==2.0.0)', 'datafork(>=0.0.2)'],
    entry_points = {
        'console_scripts': [
            'alac = alamatic.tools:alac',
        ],
    },
)
