import logging
import configparser
from bbtf import async_controller

config = configparser.ConfigParser()
config.read('config.ini')

host1 = config['GENERAL']['host1']
host2 = config['GENERAL']['host2']
max_timeout = int(config['SOLITARY_OUTBOUND_MULTIPLE_INBOUND']['max_timeout'])


def test_client_func(client_w_ip: str, timeout: int,  udp_port: int, send_initial=False):
    import socket
    import json
    import logging

    # Setup Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', udp_port))

    if send_initial:  # only send initial packet is wanted
        logging.info(f'Send initial message to {client_w_ip}, {udp_port}')
        sock.sendto(bytes("This is the initial message", 'UTF-8'), (client_w_ip, udp_port))
        data, addr = sock.recvfrom(1024)
        logging.info(f'Received answer to inital message {data}')

    # The Test
    try:
        logging.info(f'Wait for response. Wait {timeout}s for a response')

        # Set timeout and wait for response
        sock.settimeout(timeout + 2.0)  # wait a bit longer then expected
        data, addr = sock.recvfrom(1024)
        logging.info(f'Received Message from {addr}: {data}')
        received_message = True
    except socket.timeout:
        # Handle timeout
        logging.info(f"No message from server after {timeout} seems like my job is finished. Bye.")
        received_message = False
    finally:
        sock.close()

    # Return result
    return json.dumps({'received_message': received_message, 'timeout': timeout})


def test_server_func(timeout: int, client_ip: str, client_port: int, send_initial=False, addr=()):
    import socket
    import json
    import logging
    import time

    # Setup Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', client_port))

    if send_initial:
        logging.info("Waiting for client to initialize connection...")
        data, addr = sock.recvfrom(1024)  # receive data from client
        logging.info(f'Received message from client: {data} from {addr}')
        sock.sendto(bytes("Initial answer", 'UTF-8'), (addr[0], addr[1]))
        logging.info(f'Answered to initial message')
    if len(addr) == 0:
        addr = (client_ip, client_port)

    time.sleep(timeout)
    # Transmit expected timeout to client
    logging.info(f"Send message to client: {addr}")
    sock.sendto(bytes(json.dumps({'expected_timeout': timeout}), 'UTF-8'), (addr[0], addr[1]))
    sock.close()
    return addr


@async_controller(host1, host2, test_client_func, test_server_func)
def start_controller(client_l_remote_func, client_w_remote_func) -> dict:
    """
    UDP-2
    The intent of this test is to determine if inbound traffic refreshes a binding, compared to UDP-1. The test client
    sends a solitary UDP packet to the test server and then remains silent. The server sends a stream of responses
    across the binding, and increases the delay between each response packet until the binding times out.
    :param client_l_remote_func:
    :param client_w_remote_func:
    :return:
    """
    # init test
    import json
    import random

    port = random.randint(49152, 65535)

    def test_step(last_working_timeout, limit_timeout, send_initial):
        timeout = 10
        # init test step
        addr = client_w_remote_func(timeout, host1,  port, send_initial=send_initial)
        res = json.loads(client_l_remote_func(host2, timeout, port, send_initial=send_initial).value)
        addr = addr.value
        while True:
            if res['received_message']:
                last_working_timeout = timeout
                if timeout + 15 < limit_timeout:
                    timeout += 15
                else:
                    timeout = (limit_timeout + timeout) / 2
            else:
                if last_working_timeout == limit_timeout:
                    last_working_timeout -= 10
                limit_timeout = timeout
                return test_step(last_working_timeout, limit_timeout, True)

            if abs(limit_timeout - last_working_timeout) < 2 or timeout > max_timeout:
                return last_working_timeout

            addr = client_w_remote_func(timeout, host1, port, addr=(addr[0], addr[1]), send_initial=False)
            res = json.loads(client_l_remote_func(host2, timeout, port, send_initial=False).value)
            addr = addr.value

    res_timeout = test_step(10, max_timeout, True)
    result_obj = {'test_type': 'UDP', 'test_name': 'Solitary outbound multiple inbound', 'result': res_timeout}
    logging.info(result_obj)
    return result_obj

