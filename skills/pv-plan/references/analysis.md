# 音频分析依赖与验收

## 真实顺序

混音/歌词 → 分离声部 → 测量并配置时间偏移 → 校时16k人声、CTC emissions、Whisper核对、vocal_feats → align与analyze → 图/听核验 → 正式JSON。

align与analyze在前置特征齐备后可独立做。align读取8组emission（主融合6组，lead为交叉检查）、whisper_turbo_prompt.json和vocal_feats.npz；analyze也读取vocal_feats。无法只运行README末尾两条命令就从零重建。

## 补齐16k输入

原whisper_run.py读取work/vocals16k.wav，没有生成入口。本套pv-alignment-prep/scripts/prepare_vocal.py通过common.load_stem('vocals',sr=16000)生成它，沿用已测校正，只应用一次。重复执行内容一致则复用，不一致需明确重建。

模型准备/时间校正完成后，在analysis/执行：

```bash
uv run --frozen python SKILLS/pv-alignment-prep/scripts/prepare_vocal.py --root ROOT
uv run --frozen python ctc_emissions.py
uv run --frozen python whisper_run.py turbo
uv run --frozen python vocal_feats.py
uv run --frozen python align.py --plots
uv run --frozen python analyze.py --plots
uv run --frozen python zoom.py lines
```

新平台后端若输出名不同，应明确适配consumer或输出兼容文件，不能让align默用旧Whisper JSON。

## 数据接口与检查

lyrics.json：lines[].text/start/end/words，词的w/start/end/conf和可选syl；源歌词词序一致、范围在音频内、word非负非反向、不重叠；syl须在词内且递增。置信度是模型/声道/Whisper一致性的经验评分，不是校准准确率。

audio.json：duration/bpm/fps/beats/downbeats/sections，rms/low/mid/high/vocal/drums/bass/other（可位于features或顶层），onsets的kick/snare/hat/vocal。包络采样数量对应duration*fps，值0..1；事件时间/强度有效、序列有序；段落和弱起用音乐证据核对。

结构检查见入口inspect，但它不能证明唱词或拍位正确。逐行QA比较final/fused-ctc/subword/单模型/Whisper；zoom看细节，结合实际听音修正。保存疑难词、修正原因和剩余时间误差。正式数据变化会影响时间轴、场景和plates。

## 当前歌曲专属规则

FIX、pron中的专有缩写、N_FRAMES=7833、BPM搜索125–138、4/4相位、SECTION_BARS和QA的132BPM网格需换歌适配。原common将stem提前约23ms；已经gapless对齐的stem再裁会制造新误差。原fuse-pitch.ts为预提取结果，新歌音高资产应有提取脚本与歌词相对锚点。
