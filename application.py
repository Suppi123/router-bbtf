import os
import click
import importlib
import configparser
from bbtf.util import write_result

config = configparser.ConfigParser()
config.read('config.ini')
output_file = config['GENERAL']['output_file']


@click.command()
@click.option('--test_name', default='', help='Name of the test to be executed')
@click.option('--listall', is_flag=True, default=False, help='List all available tests')
def application(test_name: str, listall: bool):
    test_tree = os.listdir('tests')
    test_modules = list()
    for test in test_tree:
        if test.endswith('_test.py'):
            test = test[0: len(test)-3]
            test_modules.append(importlib.import_module('.' + test, package='tests'))

    if listall:  # list all tests
        click.echo('These are all available tests:')
        for test_mod in test_modules:
            click.echo(' - ' + test_mod.__name__)
    else:  # execute all or specified test
        for test_mod in test_modules:
            if test_name == '':  # run every test
                click.echo(f'Execute {test_mod.__name__}')
                result = test_mod.start_controller()
                write_result(output_file=output_file, result=result)
            elif test_mod.__name__ == 'tests.' + test_name:  # run only the specified test
                click.echo(f'Execute {test_mod.__name__}')
                result = test_mod.start_controller()
                write_result(output_file=output_file, result=result)


if __name__ == '__main__':
    application()

