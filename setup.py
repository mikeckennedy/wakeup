import re

from setuptools import setup

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('wakeup/__init__.py').read(),
    re.M
).group(1)

requires = [
    'aiohttp',
    'unsync',
    'colorama',
]

setup(
    name='wakeup',
    version=version,
    packages=['wakeup'],
    install_requires=requires,
    entry_points={
        "console_scripts": ['wakeup = wakeup:main']
    },
    url='https://github.com/mikeckennedy/wakeup',
    license='MIT',
    author='Michael Kennedy',
    author_email='michael@talkpython.fm',
    description='An app to exercise a website to warm up every page.'
)
