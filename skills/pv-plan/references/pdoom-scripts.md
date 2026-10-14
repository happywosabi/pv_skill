# 随技能分发的 pdoom 脚本和工程模板

## 位置与来源

总入口技能内置[工程代码快照](../assets/pdoom-project/)，所以整套技能安装后无需依赖克隆仓库的绝对路径找这些脚本。

上游为 [mexicat/pdoom-video](https://github.com/mexicat/pdoom-video)，固定提交 `fa164b74fd0b26a99375715b619c55b4a0fb3d05`。原始代码、配置、引擎和场景保持该提交内容；[UPSTREAM.json](../assets/pdoom-project/UPSTREAM.json)记录来源、83个文件的SHA256/长度和未打包的参考素材路径。[上游MIT许可](../assets/pdoom-project/LICENSE)随快照保留。

这份快照用于准备工作工程、阅读实现和在已授权范围内适配，不是默认可以直接播放的成片工程。不要直接在已安装技能的assets目录运行分析：common.py会在那里创建缓存/中间结果，源码和新歌配置也需要可写的任务工作目录。

## 准备工作目录

有用户指定的现有pdoom工程就直接核验并复用，不强行替换。没有工程时，使用[bootstrap_project.py](../scripts/bootstrap_project.py)复制模板到用户任务目录：

```bash
python3 SKILLS/pv-plan/scripts/bootstrap_project.py --destination ROOT
python3 SKILLS/pv-plan/scripts/bootstrap_project.py --destination ROOT --apply
python3 SKILLS/pv-plan/scripts/workflow.py inspect --root ROOT
```

第一条只读检查来源和目标冲突。`--apply`复制，先完整核验文件哈希，拒绝覆盖已有不同内容；同内容重复执行复用，不重写。目标不能位于技能资源内部。它不安装依赖、不下载模型/字体、不启动渲染。

复制后，`.pv-project-source.json`保留来源与排除素材清单。AI记录ROOT，后续命令均以这个工作工程为准。`pv-project-adapt`负责换歌路径/语言/节奏/窗口规则，`pv-assets`负责实际需要的字体和素材。

## 分析脚本映射

| 模板内路径（复制后相对ROOT） | 用途 / 调用技能 |
|---|---|
| `analysis/common.py` | 路径、缓存、声部校时和音频读取；所有分析阶段共享 |
| `analysis/ctc_emissions.py` | 多模型/多声道字符概率；`pv-alignment-prep` |
| `analysis/whisper_run.py` | Whisper逐词核对；`pv-alignment-prep` |
| `analysis/vocal_feats.py` | RMS、音高与起音缓存；`pv-alignment-prep` |
| `analysis/pron.py` | 专有词/缩写发音；`pv-project-adapt`、`pv-lyric-alignment` |
| `analysis/ctcalign.py` | 整曲CTC/Viterbi与概率融合；`pv-lyric-alignment` |
| `analysis/align.py` | 精修、置信度和逐词JSON；`pv-lyric-alignment` |
| `analysis/analyze.py` | 节拍、小节、段落、包络和事件JSON；`pv-music-analysis` |
| `analysis/qa_plot.py` | 对齐审查绘图，被align.py调用；`pv-timing-review` |
| `analysis/zoom.py` | 局部/逐行声谱与时间边界；`pv-timing-review` |
| `analysis/make_fonts.py` | 可变字体静态实例；`pv-assets` |
| `analysis/pyproject.toml`、`analysis/uv.lock` | 原分析依赖与锁；`pv-python-setup` |

`whisper_run.py`仍需要16k输入，因此技能已有的[prepare_vocal.py](../../pv-alignment-prep/scripts/prepare_vocal.py)在复制后的ROOT上准备它。前置声部/校时/模型齐备后，在ROOT/analysis运行原脚本；完整顺序见[分析参考](analysis.md)。

## 渲染依赖闭包

`app/scripts/render.ts`含stills、sheet、perf、plates和video入口，依赖Bun、Playwright、Chrome、ffmpeg以及浏览器页面的`window.__pdoom`。为避免只拿导出脚本却缺页面/API，模板还包含：

- `app/src/engine/`、`app/src/scenes/`、`app/src/main.ts`、`app/src/timeline.ts`：场景、合成、读回和导出接口。
- `app/index.html`、`app/vite.config.ts`：预览/导出页面与资产访问。
- `app/package.json`、`app/bun.lock`、两个tsconfig、`app/plates.json`：锁定依赖、类型检查和回放选时。
- `docs/ENGINE.md`、`docs/TREATMENT.md`：原API和原歌视觉方案，供适配参考。

运行时从ROOT/app执行`bun scripts/render.ts ...`，不要从技能assets目录导出。命令和审查见[渲染参考](render.md)。保留原代码的语言/画幅/Metal/MPS等边界；当前脚本分发不等于已经解决跨平台或新歌适配。

## 需要另行准备的内容

未打包歌曲、原始歌词、歌词/音频时序JSON、字体、蒙太奇图、声部、模型权重和生成视频。新歌素材由用户提供或在制作任务中生成；字体从合适授权来源准备并与实际type.ts加载表一致。原片复现可以在明确需要时获取相应上游资产并保留其各自许可。

code/template存在只能证明前置源码齐备；音频/歌词检查、时序生成、字体/贴图加载、浏览器和成片验证仍分别由对应技能完成。禁止因ROOT有app/analysis两个目录便标记整片已就绪。
