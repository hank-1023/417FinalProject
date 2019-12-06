import argparse
import asyncio
import signal
import logging


def main():
    loop = asyncio.get_event_loop()