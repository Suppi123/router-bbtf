# Router Black Box Test Framework
A framework to facilitate the development of black box tests for home routers.

## Overview

###network folder

The network folder contains an example script to simulate a simplified test setup using mininet.
Execute with `sudo python3 simple-test.py`

###rpyc_server folder

The rpyc_server folder contains (nearly) everything you need to make a host ready for testing.
You just need to copy the folder to the host and use either the rpyc_classic.py or the host.py to set up working host.
The rpyc_classic.py can only run one test at a time but offers logging. The host.py can run multiple
tests simultaneously but without logging to the console.

To start the rpyc_classic.py use `python3 rpyc_classic.py --host 0.0.0.0`

To start the host.py use `python3 host.py`

###tests folder

Contains all tests developed so far. All tests should end with `_test.py` to be recognized.

##Installation

###Host Setup

To set up a host for testing purposes copy the rpyc_server folder to the test device.
If you want to do a speedtest also install iperf3:

`sudo apt install iperf3`

###Controller Setup

Before the tests can be started, the following steps are necessary on the controller system:

If you want to do a speedtest you also have to install iperf3 and an iperf3 python wrapper on the controller system 

`sudo apt install iperf3`

`pip3 install iperf3`

Necessary steps:

`pip3 install click`

`pip3 install rpyc`

##Perform a test

* Run rpyc_classic.py or host.py on the host devices depending on the use case.

    `python3 rpyc_classic.py --host 0.0.0.0`
    
    or

    ` python3 host.py`

* Adjust the settings in the config.ini
* Start the test(s) on the controller. To start a specific test use
    
    `python3 application.py --test_name <name-of-test>`
  
    to start all available tests use
    
    `python3 application.py`

##Develop a test

Each test consists of three parts. A server component that runs on a host. A client component running on a host
and a controller component. If the test is synchronous, the client and server components can be the same.

###Example:

```python
import configparser
from bbtf import controller

config = configparser.ConfigParser()
config.read('config.ini')

host1 = config['GENERAL']['host1']
host2 = config['GENERAL']['host2']

def client_func(host2_ip, host2_port):
    #  do some client stuff


def server_func(host1_ip, host1_port):
    # do some server stuff


@controller(host1, host2, client_func, server_func)
def start_controller(host1_remote_func, host2_remote_func) -> dict:
    # start server
    host2_remote_func(host1, 12345)
    
    # start client
    result = host1_remote_func(host2, 12345)
    
    return result
```

###Explanation

####Config

If you want you can use the config.ini to use global settings. This is espacially
useful for the IP addresses of the hosts. In the config.ini you can also define settings
that are only valid for your tests.

####Client and server functions

Here you can define the code to be executed on the host devices. It is important to note that
only modules that are installed on the host device can be used for imports. Imports that are 
used within these functions should also be defined within these functions. These functions
will later run independently on the host devices.

####Controller function

This is where the real magic happens. A controller function always needs the @controller
decorator. The decorator distributes the test functions to the hosts and passes a reference to these
functions as parameter to the actual function. To make this possible rpyc is used.
The functions can then be called like local functions, but they are executed on the respective 
client. For special use cases there is the @async_controller decorator. This can be used if the test
functions should be executed non-blocking. Important! The controller function should always
be called start_controller so that it can be started from application.py.


