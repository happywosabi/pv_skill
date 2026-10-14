# 音频模型准备

模型调用脚本在总入口的工程模板中，参见[pdoom脚本说明](pdoom-scripts.md)。这些是源码和配置，模型权重必须在实际ROOT的环境中按任务准备；不要在技能安装目录触发权重下载。

## 实际模型与缓存

原脚本使用Demucs htdemucs_ft、torchaudio.pipelines.MMS_FA与WAV2VEC2_ASR_LARGE_LV60K_960H、mlx-whisper large-v3-turbo，以及一个mel-band-roformer karaoke主唱模型。最后一个的具体权重名/参数没有提交，必须查当前可用模型实际选型，不伪造原作者记录。

common.py应在torch/hf/mlx等导入前加载，让缓存落analysis/.cache；audio-separator另显式指定model_file_dir。所有权重加载和下载遵守当前机器网络/权限，必要模型准备在用户制作授权内，遇到实际阻塞才请求所缺资源。

## 官方资料（2026-10-06核对）

- [Demucs](https://github.com/facebookresearch/demucs)：CLI的`-n htdemucs_ft`选择模型，输出模型名/歌曲名子目录。
- [audio-separator](https://github.com/nomadkaraoke/python-audio-separator)：CLI/API、模型列表与参数。
- [torchaudio模型管线](https://docs.pytorch.org/audio/stable/pipelines.html)：与安装版本一起核对模型和labels接口。
- [MLX Whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper)：原平台路线；非Apple选实际可运行的后端，保持消费者JSON。

使用前以已安装版本的`--help`/API确认当前参数：

```bash
uv run --frozen audio-separator --list_models
uv run --frozen audio-separator --help
```

选有Lead/Backing Vocal输出能力的具体模型，试听困难段；普通Vocals vs Instrumental模型不能保证剥离伴唱。把CLI返回的输出文件映射到lead.wav，保留原件。API支持model_file_dir、output_dir、output_format等；不要把示例模型名当本项目实际使用模型。

models.json记录每个用途的backend、model/weight、revision或版本、缓存位置、设备、来源链接、输入/输出接口和短推理结果。若无法获取revision/哈希如实注明，不虚构。

下载完成≠推理完成。验证torch/torchaudio/设备组合的短推理、Whisper接口与实际分离声部。普通模型加载不等于一次完整全曲分析，已缓存可复用但中间emission/转录依然必须匹配歌曲指纹。
