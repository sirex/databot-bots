from setuptools import setup, find_packages

setup(
    name="databot-bots",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'databot',
        'gramtool',
        'GeoAlchemy2',
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'botlib-tool = botlib.tool:main',
            'botlib-index = botlib.indexfinder:main',
        ],
    },
)
