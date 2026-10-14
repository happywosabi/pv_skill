# PV Skills

从一首歌到程序化 PV 的完整 Codex 技能包：**1 个总入口 + 26 个阶段技能**。

总入口 `$pv-plan` 检查用户输入、核验已有产物、识别制作进度，说明当前需要人提供什么，并选择下一项可执行技能。每个阶段都包含输入、AI 工作、产物、完成条件和交接说明。

## 安装

安装器和工作流助手需要 Python 3.9 或以上。音频分析工程另需 Python 3.12 或以上；只安装技能无需下载音频模型。

```bash
git clone https://github.com/happywosabi/pv_skill.git
cd pv_skill
python3 skills/pv-plan/scripts/install.py
python3 skills/pv-plan/scripts/install.py --apply
```

第一条安装命令只检查目录与冲突；`--apply` 才安装。默认目标为 `$CODEX_HOME/skills`，未设置时为 `~/.codex/skills`，可用 `--dest` 指定。

请整体安装，同级技能共享路由、参考和执行协议。安装器复用相同版本，并拒绝覆盖内容不同的已有同名技能。

## 使用

```text
使用 $pv-plan 检查当前项目，判断目前属于哪个制作阶段、需要我补充什么，并继续下一项可执行技能。
```

也可指定范围：为新歌制作完整 PV、重新导出已有作品、修改已有场景，或只修复歌词和音乐时序数据。

当前会话未列出新技能时，可直接让 AI 读取安装目录的 `pv-plan/SKILL.md`。所有阶段都可独立调用，并核对前置产物。

## 覆盖范围

| 阶段 | 内容 |
|---|---|
| 输入与环境 | 歌曲/歌词/需求检查、环境审计、工具和依赖安装、换歌适配 |
| 模型与时序 | 模型准备、声部分离、时间校准、CTC/Whisper、人声特征、歌词和节拍分析、同步审查 |
| 概念与画面 | 核心概念、视觉风格、分镜、字体/素材/音高资产、时间轴、场景实现和渲染修复 |
| 审片与交付 | 预览/静帧/短片、性能、蒙太奇图片、正式导出、成片验收与交付 |

详见 [完整阶段目录与使用说明](docs/PV_SKILLS.md) 和 [总入口](skills/pv-plan/SKILL.md)。

## 制作工程与任务记录

本仓库提供技能、辅助脚本及 [pdoom-video](https://github.com/mexicat/pdoom-video) 的工程代码模板。模板位于 `skills/pv-plan/assets/pdoom-project/`，随总入口一起安装，含11个Python分析脚本、导出脚本、渲染引擎/场景代码、依赖锁与API文档，共83个上游文件。来源提交、文件哈希和原MIT许可均保留。详见 [脚本清单与运行说明](skills/pv-plan/references/pdoom-scripts.md)。

已有制作工程可以直接复用；没有工程时，将模板复制到任务工作目录：

```bash
python3 skills/pv-plan/scripts/bootstrap_project.py --destination ../my-pv
python3 skills/pv-plan/scripts/bootstrap_project.py --destination ../my-pv --apply
python3 skills/pv-plan/scripts/workflow.py inspect --root ../my-pv
```

默认只读预检查；`--apply`才复制，拒绝覆盖不同内容的现有文件。模板不含歌曲、原始歌词、时序JSON、字体、蒙太奇图、声部和模型权重，这些由对应技能在真实制作任务中补齐。不要在安装的技能assets目录执行分析、改写配置或输出成片。

在实际工程中调用入口，或明确提供工程根目录：

```bash
python3 skills/pv-plan/scripts/workflow.py inspect --root /path/to/pdoom-video
```

`pv_skill` 仓库目录不是制作工程根目录。任务状态和生成结果保存在制作工程的 `out/pv/<job>/`。源输入、证据或依赖变化时，已完成阶段会显示为过期，需要重新核验；状态助手不代替实际听音、看图和成片验收。

新歌、非英语、变速曲目和不同画幅需要实际适配原工程规则。技能会检查并实施相关适配，不承诺只更换音频即可完成新作品。

## 验证

状态与安装器检查仅使用 Python 标准库：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 skills/pv-plan/scripts/test_workflow.py
PYTHONDONTWRITEBYTECODE=1 python3 skills/pv-plan/scripts/test_bootstrap_project.py
```

真实 WAV 读写检查需要 `numpy` 和 `soundfile`，可在隔离环境或已有分析环境执行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install numpy soundfile
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python skills/pv-alignment-prep/scripts/test_prepare_vocal.py
```

Windows 使用 `.venv\Scripts\python.exe` 替换示例解释器路径。

## 来源与许可

流程调查基于 [mexicat/pdoom-video](https://github.com/mexicat/pdoom-video)。保留其工程约束与来源说明；本技能包提供路由、阶段说明和辅助脚本。

代码与文档采用 [MIT License](LICENSE)，包含上游来源声明。歌曲、歌词、字体、模型权重与生成视频各自的许可由其来源决定。
