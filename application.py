import os
import argparse
import importlib
import threading
import configparser
from bbtf.util import write_result

config = configparser.ConfigParser()
config.read('config.ini')
output_file = config['GENERAL']['output_file']

parser = argparse.ArgumentParser()
parser.add_argument('--test', type=str, default='', help='Name of the test to be executed')
parser.add_argument('--fulltest', action='store_true', help='Run all tests as specified in test_groups.ini')
parser.add_argument('--listall', action='store_true', help='List all available tests')


def threaded_test(test_mod):
    print(f"Start test {test_mod.__name__}")
    result = test_mod.start_controller()
    print(f"Finished test {test_mod.__name__}")
    write_result(output_file=output_file, result=result)


def application(_test_name: str, _fulltest: bool, _listall: bool):
    test_tree = os.listdir('tests')
    test_modules = list()
    for test in test_tree:
        if test.endswith('_test.py'):
            test = test[0: len(test)-3]
            test_modules.append(importlib.import_module('.' + test, package='tests'))

    if _listall:  # list all tests
        print('These are all available tests:')
        for test_mod in test_modules:
            print(' - ' + test_mod.__name__)

    elif _fulltest:  # run tests as specified in test_groups.ini
        test_groups = configparser.ConfigParser()
        test_groups.read('test_groups.ini')
        for group in test_groups.sections():
            thread_list = list()
            for (key, val) in test_groups.items(group):
                match_test_mod = [test_mod for test_mod in test_modules if test_mod.__name__.endswith(val)]
                if len(match_test_mod) == 1:  # check for unique result
                    test_thread = threading.Thread(target=threaded_test, args=(match_test_mod[0],))
                    thread_list.append(test_thread)  # add thread to the list so we can wait for it later
                    test_thread.start()
                else:
                    print(f'Can not find {val} in tests folder')
            for thread in thread_list:  # wait for threads to finish
                thread.join()

    else:  # execute all or specified test
        for test_mod in test_modules:
            if _test_name == '':  # run every test
                print(f'Execute {test_mod.__name__}')
                result = test_mod.start_controller()
                write_result(output_file=output_file, result=result)
            elif test_mod.__name__ == 'tests.' + _test_name:  # run only the specified test
                print(f'Execute {test_mod.__name__}')
                result = test_mod.start_controller()
                write_result(output_file=output_file, result=result)


if __name__ == '__main__':
    args = parser.parse_args()
    test_name = args.test
    fulltest = args.fulltest
    listall = args.listall
    application(test_name, fulltest, listall)


