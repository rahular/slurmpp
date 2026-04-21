#!/bin/bash
grep -i NOPASSWD /etc/sudoers 2>/dev/null | head -3
ls /etc/sudoers.d/ 2>/dev/null
whoami
id
