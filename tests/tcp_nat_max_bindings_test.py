import configparser
from bbtf import async_controller


config = configparser.ConfigParser()
config.read('config.ini')

host1 = config['GENERAL']['host1']
host2 = config['GENERAL']['host2']


def test_client_func(client_w_ip, client_tcp_port, server_tcp_port):
    import logging
    import socket
    import threading
    import json

    def client_thread(sck):
        while True:
            try:
                sck.recv(1024)
            except Exception as e:
                logging.info(f'{e}')

    def create_connection(remote_ip, client_port, remote_port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(180)
            sock.bind(('', client_tcp_port))
            sock.connect((client_w_ip, server_tcp_port))
            t = threading.Thread(target=client_thread, args=(sock,), daemon=True)
            t.start()
            logging.info(f"Connected to {client_w_ip} from port {client_tcp_port}")
            return json.dumps({'new_connection': True, 'reason': ''})
        except Exception as e:
            if str(e) == '[Errno 98] Address already in use':
                return create_connection(client_w_ip, client_tcp_port+1, server_tcp_port)
            else:
                logging.info(f"Could not establish connection: {e}")
                return json.dumps({'new_connection': False, 'reason': str(e)})

    return create_connection(client_w_ip, client_tcp_port, server_tcp_port)


def test_server_func(tcp_port):
    import socket
    import logging
    import threading
    import time

    list_of_connections = list()
    exit_flag = False

    def client_thread():
        while True:
            if exit_flag:
                for conn in list_of_connections:
                    conn.close()
                break

            for conn in list_of_connections:
                conn.send(bytes(f'Still there?', 'UTF-8'))

            logging.info(f'At the moment there are {len(list_of_connections)} connections')
            time.sleep(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.settimeout(180)
    sock.bind(('0.0.0.0', tcp_port))
    logging.info(f"Opened Port {tcp_port}")

    sock.listen(5)
    t = threading.Thread(target=client_thread, args=(), daemon=True)
    t.start()
    while True:
        try:
            conn, addr = sock.accept()
            list_of_connections.append(conn)
        except Exception as e:
            logging.error(f'Could not accept new connection: {e}')
            sock.close()
            exit_flag = True


@async_controller(host1, host2, test_client_func, test_server_func)
def start_controller(client, server):
    import logging
    import time
    import json

    server_port = 6000
    client_start_port = 6000
    server(server_port)
    connection_counter = 0
    while True:
        time.sleep(0.05)  # short break
        client_res = json.loads(client(host2, client_start_port, server_port).value)
        client_start_port += 1
        if client_res['new_connection']:
            connection_counter += 1
            continue
        else:
            logging.info(f'Reached Maximum of {connection_counter} connections. Reason: {client_res["reason"]}')
            result_obj = {'test_name': 'TCP Max NAT bindings', 'result': connection_counter,
                          'reason': client_res["reason"]}
            logging.info(result_obj)
            return result_obj


