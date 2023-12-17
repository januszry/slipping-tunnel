#!/usr/bin/env python3
import argparse
import json
import logging
import sys
import subprocess

from typing import List


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Instance:
    def __init__(self, ips: List[str], ports: List[int]) -> None:
        self.ips = ips
        self.ports = ports

    def __repr__(self):
        return f'{self.ips}:{self.ports}'

    def __str__(self):
        return self.__repr__()


def cli(jump_host: str, config_file: str):
    instances = []
    with open(config_file) as f:
        for item in json.load(f):
            ips = []
            if 'ip' in item:
                ips.append(item['ip'])
            if 'ips' in item:
                ips = ips + item['ips']
            instances.append(Instance(ips, item['ports']))
    connect(jump_host, instances)


def connect(jump_host: str, instances: List[Instance]):
    print_instances(instances)
    add_local_interfaces(instances)
    connect_ssh_tunnel(jump_host, instances)
    remove_local_interfaces(instances)


def print_instances(instances: List[Instance]):
    logger.info('Instance List:')
    for i in instances:
        logger.info("\t%s", i)


def add_local_interfaces(instances: List[Instance]):
    logger.info(' * adding interface, user password might be needed')
    for i in instances:
        for ip in i.ips:
            if sys.platform == 'darwin':
                cmd = ['sudo', 'ifconfig', 'lo0', 'alias', ip]
            else:
                cmd = ['sudo', 'ip', 'add', 'a', 'dev', 'lo', ip]
            logger.info("\tCommand %s", cmd)
            subprocess.call(cmd)


def remove_local_interfaces(instances: List[Instance]):
    logger.info(' * removing interface, user/root password might be needed')
    for i in instances:
        for ip in i.ips:
            if sys.platform == 'darwin':
                cmd = ['sudo', 'ifconfig', 'lo0', '-alias', ip]
            else:
                cmd = ['sudo', 'ip', 'del', 'a', 'dev', 'lo', ip]
            logger.info("\tCommand %s", cmd)
            subprocess.call(cmd)


def connect_ssh_tunnel(jump_host: str, instances: List[Instance]):
    logger.info(' * connecting to jump host %s', jump_host)
    opts = []
    for i in instances:
        for ip in i.ips:
            for port in i.ports:
                opts += ['-L', f'{ip}:{port}:{ip}:{port}']
    command = ['ssh'] + opts + [jump_host]
    logger.info("\tCommand %s", command)
    subprocess.call(command)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("jump_host", type=str)
    parser.add_argument("config_file", type=str)
    args = parser.parse_args()
    cli(args.jump_host, args.config_file)
