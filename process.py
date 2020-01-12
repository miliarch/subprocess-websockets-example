#!/usr/bin/env python3
# Subprocess / Websockets Example
import sys
import select
from datetime import datetime, timedelta
from random import random


def calc_next_time(seconds):
    return datetime.now() + timedelta(seconds=seconds)


def generate_delay():
    return random() * 5


def main():
    delay = generate_delay()
    next_time = calc_next_time(delay)
    while True:
        now = datetime.now()
        delta = next_time - now
        if delta.seconds > delay:
            print(now.isoformat())
            delay = generate_delay()
            next_time = calc_next_time(delay)
        # This solution to non-blocking stdin read found here:
        # https://repolinux.wordpress.com/2012/10/09/non-blocking-read-from-stdin-in-python/
        while sys.stdin in select.select([sys.stdin, ], [], [], 0.0)[0]:
            line = sys.stdin.readline()
            if line:
                print(line.rstrip('\n'))
            else:
                print('eof')
                exit(0)


if __name__ == '__main__':
    main()
