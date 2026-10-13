# 工程事实与适配边界

每次场景或共享渲染修改前读取工程docs/ENGINE.md与docs/TREATMENT.md，并遵守实际AGENTS。docs里针对协作作者的文件范围不能被误解为永久禁止已获用户授权的必要时间轴/引擎修改；不明确的范围先做可独立工作再澄清。

## 当前实现

- app/src/main.ts驱动预览和window.__pdoom导出接口。
- app/src/timeline.ts用歌词get/nth和beatAt/timeOfBeat构建窗口，原歌17模块22实例。现有cut对齐不晚于首词的beat，并不保证全部downbeat。
- Scene.init创建资源，render完整覆盖线性HDR目标。默认无状态，以f.t和固定随机种子控制画面；状态场景必须reset/preroll且不能auto采样。
- Layer2D/LineBatch/FSPass/Three几何共同渲染；布局1920x1080逻辑像素，目标scale决定物理输出。
- 使用font/layout/glyphX保持kerning；字体轮廓/粒子/单线字体可以把歌词融入画面。
- 字体、plates、audio、data为本地资产；Vite插件提供audio/data并在build时复制。

## 换歌检查清单

分析路径common.py；main.ts和render.ts的音轨路径；歌词源格式；CTC字符表与pron；N_FRAMES；对齐FIX与阈值；分析速度范围/拍号/第一小节相位/SECTION_BARS；QA图中的固定节拍网格；音高曲线；时间轴歌词查询/nth；场景中歌词索引/词数假设；PDoom等叙事数字；plate列表/代表秒数；片尾重放开场；其他绝对时间/原歌梗。

不要把原歌的1015样本偏移、132BPM、4/4和末日概念当跨作品默认。新歌/新画幅在实际任务工作区适配，保留原素材与可恢复版本；除明确请求外不做整套引擎重构。

## 创意产物

任务concept.md存核心表达；style.md存视觉规范；storyboard.md和scene-specs.json存场景、歌词/节拍锚点、镜头、文字行为、资产和转场。必要时将已实施的规范同步到TREATMENT。保留草案/采用假设/用户已决定的区别，不要新增机械签字阶段。

现有style bible是可参考的完成案例；每首新歌应有自身概念与视觉选择。复用场景引擎和模板不意味着复用原歌叙事。纯器乐/非英语/竖屏需要真正工程适配，入口不得宣称只换MP3即可。
