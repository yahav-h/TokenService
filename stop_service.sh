#!/bin/sh
ps aux | grep token_service_main.py | awk '{print $2}' | xargs kill