#!/bin/bash

sudo systemctl daemon-reload
sudo systemctl restart romabot.service
journalctl -u romabot.service -f
