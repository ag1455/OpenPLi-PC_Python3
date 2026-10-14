#!/bin/bash

find /var/log -name "*.gz" -exec rm {} \;
find /var/log -name "*.1" -exec rm {} \;
find /var/log -name "*.1.log" -exec rm {} \;
find /var/log -name "*.0" -exec rm {} \;
find /var/log -name "*.old" -exec rm {} \;
apt clean

exit