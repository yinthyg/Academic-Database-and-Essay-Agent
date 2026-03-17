#!/bin/bash
source ~/vllm_env/bin/activate
cd /mnt/d/agent_litkb
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo "使用虚拟环境: ~/vllm_env"
echo "当前目录: $(pwd)"
echo "启动后端服务..."
python -m backend.main
