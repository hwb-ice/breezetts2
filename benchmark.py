"""Measure actual SSE audio arrival, throughput, and save generated speech."""
import argparse, base64, json, time, urllib.request, wave
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--chunk', type=int, default=40)
p.add_argument('--cfg', type=float, default=1)
p.add_argument('--mode', default='tag_aware')
p.add_argument('--url', default='http://127.0.0.1:7860/v1/audio/speech')
p.add_argument('--name', default='test')
p.add_argument('--text', default='你好，这里是本地语音助手。今天我们测试中文语音合成，看看这台电脑能否流畅地实时朗读。希望你听到的声音自然清晰。')
a = p.parse_args()
payload = {'model':'breeze-tts-2','input':a.text,'response_format':'pcm','stream_format':'sse','options':{'text_chunk_size':a.chunk,'text_chunk_mode':a.mode,'guidance_scale':a.cfg,'seed':42}}
req = urllib.request.Request(a.url, data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
local_http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
start = time.perf_counter()
events = []
with local_http.open(req, timeout=600) as response:
    for line in response:
        if line.startswith(b'data: '):
            raw = line[6:].strip()
            if raw == b'[DONE]': break
            event = json.loads(raw)
            if event.get('type')=='error' or 'error' in event: raise RuntimeError(event)
            event['_arrival_s'] = time.perf_counter()-start
            events.append(event)
            print(json.dumps({k:v for k,v in event.items() if not isinstance(v,str) or len(v)<400},ensure_ascii=False),flush=True)
elapsed = time.perf_counter()-start
out=Path('outputs'); out.mkdir(exist_ok=True)
(out/f'{a.name}.events.json').write_text(json.dumps({'elapsed_s':elapsed,'request':payload,'events':events},ensure_ascii=False),encoding='utf-8')
chunks=[e for e in events if e.get('type')=='speech.audio.delta']
pcm=b''.join(base64.b64decode(e['audio']) for e in chunks)
if not pcm: raise RuntimeError('No audio received')
with wave.open(str(out/f'{a.name}.wav'),'wb') as wav:
    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(24000); wav.writeframes(pcm)
duration=len(pcm)/48000
summary={'name':a.name,'chunk':a.chunk,'cfg':a.cfg,'elapsed_s':elapsed,'audio_s':duration,'rtf':elapsed/duration,'first_audio_s':chunks[0]['_arrival_s'],'chunks':len(chunks)}
playback_end=chunks[0]['_arrival_s']; gaps=[]
for e in chunks:
    gap=max(0,e['_arrival_s']-playback_end)
    if gap>0.05: gaps.append(gap)
    playback_end=max(playback_end,e['_arrival_s'])+len(base64.b64decode(e['audio']))/48000
summary['playback_gap_count']=len(gaps)
summary['playback_gap_s']=sum(gaps)
(out/f'{a.name}.metrics.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
