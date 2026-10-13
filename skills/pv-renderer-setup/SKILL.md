---
name: pv-renderer-setup
description: "安装 Bun 锁定依赖并验证 Chrome/WebGL2/ffmpeg 的 PV 渲染链；用于初次预览、导出或渲染环境恢复。"
---

# 配置浏览器渲染依赖

先读取[共享执行协议](../pv-plan/references/protocol.md)，确定工程根目录、任务目录和当前授权范围。独立调用时也检查本阶段前置产物；状态未创建则交 `$pv-plan` 初始化，不把本项目原歌数据自动当作新歌数据。

## 输入

Bun、Chrome、ffmpeg和app工程。

## AI 执行

在 app/ 执行 bun install --frozen-lockfile。分别运行应用与脚本类型检查，运行 bunx vite build。构建是代码验证；render.ts默认使用Vite服务器，并不要求从dist渲染。
确认项目使用 playwright-core + channel: chrome，包安装不等于下载了浏览器。复用现有Chrome；缺失时按运行工具阶段安装。Linux/Windows必须去掉或配置实际适用的Metal参数，不能把软件渲染当成硬件GPU验证。
已有场景运行小范围GPU/静帧启动检查并收集SCENE ERRORS/浏览器日志。新歌场景尚未完成时可用独立WebGL2页面验证基础环境，再把完整场景验收留给预览阶段；不因待建场景造成安装与场景实现的循环依赖。旧场景不兼容属于代码问题，交 pv-renderer-repair；不要靠 --only 掩盖全片错误。

## 产物与完成条件

renderer-setup.md：锁定安装、两个类型检查、构建和浏览器/WebGL启动证据。

实际浏览器可启动、WebGL2与目标尺寸可用；缺资产/场景错误不被误报为成功。

## 需要人提供什么

需要用户提供指定浏览器/受管机器权限时；普通项目代码修复由AI处理。

## 交接

按共享协议把实际验证、输入指纹、产物和剩余问题写入阶段报告，再登记状态。新制作走场景/资产路径；已有作品可进入 pv-preview-review。

## 按需参考

执行本阶段时读取[相关操作参考](../pv-plan/references/environment.md)；命令以当前工程代码和平台验证结果为准。
