import openvino_genai
print('OpenVINO GenAI imported OK')
print('Trying NPU...')
p = openvino_genai.LLMPipeline('./tinyllama-model', 'NPU')
print('Model loaded on NPU!')
config = openvino_genai.GenerationConfig()
config.max_new_tokens = 10
result = p.generate('Hi', config)
print(f'Result: {result}')
