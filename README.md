# pyrtma
RTMA client written in python with no external dependencies. Supports the most used features only.

**This project is under active development and experimentation. Do not use in production until a stable release has been issued.**

## Install
From root directory of the repo:
```shell
$ pip install .
```
## Usage
Launch MessageManager:
```shell
$ python manager.py -a "127.0.0.1"
```

Create a module:
```python
from pyrtma.client import Client

mod = Client()
mod.Connect('127.0.0.1:7111')
```

See /examples for pub/sub use case:

In one terminal run: 
```shell
$ python example.py --pub
```

And from another run: 
```shell
$ python example.py --sub
```

Bench testing utility: 
```shell
$ python testing/pyrtma_bench.py -h
usage: pyrtma_bench.py [-h] [-ms MSG_SIZE] [-n NUM_MSGS] [-np NUM_PUBLISHERS]
                     [-ns NUM_SUBSCRIBERS] [-s SERVER]

rtmaClient bench test utility

optional arguments:
  -h, --help           show this help message and exit
  -ms MSG_SIZE         Messge size in bytes.
  -n NUM_MSGS          Number of messages.
  -np NUM_PUBLISHERS   Number of concurrent publishers.
  -ns NUM_SUBSCRIBERS  Number of concurrent subscribers.
  -s SERVER            RTMA message manager ip address (default:
                       127.0.0.1:7111)
```
