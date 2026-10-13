# PV 制作技能包

这套技能将本项目从歌曲输入到成片交付拆为 **26 个阶段技能 + 1 个总入口**。源文件保存在 `skills/`，可整体安装到当前用户的 Codex 技能目录；每个技能都定义输入、AI 工作、产物、完成条件、需要人的事项和下一步。

## 从总入口开始

```text
使用 $pv-plan 检查当前项目，判断目前的制作阶段、需要我补充什么，并继续下一项可执行技能。
```

也可以明确目标：

- “使用 $pv-plan，把我提供的新歌制作成 PV，先检查输入。”
- “使用 $pv-plan，只重新导出当前作品的 4K 版本。”
- “使用 $pv-plan，只修改第二段镜头，保留现有概念。”
- “使用 $pv-plan，只修复歌词同步数据。”

若当前会话尚未列出新技能，可以直接指定本项目 `skills/pv-plan/SKILL.md` 的真实路径让 AI 读取；后续阶段通过已安装技能或其文件路径使用。

## 阶段目录

### 总入口

| 技能 | 职责 |
|---|---|
| [$pv-plan](../skills/pv-plan/SKILL.md) | 识别模式、核验进度、指出人的事项并选择下一技能 |

### 输入与环境

| 技能 | 职责 |
|---|---|
| [$pv-input-check](../skills/pv-input-check/SKILL.md) | 检查歌曲与需求输入 |
| [$pv-environment-check](../skills/pv-environment-check/SKILL.md) | 审计制作环境 |
| [$pv-runtime-setup](../skills/pv-runtime-setup/SKILL.md) | 安装基础运行工具 |
| [$pv-python-setup](../skills/pv-python-setup/SKILL.md) | 配置 Python 分析依赖 |
| [$pv-renderer-setup](../skills/pv-renderer-setup/SKILL.md) | 配置浏览器渲染依赖 |
| [$pv-project-adapt](../skills/pv-project-adapt/SKILL.md) | 适配歌曲与工程配置 |

### 模型与音乐时序

| 技能 | 职责 |
|---|---|
| [$pv-model-setup](../skills/pv-model-setup/SKILL.md) | 选择与准备音频模型 |
| [$pv-stem-separation](../skills/pv-stem-separation/SKILL.md) | 分离并校验声部 |
| [$pv-time-calibration](../skills/pv-time-calibration/SKILL.md) | 校准音频时间基准 |
| [$pv-alignment-prep](../skills/pv-alignment-prep/SKILL.md) | 准备歌词对齐中间数据 |
| [$pv-lyric-alignment](../skills/pv-lyric-alignment/SKILL.md) | 生成逐词歌词时间 |
| [$pv-music-analysis](../skills/pv-music-analysis/SKILL.md) | 分析节拍与音乐段落 |
| [$pv-timing-review](../skills/pv-timing-review/SKILL.md) | 审查并修正音画时间 |

### 概念与画面制作

| 技能 | 职责 |
|---|---|
| [$pv-concept](../skills/pv-concept/SKILL.md) | 形成 PV 创作概念 |
| [$pv-style](../skills/pv-style/SKILL.md) | 设计风格与视觉规范 |
| [$pv-storyboard](../skills/pv-storyboard/SKILL.md) | 设计逐段分镜与转场 |
| [$pv-assets](../skills/pv-assets/SKILL.md) | 准备字体、素材与音高资产 |
| [$pv-timeline](../skills/pv-timeline/SKILL.md) | 编排与验证场景时间轴 |
| [$pv-scene-build](../skills/pv-scene-build/SKILL.md) | 实现程序化场景 |
| [$pv-renderer-repair](../skills/pv-renderer-repair/SKILL.md) | 修复渲染器与平台问题 |

### 审片与交付

