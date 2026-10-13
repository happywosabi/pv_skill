---
name: pv-music-analysis
description: "生成 PV 的节拍/小节、段落、声部能量和鼓点/人声起音数据；适配当前歌曲的速度、拍号与结构。"
---

# 分析节拍与音乐段落

先读取[共享执行协议](../pv-plan/references/protocol.md)，确定工程根目录、任务目录和当前授权范围。独立调用时也检查本阶段前置产物；状态未创建则交 `$pv-plan` 初始化，不把本项目原歌数据自动当作新歌数据。

## 输入

混音、已校时声部、人声特征和段落理解。

## AI 执行

运行analyze.py前核对fit_grid速度范围、恒定速度假设、拍号、小节第一拍相位与SECTION_BARS。原歌125–138 BPM/4拍/固定段落不可原样用于新歌；变速曲目需要实际的局部beat/downbeat序列。
结合鼓点、和声变化和人声弱起判断段落，把人工音乐判断写成当前歌配置。执行 uv run --frozen python analyze.py --plots，输出节拍、小节、sections、8路100fps包络和4类onsets。
检查全曲多区间节拍对齐和包络归一化/长度。保持AudioData消费者字段；数据语法通过不代表音乐结构正确。

## 产物与完成条件

data/audio.json、audio_overview/分段QA图、music-analysis.md和结构表。

节拍严格递增；段落覆盖合理；包络完整有界；鼓点/小节相位和弱起经核对。

## 需要人提供什么

风格或段落存在真实歧义时征询用户偏好；常规音乐结构识别由AI完成。

## 交接

按共享协议把实际验证、输入指纹、产物和剩余问题写入阶段报告，再登记状态。pv-timing-review。

## 按需参考

执行本阶段时读取[相关操作参考](../pv-plan/references/analysis.md)；命令以当前工程代码和平台验证结果为准。
