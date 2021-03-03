import argparse
import logging
from rpyc.utils.server import ThreadedServer
from rpyc.core.service import SlaveService

'''
Script Arguments
'''
parser = argparse.ArgumentParser(description='Test NAT behaviour under multiple outbound and inbound traffic')
parser.add_argument('--host', default='0.0.0.0', help='Server Address. Default: 0.0.0.0')
parser.add_argument('--port', default=18812, help='Server Port. Default: 18812')
args = parser.parse_args()

host = args.host
port = args.port

'''
Start a threaded RPyC-Server with a SlaveService
'''
logging.info(f'Start RPyC-Server on {host}. Opened port {port}')
t = ThreadedServer(SlaveService, hostname=host, port=port)
t.start()


