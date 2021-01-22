#!/bin/bash

echo $'nameserver 1.1.1.1\nnameserver 8.8.8.8' > /etc/resolv.conf

./main.py

