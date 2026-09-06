# Breeze TTS 2 · RTX 4060 本地实时语音

面向 Windows / RTX 4060 Laptop 8GB 的非官方部署与优化。基于 [audio.cpp v0.7.2](https://github.com/0xShug0/audio.cpp)，采用 Q4_K、CUDA 和原生声学帧流式输出，提供本地实时播放网页及 HTTP 接口。

## 已实现

- 首包 1 个声学帧，随后逐步增至 4 / 8 帧，平衡开口延迟与吞吐。
- 解码保留 25 帧左侧上下文，整句完成前即可输出真实 PCM。
- 保留文本编码图、首包解码图与流式生成所用计算图。
- 本地 HTTP 直接连接，禁用代理发现与 Nagle 小包等待。
- 模型常驻、启动自动预热；**不启用 GPU 保活**。
- 浏览器收到音频即排程播放，支持下载合并 WAV。

## 实测与限制

RTX 4060 Laptop 8GB，Windows，Q4_K，CFG 1。请求前初始化 HTTP 客户端，测量从发送请求到收到首个 PCM 包；未使用缓存音频。以下是单次结果，不代表分位数或延迟保证。

| 场景 | 首包 | 音频长度 | 生成耗时 | 实时倍速 | 时序断流 |
|---|---:|---:|---:|---:|---:|
| 空闲后短句 | 472ms | 4.72s | 3.03s | 1.56× | 0 |
| 连续请求 A | 220ms | 6.80s | 3.89s | 1.75× | 0 |
| 连续请求 B | 221ms | 7.20s | 4.17s | 1.73× | 0 |

**无法保证空闲后的首包低于 300ms。** “时序断流”根据到达时间与 PCM 时长计算，并非实录声卡测量；实际播放另有浏览器与声卡延迟。低比特量化及小窗口流式解码可能影响音质，尚未做正式人工听评。原始数据见 [benchmarks](benchmarks)。

## 环境与构建

需要 Windows x64、Python 3.10+、Git、NVIDIA 驱动，以及安装了 C++、Windows SDK、CMake/Ninja 的 Visual Studio Build Tools。

```powershell
git clone https://github.com/Emilia296/breezetts2.git
cd breezetts2
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

构建脚本固定上游提交 `a2a4d4f34c0960edf1bf78e392de1fbce5a855e6`，应用 [原生补丁](patches/audio-cpp-streaming.patch)，编译 Breeze 专用运行时，并下载 v0.7.2 Windows CUDA 12.4 发布包中的 CUDA 后端与运行库。无需重新编译 CUDA 内核。Visual Studio 不在默认位置时可传 `-VsInstall 'D:\vstudio'`。

模型权重不随本仓库分发。下载 [Breeze TTS 2 Q8 GGUF](https://huggingface.co/audio-cpp/audio.cpp-gguf/tree/main/Breeze-TTS-2-GGUF)，放入 `models/Breeze-TTS-2-GGUF/`。

本机测评使用从 Q8 再量化得到的 Q4_K 文件。首次使用可以先将 `server.json` 中模型路径改为 Q8 文件；按 [模型准备说明](MODEL_SETUP.md) 转换后再切回 Q4_K。Q8 显存压力更高，不应套用表中的 Q4_K 数值。

## 启动与使用

```powershell
.\start.bat
```

- 实时试听：http://127.0.0.1:7861
- 原生界面 / API：http://127.0.0.1:7860
- 停止：`powershell -ExecutionPolicy Bypass -File .\stop.ps1`
- 预热完成标志：`logs/warmup.out.log` 中出现 `Model warmed up`。

服务只监听 `127.0.0.1`。浏览器中的停止按钮仅停止播放，不取消已提交的 GPU 请求。长文本默认每 120 字分段；每段 `max_tokens=600` 是约 48 秒的声学帧上限。

```powershell
python benchmark.py --name local --chunk 120 --url http://127.0.0.1:7861/speech
```

实时适配层 `POST /speech` 与原生 `POST /v1/audio/speech` 使用相同请求结构：

```json
{"model":"breeze-tts-2","input":"你好，这里是本地语音助手。","response_format":"pcm","stream_format":"sse","options":{"guidance_scale":1,"text_chunk_size":120,"seed":42}}
```

`speech.audio.delta.audio` 为 Base64 PCM16LE，24000 Hz，单声道；以 `speech.audio.done` 和 `[DONE]` 结束。

## 许可与来源

项目代码及上游补丁使用 Apache-2.0，保留 [audio.cpp](https://github.com/0xShug0/audio.cpp) 许可声明。Breeze TTS 2 模型、衍生权重和自托管输出另受 [BreezeBlue 模型许可](https://github.com/breezeblue-ai/breeze-tts/blob/main/MODEL_LICENSE)约束，限研究与非商业用途；代码许可不授予模型商用权利。
