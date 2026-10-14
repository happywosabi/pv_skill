---
name: pv-python-setup
description: "安装、验证并按平台适配 PV 的 Python 音频分析环境；仅在生成或修复音频时序数据时使用。"
---

# 配置 Python 分析依赖

先读取[共享执行协议](../pv-plan/references/protocol.md)，确定工程根目录、任务目录和当前授权范围。独立调用时也检查本阶段前置产物；状态未创建则交 `$pv-plan` 初始化，不把本项目原歌数据自动当作新歌数据。

## 输入

兼容 Python、uv、环境报告和分析脚本。

## AI 执行

从 analysis/ 使用 uv sync --locked，检查声明与锁一致且保留锁文件；后续已验证环境可用 --frozen 运行。依赖声明与锁不一致时定位差异，别静默升级所有包。读取环境参考中的非 Apple 路线：MLX 不兼容时，在独立环境/有证据的项目适配中替换 Whisper 后端并保持其 JSON接口，不能直接把失败依赖忽略后宣称完成。
用 uv run --frozen python 做导入检查：numpy、scipy、librosa、soundfile、torch、torchaudio、numba、soxr、fontTools、audio_separator及实际 Whisper后端。numba/soxr虽可能为传递依赖，也确实被脚本使用。
检查 torch/torchaudio ABI 和音频读写；选择 MPS/CPU/CUDA需验证实际脚本会使用该设备。该阶段导入不应下载权重。

## 产物与完成条件

python-setup.md、可复用分析环境和平台适配说明。

所有将要调用的模块能导入；可读音频并运行短的特征计算；依赖锁变化若必要有明确原因。

## 需要人提供什么

缺少必须的镜像/凭据或平台无法满足已选路线时；AI自行处理常规依赖冲突。

## 交接

按共享协议把实际验证、输入指纹、产物和剩余问题写入阶段报告，再登记状态。pv-model-setup。

## 按需参考

执行本阶段时读取[相关操作参考](../pv-plan/references/environment.md)；命令以当前工程代码和平台验证结果为准。

## pdoom 脚本与工程资源

本技能涉及的原项目脚本、依赖配置和必要渲染源码已随总入口打包，位置与运行方法见[内置脚本说明](../pv-plan/references/pdoom-scripts.md)。使用用户现有工程或先把模板复制到实际ROOT；不要在技能安装目录执行会写缓存/产物的脚本。只需概念或风格草案时可先开展该工作，无需启动完整工程。
