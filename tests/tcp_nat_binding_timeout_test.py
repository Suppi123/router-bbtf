import configparser
from bbtf import controller

config = configparser.ConfigParser()
config.read('config.ini')

host1 = config['GENERAL']['host1']
host2 = config['GENERAL']['host2']

max_timeout = int(config['TCP_NAT_BINDING_TIMEOUT']['max_timeout'])


def test_client_func(host_w_ip: str, tcp_port: int, timeout: float):
    import time
    import socket
    import logging
    import json

    time.sleep(2)  # wait a bit

    #  Setup Socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 0)

        sock.connect((host_w_ip, tcp_port))
        sock.sendall(bytes("Initial Message", 'UTF-8'))

        #  The Test
        try:
            logging.info(f'Wait for response. Wait {timeout + 1.0}s for a response')

            #  Set timeout and wait for response
            sock.settimeout(timeout + 1.0)
            data = sock.recv(1024)
            logging.info(f"Received Message after {timeout} seconds.")
            received_message = True
        except socket.timeout:
            #  Handle timeout
            logging.info(f"No message from server after {timeout} seems like my job is finished. Bye.")
            received_message = False
        finally:
            sock.close()

    result_obj = {'received_message': received_message, 'timeout': timeout}
    logging.info(result_obj)
    return json.dumps(result_obj)


def test_server_func(tcp_port: int, timeout: float):
    import socket
    import logging
    import time
    import threading

    def test():
        #  Setup Socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 0)
            sock.bind(('0.0.0.0', tcp_port))
            logging.info(f"Opened Port {tcp_port}")

            sock.listen()
            conn, addr = sock.accept()
            with conn:
                logging.info(f"Connection with {addr}")
                logging.info(f"Waiting for {timeout} seconds before sending a reply")
                time.sleep(timeout)
                conn.sendall(bytes(f"Reply after {timeout} seconds", "UTF-8"))
                logging.info(f"Send message after {timeout} seconds")
                conn.close()

            sock.close()

        logging.info("Bye")

    thread = threading.Thread(target=test, args=(), daemon=True)
    thread.start()

    return ""


@controller(host1, host2, test_client_func, test_server_func)
def start_controller(host_l_remote_func, host_w_remote_func) -> dict:
    """
    Like UDP-1 (Solitary Outbound Test) except the client opens a TCP connection with the server. The connection
    is left on idle with no TCP keepalives in use.
    :param host_l_remote_func:
    :param host_w_remote_func:
    :return:
    """
    import json
    import logging

    #  Test
    res = dict()
    start_port = 2200  # use this port as first test port
    last_working_timeout = 0  # this is the last timeout where we got a result. Set to 0 at the beginning
    lowest_not_working_timeout = max_timeout  # this ist the lowest timeout where we got no result
    timeout = 3600  # the timeout we are about to test
    timed_out_once = False  # indicates if we already had a timed out binding

    while abs(lowest_not_working_timeout - timeout) > 1 and timeout <= max_timeout:
        host_w_remote_func(start_port, timeout)
        result = host_l_remote_func(host2, start_port, timeout)
        start_port += 1  # use a new port for every test
        #  Result handling
        res = json.loads(result)
        logging.info(res)
        if res['received_message']:
            logging.info(f"Message for timeout {res['timeout']} received")
            last_working_timeout = timeout  # we received a message. So this is ne new last working timeout
            if timed_out_once:
                timeout = (timeout + lowest_not_working_timeout) / 2  # binary search
            else:
                timeout += 3600  # increase the timeout to find the next not working timeout
        else:
            timed_out_once = True
            logging.info(f"Timeout by {res['timeout']} seconds")
            lowest_not_working_timeout = timeout  # we received no message so this is the new lowest not working timeout
            timeout = (timeout + last_working_timeout) / 2  # binary search

    nat_timeout = res['timeout']
    result_obj = {'test_type': 'TCP', 'test_name': 'TCP NAT Binding Timeout', 'result': nat_timeout}
    logging.info(f'Got result {result_obj}')
    return result_obj
