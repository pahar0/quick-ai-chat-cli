#!/bin/bash
git clone git@github.com:pahar0/cli-gpt-chat.git
cd cli-gpt-chat
pip install -r requirements.txt
chmod +x gpt.py
sudo ln -sf $(pwd)/gpt.py /usr/local/bin/gpt
source ~/.bashrc
echo -e "Installation completed. You can now use the command \033[33mgpt\033[0m anywhere in your terminal."