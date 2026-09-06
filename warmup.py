import json,time,urllib.request
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
for _ in range(120):
    try:
        urllib.request.urlopen('http://127.0.0.1:7860/health',timeout=2).close()
        break
    except OSError: time.sleep(1)
else: raise RuntimeError('Server did not become ready')
body={'model':'breeze-tts-2','input':'你好，这里是本地语音助手。今天我们测试中文语音合成，看看这台电脑能否流畅地实时朗读。希望你听到的声音自然清晰。','response_format':'pcm','stream_format':'sse','options':{'guidance_scale':1,'seed':42}}
req=urllib.request.Request('http://127.0.0.1:7860/v1/audio/speech',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=180) as response: response.read()
print('Model warmed up',flush=True)
