---
name: pv-environment-check
description: "只读审计 PV 工程的系统、Python/uv、Bun、Chrome、ffmpeg、模型缓存和存储条件；用于安装前或环境故障定位。"
---

# 审计制作环境

先读取[共享执行协议](../pv-plan/references/protocol.md)，确定工程根目录、任务目录和当前授权范围。独立调用时也检查本阶段前置产物；状态未创建则交 `$pv-plan` 初始化，不把本项目原歌数据自动当作新歌数据。

## 输入

任务模式和工程路径；输入缺失时也可独立进行。

## AI 执行

运行 inspect，补充操作系统/架构、可执行文件实际路径和版本、磁盘空间。视频模式检查 Chrome 的真实安装与 ffmpeg libx264；分析模式检查 Python >=3.12、uv、PyTorch设备和 Whisper后端。
把环境分为原项目的 Apple Silicon 路线与需要适配的 Linux/Windows 路线。当前 pyproject 含 mlx-whisper，CTC脚本只自动选择 MPS/CPU，导出脚本写死 ANGLE Metal。安装依赖不能自动证明这些路径已可运行。
列出必要、可复用、缺失和平台不兼容项；仅导出时跳过 Python/模型；仅分析时不要求 Bun/浏览器。不要为审计调用会隐式下载模型的 get_model 或转录操作。

## 产物与完成条件

environment.json / environment.md：路径、版本、设备、空间和最小安装清单。

报告包含当前模式所需组件；平台风险被实际识别；未把存在可执行文件等同于 GPU 可用。

## 需要人提供什么

只有所需工具无法在当前权限下安装、离线镜像/网络凭据缺失、或必须换机器时才请求具体协助。

## 交接

按共享协议把实际验证、输入指纹、产物和剩余问题写入阶段报告，再登记状态。pv-runtime-setup；平台代码适配可启用 pv-renderer-repair。

## 按需参考

执行本阶段时读取[相关操作参考](../pv-plan/references/environment.md)；命令以当前工程代码和平台验证结果为准。
