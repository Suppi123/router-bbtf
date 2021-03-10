import logging
import configparser
from bbtf.controller import async_controller


config = configparser.ConfigParser()
config.read('config.ini')

host1 = config['GENERAL']['host1']
host2 = config['GENERAL']['host2']
max_timeout = int(config['MULTIPLE_OUTBOUND_MULTIPLE_INBOUND']['max_timeout'])
start_timeout = int(config['MULTIPLE_OUTBOUND_MULTIPLE_INBOUND']['start_timeout'])
timeout_steps = int(config['MULTIPLE_OUTBOUND_MULTIPLE_INBOUND']['timeout_steps'])


def test_client_func(client_w_ip: str, timeout: int, udp_port: int, send_initial: bool):
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
        # Send reply
        logging.info(f'Send reply message to {client_w_ip}, {udp_port}')
        sock.sendto(bytes("This is the reply message", 'UTF-8'), (client_w_ip, udp_port))
        received_message = True
    except socket.timeout:
        # Handle timeout
        logging.info(f"No message from server after {timeout} seems like my job is finished. Bye.")
        received_message = False
    finally:
        sock.close()

    # Return result
    return json.dumps({'received_message': received_message, 'timeout': timeout})


def test_server_func(timeout: int, client_ip: str, client_port: int, send_initial: bool, addr=()):
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
    # Wait for reply
    sock.settimeout(2.0)
    try:
        data, addr = sock.recvfrom(1024)
        logging.info(f"Got reply: {data}")
    except Exception as e:
        logging.info(f"No reply message {e}")
    finally:
        sock.close()

    return addr


@async_controller(host1, host2, test_client_func, test_server_func)
def start_controller(client_l_remote_func, client_w_remote_func) -> dict:
    """
    UDP-3
    The intent is to determine whether outbound traffic refreshes a binding. This test is similar to UDP-2, except that
    the client sends another packet to the server whenever it receives a response packet from it.
    :param client_l_remote_func:
    :param client_w_remote_func:
    :return:
    """
    import json
    import time
    import random

    port = random.randint(49152, 65535)

    def test_step(last_working_timeout, limit_timeout, send_initial):
        timeout = start_timeout
        # init test step
        addr_res = client_w_remote_func(timeout, host1, port, send_initial)
        time.sleep(10)
        res = json.loads(client_l_remote_func(host2, timeout, port, send_initial).value)
        addr = addr_res.value
        while True:
            logging.info(f"Got result {res}")
            if res['received_message']:
                last_working_timeout = timeout
                if timeout + timeout_steps < limit_timeout:
                    timeout += timeout_steps
                else:
                    timeout = (limit_timeout + timeout) / 2
            else:
                if last_working_timeout == limit_timeout:
                    last_working_timeout -= 10
                limit_timeout = timeout
                return test_step(last_working_timeout, limit_timeout, True)

            if abs(limit_timeout - last_working_timeout) < 2 or timeout > max_timeout:
                return last_working_timeout

            addr_res = client_w_remote_func(timeout, host1, port, addr=(addr[0], addr[1]), send_initial=False)
            res = json.loads(client_l_remote_func(host2, timeout, port, send_initial=False).value)
            addr = addr_res.value

    res_timeout = test_step(0, max_timeout, True)
    result_obj = {'test_type': 'UDP', 'test_name': 'Multiple outbound multiple inbound', 'result': res_timeout}
    logging.info(result_obj)
    return result_obj

