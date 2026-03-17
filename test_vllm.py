import openai

# 先用 127.0.0.1 测试
client = openai.OpenAI(
    base_url="http://192.168.20.51:8000/v1",
    api_key="dummy"
)

try:
    resp = client.chat.completions.create(
        model="/mnt/d/agent_litkb/r1_model_7b_awq",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "你好，简单自我介绍一下。"}
        ],
        max_tokens=64,
    )
    print("✅ 成功:", resp.choices[0].message.content)
except Exception as e:
    print("❌ 失败:", repr(e))