---
name: pv-timeline
description: "将 PV 分镜落实为歌词与节拍锚定的 TimelineEntry，验证窗口覆盖、复用实例和转场；在分镜或时序数据变化时使用。"
---

# 编排与验证场景时间轴

先读取[共享执行协议](../pv-plan/references/protocol.md)，确定工程根目录、任务目录和当前授权范围。独立调用时也检查本阶段前置产物；状态未创建则交 `$pv-plan` 初始化，不把本项目原歌数据自动当作新歌数据。

## 输入

分镜、正式时序数据和实际场景文件规划。

## AI 执行

读取ENGINE/TREATMENT，编辑当前任务授权的timeline。检查歌词get查询、重复歌词nth、弱起与切点容差，确保切点不晚于需要呈现的词。
用参数复用场景，给实例唯一id；--only使用实例id。窗口触碰为硬切，重叠需检查引擎默认crossfade或场景handlesTransition。现有cut通常对齐beat，不要把它误说成所有切点都在downbeat。
实际加载时间轴并检查覆盖范围、意外空洞/重叠、scene模块与参数、最终时长；输出边界列表供审片。尚未实现的模块明确待建。

## 产物与完成条件

timeline.ts、timeline-review.md和实际边界列表。

查询与实例id有效；完整窗口符合分镜；类型检查通过；首词与切点关系经核对。

## 需要人提供什么

涉及用户明确要求决定的剪辑取舍；常规拍点和窗口实现由AI处理。

## 交接

按共享协议把实际验证、输入指纹、产物和剩余问题写入阶段报告，再登记状态。pv-scene-build或已有场景的pv-preview-review。

## 按需参考

执行本阶段时读取[相关操作参考](../pv-plan/references/project.md)；命令以当前工程代码和平台验证结果为准。
