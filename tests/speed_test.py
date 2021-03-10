import logging
import configparser
from bbtf import async_controller

config = configparser.ConfigParser()
config.read('config.ini')

host1 = config['GENERAL']['host1']
host2 = config['GENERAL']['host2']
start_port = int(config['SPEED']['start_port'])
test_duration = int(config['SPEED']['test_duration'])


def speed_test_client_func(host, port=5501, duration=10, reverse=False, protocol='tcp'):
    import iperf3
    client = iperf3.Client()
    client.protocol = protocol
    client.duration = duration
    client.server_hostname = host
    client.port = port
    client.reverse = reverse
    result = client.run()
    return result


def speed_test_server_func(port=5501, protocol='tcp'):
    import iperf3
    import threading
    server = iperf3.Server()
    server.protocol = protocol
    server.port = port
    server_thread = threading.Thread(target=server.run, args=(), daemon=True)
    server_thread.start()
    return


@async_controller(host1, host2, speed_test_client_func, speed_test_server_func)
def start_controller(client, server):
    import time

    result = list()

    _start_port = start_port

    # Test only upload and only download for TCP and UDP
    tests = [{'reverse': True, 'protocol': 'tcp'}, {'reverse': False, 'protocol': 'tcp'},
             {'reverse': True, 'protocol': 'udp'}, {'reverse': False, 'protocol': 'udp'}]
    for test in tests:
        try:
            # Create Server
            server(port=_start_port, protocol=test['protocol'])
            time.sleep(5)  # server startup time
            # Start Client
            async_iperf_result = client(host2, port=_start_port, duration=test_duration, reverse=test['reverse'],
                                        protocol=test['protocol'])
            iperf_result = async_iperf_result.value

            _start_port += 1
            logging.info(f'Result: {str(iperf_result)}')
            # Generate Report
            if test['protocol'] == 'tcp':
                result.append({'test_name': 'speed_test', 'protocol': iperf_result.protocol, 'reverse': test['reverse'],
                               'Mbps': iperf_result.received_Mbps})
            else:
                result.append({'test_name': 'speed_test', 'protocol': iperf_result.protocol, 'reverse': test['reverse'],
                               'Mbps': iperf_result.Mbps})
        except Exception as e:
            logging.error(f"Error while executing speed test {e}")

    # Test simultaneous up- and download
    _start_port1 = _start_port
    _start_port2 = _start_port + 1
    for protocol in ['tcp', 'udp']:
        try:
            # Create Server1
            server(protocol=protocol, port=_start_port1)
            # Create Server2 on different port for reverse test
            server(protocol=protocol, port=_start_port2)
            # Server startup time
            time.sleep(10)
            # Start Client for Server1"""
            async_result_up = client(host2, port=_start_port1, reverse=False, protocol=protocol)
            # Start Reverse-Client for Server2
            async_result_down = client(host2, port=_start_port2, reverse=True, protocol=protocol)
            # Wait for Results
            result_up = async_result_up.value
            result_down = async_result_down.value
            # Increment start ports for the next run
            _start_port1 += 2
            _start_port2 += 2
            # Generate Report
            if protocol == 'tcp':
                result.append({'test_name': 'speed_test_bidirectional', 'protocol': protocol,
                               'Mbps_Up': result_up.received_Mbps, 'Mbps_Down': result_down.received_Mbps})
            else:
                result.append({'test_name': 'speed_test_bidirectional', 'protocol': protocol,
                               'Mbps_Up': result_up.Mbps, 'Mbps_Down': result_down.Mbps})
        except Exception as e:
            logging.error(f"Error while executing speed test {e}")

    logging.info(f'Got result {result}')
    return result
