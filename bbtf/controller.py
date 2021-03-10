import rpyc
import logging
from functools import wraps
'''
Logging
'''
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def controller(host1: str, host2: str, host1_test, host2_test, host1_port=18812, host2_port=18812):
    """
    Distribute the test functions on the clients and returns a synchronous remote access to the functions.
    :param host1: address of host1
    :param host2: address of host2
    :param host1_test: test function to be executed on host 1
    :param host2_test: test function to be executed on host 2
    :param host1_port: rpyc port of host 1
    :param host2_port: rpyc port of host 2
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Connect to first host
            try:
                connection1 = rpyc.connect(host1, host1_port, keepalive=True, service=rpyc.core.service.MasterService)
                connection1._config['sync_request_timeout'] = None  # No timeout
                logging.info(f'Connected to {host1} on port {host1_port}')
            except Exception as e:
                logging.error(f'Could not connect to host1: {e}')
                raise e

            # Connect to second host"""
            try:
                connection2 = rpyc.connect(host2, host2_port, keepalive=True, service=rpyc.core.service.MasterService)
                connection2._config['sync_request_timeout'] = None  # No timeout
                logging.info(f'Connected to {host2} on port {host2_port}')
            except Exception as e:
                logging.error(f'Could not connect to host2: {e}')
                raise e

            # Teleport test function to first host
            host1_test_remote = connection1.teleport(host1_test)
            logging.info(f'Teleported {host1_test.__name__} to {host1}')

            # Teleport test function to second host
            host2_test_remote = connection2.teleport(host2_test)
            logging.info(f'Teleported {host2_test.__name__} to {host2}')

            # Now we have a nice test setup
            logging.info(f'Successfully setup the test on both hosts')
            return func(host1_test_remote, host2_test_remote, *args, **kwargs)
        return wrapper
    return decorator


def async_controller(host1: str, host2: str, host1_test, host2_test, host1_port=18812, host2_port=18812):
    """
    Distribute the test functions on the clients and returns a asynchronous remote access to the functions.
    :param host1: address of host1
    :param host2: address of host2
    :param host1_test: test function to be executed on host 1
    :param host2_test: test function to be executed on host 2
    :param host1_port: rpyc port of host 1
    :param host2_port: rpyc port of host 2
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Connect to first host
            try:
                connection1 = rpyc.connect(host1, host1_port, keepalive=True, service=rpyc.core.service.MasterService)
                connection1._config['sync_request_timeout'] = None  # No timeout
                logging.info(f'Connected to {host1} on port {host1_port}')
            except Exception as e:
                logging.error(f'Could not connect to host1: {e}')
                raise e

            try:
                # Connect to second host
                connection2 = rpyc.connect(host2, host2_port, keepalive=True, service=rpyc.core.service.MasterService)
                connection2._config['sync_request_timeout'] = None  # No timeout
                logging.info(f'Connected to {host2} on port {host2_port}')
            except Exception as e:
                logging.error(f'Could not connect to host2: {e}')
                raise e

            # Teleport test function to first host
            host1_test_remote = rpyc.async_(connection1.teleport(host1_test))
            logging.info(f'Teleported {host1_test.__name__} to {host1}')

            # Teleport test function to second host
            host2_test_remote = rpyc.async_(connection2.teleport(host2_test))
            logging.info(f'Teleported {host2_test.__name__} to {host2}')

            # Now we have a nice test setup
            logging.info(f'Successfully setup the test on both hosts')
            return func(host1_test_remote, host2_test_remote, *args, **kwargs)
        return wrapper
    return decorator





