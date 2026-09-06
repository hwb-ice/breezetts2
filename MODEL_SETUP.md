# 模型准备

1. 从 README 链接下载 `breeze-tts-2-q8_0.gguf` 到 `models/Breeze-TTS-2-GGUF/`。
2. 临时将 `server.json` 的模型路径改为 Q8 文件，运行 `start.bat`，等待模型加载。加载时运行库会把嵌入的 tokenizer/config 解包至 `%TEMP%/audiocpp-gguf/<fingerprint>/`。
3. 停止服务。在该目录中找到包含本模型 `config.json`、`tokenizer.json` 和 `audio_tokenizer/config.json` 的目录。可以查看 `config.json` 确认为 Breeze 模型。
4. 将下面的 `<sidecar-directory>` 替换为第 3 步找到的路径，执行转换：

```powershell
.\runtime\audiocpp_gguf.exe --input models/Breeze-TTS-2-GGUF/breeze-tts-2-q8_0.gguf --output models/Breeze-TTS-2-GGUF/breeze-tts-2-q4_k.gguf --type q4_k --root '<sidecar-directory>' --allow-missing-model-spec
```

转换可能需要数分钟。该 Q4_K 是由 Q8 再量化而成，不是从原始 BF16 直接量化；音质需自行评估。转换器关于未嵌入 model spec 的提示在此流程中是预期行为，`server.json` 已通过 `model_spec_override` 指定本地规格。

5. 将 `server.json` 路径改回 Q4_K 文件，重新启动。保留 `runtime/model_specs/breeze_tts.json`。

本机生成的 Q4_K 文件为 4,026,005,184 字节。模型许可与代码许可独立，见 README 许可说明。
