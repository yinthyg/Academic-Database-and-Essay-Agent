#!/bin/bash
source ~/vllm_env/bin/activate
cd /mnt/d/agent_litkb/webui
echo "使用虚拟环境: ~/vllm_env"
python app.py
