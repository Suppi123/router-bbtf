import logging
import configparser
from bbtf import async_controller


config = configparser.ConfigParser()
config.read('config.ini')

host1 = config['GENERAL']['host1']
host2 = config['GENERAL']['host2']
output_file = config['GENERAL']['output_file']
max_timeout = int(config['SOLITARY_OUTBOUND']['max_timeout'])


def test_client_func(client_w_ip: str, timeout: float, udp_port: int) -> str:
    """
    Create a socket, send a UDP packet to the server and wait for a response. If no response arrived till given timeout
    return False, else return True.
    :param client_w_ip:
    :param timeout:
    :param udp_port:
    :return:
    """

    import time
    import socket
    import json

    time.sleep(2)  # wait a bit

    # Setup Socket and send the solitary outbound
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes("This is solitary outbound", 'UTF-8'), (client_w_ip, udp_port))

    # Wait for reply
    try:
        # Set timeout and wait for response
        sock.settimeout(timeout + 1.0)
        data, addr = sock.recvfrom(1024)
        sock.close()
        received_message = True

    except socket.timeout:
        #  Handle timeout
        sock.close()
        received_message = False

    return json.dumps({'received_message': received_message, 'timeout': timeout})


def test_server_func(timeout: float, udp_port: int):
    """
    Create a socket. Wait for initial packet. Reply to initial packet after given timeout.
    :param timeout:
    :param port:
    :return:
    """
    import socket
    import json
    import time

    # Setup Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', udp_port))
    data, addr = sock.recvfrom(1024)  # receive data from client
    # Sleep
    time.sleep(timeout)
    # Transmit expected timeout to client
    sock.sendto(bytes(json.dumps({'timeout': timeout}), 'UTF-8'), (addr[0], addr[1]))
    sock.close()
    return


@async_controller(host1, host2, test_client_func, test_server_func)
def start_controller(host_l_remote_func, host_w_remote_func) -> dict:
    """
    UDP-1
    This test measures how long a NAT maintains a UDP binding after the test client sends a single UDP packet to the
    server. The server does not send traffic to the client, apart from the packet triggered by the sleep timer, and the
    client does not send any further traffic.
    :param host_l_remote_func:
    :param host_w_remote_func:
    :return:
    """
    import json

    #  Test
    res = dict()
    start_port = int(config['SOLITARY_OUTBOUND']['start_port'])
    tmp_min_timeout = 0
    tmp_max_timeout = max_timeout
    timeout = max_timeout / 2
    timed_out_once = False
    while abs(tmp_max_timeout - tmp_min_timeout) > 1 and timeout <= max_timeout:
        host_w_remote_func(timeout, start_port)
        result = host_l_remote_func(host2, timeout, start_port)
        start_port += 1  # use a new port for every test
        #  Result handling
        res = json.loads(result.value)
        logging.info(res)
        if res['received_message']:
            logging.info(f"Solitary Outbound: Message for timeout {res['timeout']} received")
            tmp_min_timeout = timeout
            if timed_out_once:
                timeout = (timeout + tmp_max_timeout) / 2
            else:
                timeout += 20
        else:
            timed_out_once = True
            logging.info(f"Timeout by {res['timeout']} seconds")
            tmp_max_timeout = timeout
            timeout = (timeout + tmp_min_timeout) / 2

    nat_timeout = res['timeout']
    result_obj = {'test_type': 'UDP', 'test_name': 'Solitary outbound package', 'result': nat_timeout}
    logging.info(f'Got result {result_obj}')
    return result_obj
