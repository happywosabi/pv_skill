---
name: pv-alignment-prep
description: "生成校时后的16k人声、两模型多声道CTC概率、Whisper核对JSON和人声特征缓存；补齐歌词对齐全部前置输入。"
---

# 准备歌词对齐中间数据

先读取[共享执行协议](../pv-plan/references/protocol.md)，确定工程根目录、任务目录和当前授权范围。独立调用时也检查本阶段前置产物；状态未创建则交 `$pv-plan` 初始化，不把本项目原歌数据自动当作新歌数据。

## 输入

校时后的声部、已加载模型和正确歌词。

## AI 执行

使用本skill scripts/prepare_vocal.py --root ROOT准备work/vocals16k.wav；脚本通过common.load_stem读取已校时人声，已有不同内容默认不覆盖。换歌确认旧产物过期后用--replace重建并记录。
在analysis/运行 uv run --frozen python ctc_emissions.py、whisper_run.py turbo、vocal_feats.py。默认CTC为vocals/lead/vocL/vocR各两模型，共8组emission；align.py的主融合用6组，交叉检查还需要lead两组。
检查概率矩阵时间长度一致且无NaN，Whisper包含segments[].words及word/start/end，vocal_feats的hop与数组长度一致。切换非MLX后端要保持whisper_turbo_prompt.json等消费者接口；所有缓存记录当前音频与模型来源。

## 产物与完成条件

vocals16k.wav、8个emission_*.npy、whisper_turbo_prompt.json、vocal_feats.npz、alignment-prep.md。

产物满足真实消费者字段和长度；人声为16k单声道且时间校正只应用一次。

## 需要人提供什么

无额外人类步骤；源素材或平台阻塞交对应前置skill。

## 交接

按共享协议把实际验证、输入指纹、产物和剩余问题写入阶段报告，再登记状态。pv-lyric-alignment和pv-music-analysis可独立执行。

## 按需参考

执行本阶段时读取[相关操作参考](../pv-plan/references/analysis.md)；命令以当前工程代码和平台验证结果为准。

人声准备 helper：[scripts/prepare_vocal.py](scripts/prepare_vocal.py)。它需要分析环境的 soundfile、numpy、soxr 与项目 common.py；使用 `uv run --frozen python` 执行。
