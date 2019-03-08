import sys

from .warmup_core import main


def run():
    results = main()
    sys.exit(0)


if __name__ == '__main__':
    run()
