---
name: pv-scene-build
description: "根据已确定分镜与视觉规范实现或修改 PV 场景代码、逐词歌词动画和镜头；覆盖2D/3D/GLSL场景制作。"
---

# 实现程序化场景

先读取[共享执行协议](../pv-plan/references/protocol.md)，确定工程根目录、任务目录和当前授权范围。独立调用时也检查本阶段前置产物；状态未创建则交 `$pv-plan` 初始化，不把本项目原歌数据自动当作新歌数据。

## 输入

场景规格、风格、资产和时间轴。

## AI 执行

先读docs/ENGINE.md与docs/TREATMENT.md；匹配TypeScript风格，默认导出Scene类。把重计算放init，按f.t/歌词/节拍/seeded randomness生成画面；逐词或音节进度来自Lyrics API。
根据场景需要组合Canvas2D、LineBatch、Three.js几何/实例化和GLSL/SDF。render完整覆盖HalfFloat线性HDR目标，按共享参数输出后期；世界/屏幕和逻辑/物理像素正确区分。
实现当前请求的场景和交接，不擅自重做全片。尽量无状态以支持乱序子帧；确有状态则实现reset/preroll并使用固定采样。处理字体kerning、首末词和HUD/安全区；引擎问题交pv-renderer-repair。

## 产物与完成条件

场景/helper代码、scene-build.md、关键时间静帧/短片。

类型/构建及目标场景渲染通过；逐词同步可读；1080p和目标scale检查；无浏览器/场景错误。

## 需要人提供什么

只有实质审美反馈或外部素材缺失需要人；AI完成具体代码和首轮审查。

## 交接

按共享协议把实际验证、输入指纹、产物和剩余问题写入阶段报告，再登记状态。pv-preview-review。

## 按需参考

执行本阶段时读取[相关操作参考](../pv-plan/references/project.md)；命令以当前工程代码和平台验证结果为准。

## pdoom 脚本与工程资源

本技能涉及的原项目脚本、依赖配置和必要渲染源码已随总入口打包，位置与运行方法见[内置脚本说明](../pv-plan/references/pdoom-scripts.md)。使用用户现有工程或先把模板复制到实际ROOT；不要在技能安装目录执行会写缓存/产物的脚本。只需概念或风格草案时可先开展该工作，无需启动完整工程。
