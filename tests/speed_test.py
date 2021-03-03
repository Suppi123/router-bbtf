import logging
import configparser
from bbtf import async_controller

config = configparser.ConfigParser()
config.read('config.ini')

host1 = config['GENERAL']['host1']
host2 = config['GENERAL']['host2']


def speed_test_client_func(host, port=5501, reverse=False, protocol='tcp'):
    import iperf3
    client = iperf3.Client()
    client.protocol = protocol
    client.duration = 5
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
    result = list()

    # Test only upload and only download for TCP and UDP
    tests = [{'reverse': True, 'protocol': 'tcp'}, {'reverse': False, 'protocol': 'tcp'},
             {'reverse': True, 'protocol': 'udp'}, {'reverse': False, 'protocol': 'udp'}]
    for test in tests:
        # Create Server
        server(protocol=test['protocol'])
        # Start Client
        iperf_result = client(host2, reverse=test['reverse'], protocol=test['protocol']).value
        logging.info(f'Result: {str(iperf_result)}')
        # Generate Report
        if test['protocol'] == 'tcp':
            result.append({'test_name': 'speed_test', 'protocol': iperf_result.protocol, 'reverse': test['reverse'],
                           'Mbps': iperf_result.received_Mbps})
        else:
            result.append({'test_name': 'speed_test', 'protocol': iperf_result.protocol, 'reverse': test['reverse'],
                           'Mbps': iperf_result.Mbps})

    # Test simultaneous up- and download
    for protocol in ['tcp', 'udp']:
        # Create Server1
        server(protocol=protocol)
        # Create Server2 on different port for reverse test
        server(protocol=protocol, port=5502)
        # Start Client for Server1"""
        async_result_up = client(host2, reverse=False, protocol=protocol)
        # Start Reverse-Client for Server2
        async_result_down = client(host2, reverse=True, protocol=protocol, port=5502)
        # Wait for Results
        result_up = async_result_up.value
        result_down = async_result_down.value
        # Generate Report
        if protocol == 'tcp':
            result.append({'test_name': 'speed_test_bidirectional', 'protocol': protocol,
                           'Mbps_Up': result_up.received_Mbps, 'Mbps_Down': result_down.received_Mbps})
        else:
            result.append({'test_name': 'speed_test_bidirectional', 'protocol': protocol,
                           'Mbps_Up': result_up.Mbps, 'Mbps_Down': result_down.Mbps})

    logging.info(f'Got result {result}')
    return result