| 技能 | 职责 |
|---|---|
| [$pv-preview-review](../skills/pv-preview-review/SKILL.md) | 审查预览、静帧与短片 |
| [$pv-render-performance](../skills/pv-render-performance/SKILL.md) | 评估与优化渲染成本 |
| [$pv-montage](../skills/pv-montage/SKILL.md) | 生成片尾场景回放图片 |
| [$pv-export](../skills/pv-export/SKILL.md) | 导出完整 PV 视频 |
| [$pv-final-review](../skills/pv-final-review/SKILL.md) | 验收最终成片 |
| [$pv-delivery](../skills/pv-delivery/SKILL.md) | 交付成片与制作记录 |

## 总入口怎样判断进度

四种模式为 `new-song`、`existing-render`、`revise-scenes`、`repair-analysis`。已提交作品导出会跳过 Python 和模型准备；只修分析不会默认安装浏览器或渲染全片。概念/风格重做和引擎修复可按需要额外启用，不强制每次重走全部阶段。

任务记录位于 `out/pv/<job>/workflow.json`。入口先检查真实输入和产物，再读取阶段状态。完成阶段必须登记报告和主要产物；源输入变化、证据删除/变化或上游失效时，下游显示 `stale`，需要重新核验。仅存在 JSON/MP4 不自动等于对应当前歌曲或已经审片。

状态检查辅助依赖判断，不能替代 AI 的实际听音、看图、审片和用户范围判断。较大媒体使用采样指纹检测变化，完整解码由最终审片阶段执行。

每次阶段交接会说明已验证内容、下一技能、具体阻塞以及现在需要人做什么。普通安装、代码实现和首轮 QA 由 AI 执行；人提供不可推断的素材、表达意图和真实审美反馈。没有人的阻塞就直接推进；不为每个阶段增加确认关卡。

## 安装和独立检查

在本技能仓库根目录执行安装和测试命令；检查制作工程时须明确其路径。安装器先完整检查冲突：已有不同内容的同名技能会拒绝覆盖，已有相同版本会复用。

```bash
python3 skills/pv-plan/scripts/install.py
python3 skills/pv-plan/scripts/install.py --apply
python3 skills/pv-plan/scripts/workflow.py inspect --root /path/to/pdoom-video
PYTHONDONTWRITEBYTECODE=1 python3 skills/pv-plan/scripts/test_workflow.py
```

安装器默认目标为 `$CODEX_HOME/skills`，未设置时为 `~/.codex/skills`，也可用 `--dest` 指定。技能包须整体安装，同级技能的共享协议和阶段链接彼此依赖。复制版本与项目源码不同步时，先审阅版本差异，再更新确认由本项目维护的安装副本；不要覆盖用户的其他技能。

初始化和恢复的命令见 [共享协议](../skills/pv-plan/references/protocol.md)。`inspect` 默认只读，不安装包/模型、不创建制作任务；已有任务用 `--job` 检查其 brief 中的音频。新歌曲必须指定真实输入，初始化不会偷偷复用原歌。

## 补齐的制作环节与边界

- `pv-alignment-prep/scripts/prepare_vocal.py` 补齐原仓库缺失的 `vocals16k.wav` 生成入口，经项目 `common.load_stem` 应用一次既定校正。旧输出内容不同默认拒绝覆盖，核对后才用 `--replace`。
- 主唱分离模型的具体原始权重名未提交，模型技能要求查当前可用模型、实际试用并记录，禁止编造原作者配置。
- 原歌偏移、固定速度/拍号、CTC字符表、歌词 FIX、分镜锚点和局部音高曲线都需换歌适配。
- 非 Apple 环境需要真正适配 MLX Whisper 和 Chrome Metal，单纯安装依赖不能证明支持。
- 大模型、声部、渲染和任务记录保持在忽略目录；不改写歌曲/字体的独立许可。
- 技能包创建与验证不会自动开始制作新歌；外部发布、上传和发消息仍需用户明确指令。

WAV helper 的真实读写测试需 numpy、soundfile；可在现有分析环境或隔离测试环境运行 `skills/pv-alignment-prep/scripts/test_prepare_vocal.py`，不必为了技能验证安装全套大模型。
