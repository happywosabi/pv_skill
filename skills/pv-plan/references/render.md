# 渲染、审片与交付

`render.ts`、main/engine/scene代码与Bun/Vite配置已包含在总入口的工程模板中，详见[pdoom脚本说明](pdoom-scripts.md)。先复制到实际ROOT；仍需准备歌曲、正式JSON、实际字体/回放资产及浏览器环境，不能仅运行资源目录中的render.ts就声称成片可用。

命令从app/执行，输出放任务目录。下面open/t=2,6,8仅适用于原作品；换歌用真实timeline窗口和有效时间。

## 预览与审查

```bash
bunx vite
bun scripts/render.ts stills --t 2,6,8 --only open --out ../out/pv/JOB/open
bun scripts/render.ts video --from 1 --to 8 --only open --samples 4 --shutter 0.2 --preset veryfast --out ../out/pv/JOB/open.mp4
bun scripts/render.ts sheet --cuts --out ../out/pv/JOB/cuts.png
bun scripts/render.ts perf --from 20 --to 25 --samples 4 --scale 2
```

--only用timeline实例id，例如hook1/prompt1，不是文件名hook/prompt。sheet模式代码使用P.still(t)，当前不会把--samples/--shutter用于拼图；它适合构图/边界检查，运动模糊必须用真正stills/video验证。

查看实际图像/视频，不能只依据返回路径。检查歌词每词起止/长音、安全区、字体kerning、镜头和转场；检查1080p与目标scale。SCENE ERRORS/浏览器日志必须诊断；当前代码会捕获一些错误并绘制红色占位，因此进程退出0不证明画面正确。

## 源码固定与采样

导出期间关闭HMR：`PDOOM_NO_HMR=1 bunx vite --port 5190`，render命令加`--url http://localhost:5190`；脚本没有可达服务器时自动起的私服已关闭HMR。现有开发服务器可达时会被直接复用，须先检查其HMR设置。

布局为1920x1080逻辑像素，--scale 2输出3840x2160。部分中间缓冲/后期故意低分辨率，不能声称每个层都原生4K。变画幅要实际工程适配。

auto采样按32x32逻辑tile细化4/12/36/108/324；状态场景不能auto。shutter是帧时长比例，0.2为1/5帧时长。HUD/颗粒/后期参数的处理与场景子帧并不完全相同。预览与成片共享代码，采样参数不同则画质不同。

## 蒙太奇

原片尾需要14张fig JPEG；plates.json选择代表秒数，render.ts figs决定编号，outro决定消费者顺序。更新场景/数据后核对这些列表/时间并重新运行plates。新作品未使用此设计时写不适用说明，不强加蒙太奇。

## 正式导出

```bash
bun scripts/render.ts plates
bun scripts/render.ts video --samples auto --shutter 0.2 --out ../out/pv/JOB/final.mp4
bun scripts/render.ts video --scale 2 --samples auto --shutter 0.2 --x264 aq-mode=3:rc-lookahead=30 --out ../out/pv/JOB/final-4k.mp4
```

默认1920x1080/60fps、x264 CRF16/preset slow/tune grain、AAC320k、yuv420p与faststart；保留BT.709矩阵及色彩标签。两Chrome/8帧chunk和1GB内存/20GBspool是默认，可按实测资源调整；4K像素读回与颗粒编码很重，原作者机器成绩不能作为本机估算。

## 成片验收

```bash
ffprobe -v error -show_streams -show_format -of json FINAL.mp4
ffmpeg -v error -i FINAL.mp4 -map 0:v:0 -map '0:a?' -f null -
```

记录实际退出码/日志，再观看场景与疑难段。视频帧数取整会造成不到一帧的长度差，应按fps解释，不机械要求精确等于音频秒数。确认音画同步、所有场景、边界、片尾与循环；未能观看则诚实记录未验证，不能把文件属性检查当审片完成。

交付本地文件与制作记录，不自动上传平台、不自动发送消息。歌曲/歌词/字体的来源与许可独立于代码MIT；保留credits，不随交付清空模型缓存或提交大渲染。
