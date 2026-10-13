# 环境安装与平台适配

## 原项目与任务模式

分析：Python>=3.12、uv、analysis/pyproject.toml和uv.lock；渲染：Bun、app/bun.lock、Google Chrome、ffmpeg libx264。仅导出已提交作品无需安装Python包/模型；仅修分析无需Bun/Chrome。

安装首先复用当前用户已有工具。使用工具的沙箱/权限机制处理确需写系统目录的步骤，不绕过权限、不反复确认已经授权的普通安装。获取工具版本/平台对应的官方说明后再运行安装；避免把未来更新的CLI假设写死。

## 官方入口（编写时核对：2026-10-06）

- [uv安装](https://docs.astral.sh/uv/getting-started/installation/)；[uv管理Python](https://docs.astral.sh/uv/guides/install-python/)；[锁定与同步](https://docs.astral.sh/uv/concepts/projects/sync/)。可用`uv python install 3.12`安装版本化解释器，按实际依赖选择兼容版本；`uv sync --locked`验证锁无需更新。`--frozen`直接使用既有锁而不检查声明是否变化，适合已经验证的后续运行。
- [Bun安装](https://bun.sh/docs/installation)；[Bun锁定安装](https://bun.sh/docs/pm/cli/install)。使用`bun install --frozen-lockfile`，必要时先下载官方installer到临时文件检查后运行，或复用平台包管理器。
- [Playwright浏览器/Chrome channel](https://playwright.dev/docs/browsers)。playwright-core依赖安装不自动提供Chrome；已有Chrome可通过channel调用。不要未经需要用浏览器全局安装命令替换已有版本。
- [ffmpeg下载](https://ffmpeg.org/download.html)。使用平台实际包管理器提供的含libx264版本；用`ffmpeg -encoders`确认。
- [MLX Whisper官方示例](https://github.com/ml-explore/mlx-examples/tree/main/whisper)。原脚本使用mlx-whisper路径；非兼容平台要有明确替代，不能只安装同名包。

## 分析环境检查

在analysis/：

```bash
uv sync --locked
uv run --frozen python -c "import numpy, scipy, librosa, soundfile, torch, torchaudio, numba, soxr, fontTools; from audio_separator.separator import Separator; print('analysis imports OK')"
```

另检查实际Whisper后端、torch版本与设备。原ctc_emissions.py只选MPS或CPU；CUDA机器安装PyTorch并不会使该脚本自动改用CUDA。

Linux/Windows：原依赖集合含mlx-whisper。先确认该平台依赖能否满足；需要拆分平台依赖或独立venv时保留原锁文件，记录新的依赖声明/锁定结果。替代Whisper后端可以产生兼容的segments[].words JSON，但模型、分词和时间差异必须在后续QA检查。模型下载与导入检查分开。

## 渲染环境检查

在app/：

```bash
bun install --frozen-lockfile
bunx tsc --noEmit -p tsconfig.json
bunx tsc --noEmit -p tsconfig.scripts.json
bunx vite build
```

`render.ts`使用channel:'chrome'和`--use-angle=metal`。Apple路线复用；其他平台配置适用ANGLE后端并实际测GPU。不要仅删除参数后声称硬件加速成功。

新歌场景尚未完成时，可用Playwright独立页面创建WebGL2上下文、浮点目标和像素读回验证基础链；此证据只验证环境。完整场景启动/画面质量留到预览审查，避免用尚未实现的场景作为安装完成的循环依赖。
