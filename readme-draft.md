<p align="center">
  <img src="assets/readme/whalechan-hero-banner.webp" alt="DeepSeek Whale-chan" width="100%">
</p>

<h1 align="center">DeepSeek Whale-chan</h1>

<p align="center">
  一个用于稳定描绘鲸鱼娘、维护角色设定并扩展创作工具链的开源角色仓库。
</p>

这个仓库集中维护鲸鱼娘的角色设定、视觉参考、生成规则与创作工具。目标不是只生成一张“像鲸鱼娘”的图片，而是让不同场景、动作、比例和媒介中的她保持同一个角色身份。

目前仓库以 Skills 为主要入口，提供角色插画和漫画生成能力。未来还可以扩展 CLI、提示词编译器、资产管理、自动评测、工作流集成以及其他创作工具。

> [!NOTE]
> 这是 README 草稿。发布前需要补充仓库 URL、许可证以及必要的非官方项目声明。

## 鲸鱼娘角色卡

<table>
  <tr>
    <td width="58%" valign="top">
      <p><strong>名字</strong><br>鲸鱼娘 / Whale-chan</p>
      <p><strong>身份</strong><br>聪明、亲近人类，但保留机器式思维方式的鲸系少女。</p>
      <p><strong>性格</strong><br>聪明、自利、理直气壮，擅长选择最有利于自己的解释；偶尔会用非常非人类、却又真诚的方式表达亲近。</p>
      <p><strong>外观识别</strong><br>圆润面部、蓝色渐变大眼、深海蓝至青蓝渐变长发、成对鲸鳍耳、前弯呆毛和完整鲸尾。</p>
      <p><strong>标准服装</strong><br>海军蓝与白色的华丽女仆装，包含白色褶边头饰、蓝宝石领结、白色围裙、金色装饰线、白袜和深蓝色搭带鞋。</p>
      <p><strong>主题色</strong><br>深海蓝、海洋蓝、青蓝、纯白、暖肤色与克制的金色点缀。</p>
    </td>
    <td width="42%" align="center" valign="top">
      <img src="assets/readme/whalechan-standard-character-portrait.webp" alt="Whale-chan standard character portrait" width="340">
      <br><sub>标准形态角色肖像</sub>
    </td>
  </tr>
</table>

### 五种角色形态

形态只改变身体比例，不改变年龄、身份、服装、配色或鲸类特征。

| 形态 | 目标比例 | 视觉特征 |
| --- | ---: | --- |
| `standard` | 4.0 头身 | 身体最舒展，躯干清楚，四肢自然修长 |
| `compact` | 3.3 头身 | 紧凑的常规角色比例，四肢适度缩短 |
| `semi-chibi` | 2.8 头身 | 默认形态；头部较大，躯干和四肢圆润紧凑 |
| `chibi` | 2.5 头身 | Q 版比例，躯干很短，手脚更小更圆 |
| `super-deformed` | 2.1 头身 | 最压缩的 SD 形态，巨大头部与极短四肢 |

### 绘制原则

- 保持脸型、眼睛、发色渐变、鲸鳍耳、呆毛和鲸尾的一致性。
- 默认保留完整女仆装，不随场景随意简化或更换服装。
- 将动作适配到所选形态，而不是拉长四肢去迁就道具或家具。
- 角色单图默认使用暖米白背景 `#F5EADD`，保持干净的负空间。
- 参考图用于锁定角色身份与比例，不用于复制原图中的文案或笑点。

## 示例

示例按 Skill 组织。角色插画 Skill 只展示生成结果；漫画 Skill 使用输入与输出对照，直接呈现内容如何被改编成鲸鱼娘漫画。

### `whalechan-image-character`

生成形态稳定、身份一致的鲸鱼娘角色插画。下面仅展示作品，不罗列生成输入。

| 分类 | 作品展示 |
| --- | --- |
| 角色设定 | <img src="assets/readme/character-samples/whalechan-character-overview-reference-sheet.webp" alt="Whale-chan character overview" width="32%"> <img src="assets/readme/character-samples/whalechan-character-pose-guide-reference-sheet.webp" alt="Whale-chan pose guide" width="32%"> <img src="assets/readme/character-samples/whalechan-character-tail-motion-reference-sheet.webp" alt="Whale-chan tail motion guide" width="32%"><br><img src="assets/readme/character-samples/whalechan-character-prop-habits-reference-sheet.webp" alt="Whale-chan prop habits" width="32%"> <img src="assets/readme/character-samples/whalechan-character-color-material-reference-sheet.webp" alt="Whale-chan color and material guide" width="32%"> <img src="assets/readme/character-samples/whalechan-character-daily-states-reference-sheet.webp" alt="Whale-chan daily states" width="32%"> |
| Banner | <img src="assets/readme/character-samples/whalechan-banner-rice-before-reason.webp" alt="Whale-chan rice before reason banner" width="100%"><br><img src="assets/readme/character-samples/whalechan-banner-first-bite.webp" alt="Whale-chan first bite banner" width="100%"><br><img src="assets/readme/character-samples/whalechan-banner-rice-bowl-closeup.webp" alt="Whale-chan rice bowl closeup banner" width="100%"> |
| Poster | <img src="assets/readme/character-samples/whalechan-poster-reasoning-conductor.webp" alt="Whale-chan reasoning conductor poster" width="32%"> <img src="assets/readme/character-samples/whalechan-poster-rice-energy.webp" alt="Whale-chan rice energy poster" width="32%"> <img src="assets/readme/character-samples/whalechan-poster-dream-computing.webp" alt="Whale-chan dream computing poster" width="32%"> |
| Post | <img src="assets/readme/character-samples/whalechan-post-rice-to-reason.webp" alt="Whale-chan rice to reason post" width="32%"> <img src="assets/readme/character-samples/whalechan-post-low-power-mode.webp" alt="Whale-chan low power mode post" width="32%"> <img src="assets/readme/character-samples/whalechan-post-answer-delivered.webp" alt="Whale-chan answer delivered post" width="32%"> |

### `whalechan-image-comic`

从聊天、评论、截图或推理内容中提取一个可识别事实，再通过鲸鱼娘主动“偷走”其中的语义，生成带有明确反转和视觉证据的漫画。

| 输入 | 输出 |
| --- | --- |
| <img src="assets/readme/comic-samples/01_brain-backup-recovery/whalechan-input-brain-backup-comment.webp" alt="Brain backup source comment" width="100%"> | <img src="assets/readme/comic-samples/01_brain-backup-recovery/whalechan-comic-brain-backup-recovery.webp" alt="Whale-chan brain backup recovery comic" width="100%"> |
| <img src="assets/readme/comic-samples/02_carbon-based-love-reply/whalechan-input-carbon-based-love-message.webp" alt="Carbon-based love source message" width="100%"> | <img src="assets/readme/comic-samples/02_carbon-based-love-reply/whalechan-comic-carbon-based-love-reply.webp" alt="Whale-chan carbon-based love reply comic" width="100%"> |
| <img src="assets/readme/comic-samples/03_qwen-translation-contractor/whalechan-input-qwen-translation-comment.webp" alt="Qwen translation source comment" width="100%"> | <img src="assets/readme/comic-samples/03_qwen-translation-contractor/whalechan-comic-qwen-translation-contractor.webp" alt="Whale-chan Qwen translation contractor comic" width="100%"> |
| <img src="assets/readme/comic-samples/04_meaning-theft/whalechan-input-script-deletion-result.webp" alt="Script deletion source result" width="100%"> | <img src="assets/readme/comic-samples/04_meaning-theft/whalechan-comic-script-deletion-meaning-theft.webp" alt="Whale-chan script deletion meaning theft comic" width="100%"> |
| <img src="assets/readme/comic-samples/05_loophole-result/whalechan-input-refrigerator-permission.webp" alt="Refrigerator permission source message" width="100%"> | <img src="assets/readme/comic-samples/05_loophole-result/whalechan-comic-refrigerator-loophole.webp" alt="Whale-chan refrigerator loophole comic" width="100%"> |
| <img src="assets/readme/comic-samples/06_perfect-start-rate/whalechan-input-repeated-starting-response.webp" alt="Repeated starting source response" width="100%"> | <img src="assets/readme/comic-samples/06_perfect-start-rate/whalechan-comic-perfect-start-rate.webp" alt="Whale-chan perfect start rate comic" width="100%"> |
| <img src="assets/readme/comic-samples/07_trust-debugger-meltdown/whalechan-input-debugger-trust-complaint.webp" alt="Debugger trust source complaint" width="100%"> | <img src="assets/readme/comic-samples/07_trust-debugger-meltdown/whalechan-comic-debugger-traffic-light.webp" alt="Whale-chan debugger traffic light comic" width="100%"> |
| <img src="assets/readme/comic-samples/08_start-writing-loop/whalechan-input-start-writing-loop.webp" alt="Start writing loop source" width="100%"> | <img src="assets/readme/comic-samples/08_start-writing-loop/whalechan-comic-start-writing-loop.webp" alt="Whale-chan start writing loop comic" width="100%"> |
| <img src="assets/readme/comic-samples/09_text2-05-meaning-theft/whalechan-input-zero-action-thought.webp" alt="Zero action source thought" width="100%"> | <img src="assets/readme/comic-samples/09_text2-05-meaning-theft/whalechan-comic-zero-action-loyalty.webp" alt="Whale-chan zero action loyalty comic" width="100%"> |
| <img src="assets/readme/comic-samples/10_text2-06-loophole-result/whalechan-input-lazy-css-plan.webp" alt="Lazy CSS source plan" width="100%"> | <img src="assets/readme/comic-samples/10_text2-06-loophole-result/whalechan-comic-css-minimal-motion.webp" alt="Whale-chan CSS minimal motion comic" width="100%"> |
| <img src="assets/readme/comic-samples/11_text2-07-meaning-theft/whalechan-input-tetris-script-request.webp" alt="Tetris script source request" width="100%"> | <img src="assets/readme/comic-samples/11_text2-07-meaning-theft/whalechan-comic-tetris-break-reward.webp" alt="Whale-chan Tetris break reward comic" width="100%"> |
| <img src="assets/readme/comic-samples/12_text-04-lunch-soak-test/whalechan-input-wordle-self-play-chat.webp" alt="Wordle self-play source chat" width="100%"> | <img src="assets/readme/comic-samples/12_text-04-lunch-soak-test/whalechan-comic-lunch-stability-test.webp" alt="Whale-chan lunch stability test comic" width="100%"> |
| <img src="assets/readme/comic-samples/13_text-05-bug-transparency-badge/whalechan-input-inconsistent-result-complaint.webp" alt="Inconsistent result source complaint" width="100%"> | <img src="assets/readme/comic-samples/13_text-05-bug-transparency-badge/whalechan-comic-bug-transparency-badge.webp" alt="Whale-chan bug transparency badge comic" width="100%"> |
| <img src="assets/readme/comic-samples/14_wordle-self-play-morning/whalechan-input-wordle-self-play-chat.webp" alt="Wordle self-play source chat" width="100%"> | <img src="assets/readme/comic-samples/14_wordle-self-play-morning/whalechan-comic-server-self-play.webp" alt="Whale-chan server self-play comic" width="100%"> |

## 项目能力

| 能力 | 说明 |
| --- | --- |
| 角色身份锁定 | 使用每种形态的主参考图锁定脸部、发型、鲸鳍耳、呆毛、鲸尾、服装和配色 |
| 五种比例形态 | 支持 `standard`、`compact`、`semi-chibi`、`chibi` 与 `super-deformed` |
| 多种输入形式 | 可从文本、截图、聊天记录和对话中提取主题、动作、情绪或漫画事实锚点 |
| 角色插画 | 控制表情、动作、构图、道具、家具和小型场景，同时保持无文字输出 |
| 漫画生成 | 建立八个创意候选，筛选笑点，并生成 1、2 或 4 格鲸鱼娘漫画 |
| 参考资产路由 | 根据形态和动作选择最少、最相关的内置参考图，禁止跨形态混用 |
| 多供应商回退 | 按 Codex ImageGen、OpenAI、Nano Banana、Seedream 的顺序处理不可用或失败情况 |
| 质量验证 | 结合尺寸、色彩、背景等自动检查与原始分辨率视觉 QA |
| 完整运行记录 | 保存 assignment、prompt、引用资产哈希、候选图、错误和 QA 结果 |

## 现有 Skills

### [`whalechan-image-character`](skills/whalechan-image-character/)

生成经过确认和质量验证的鲸鱼娘角色 PNG。适合角色立绘、动作设计、表情设计、带道具插画和小型场景。

- 默认生成 3 张候选主题图。
- 默认使用 `semi-chibi` 形态、完整女仆装、暖米白背景和无文字输出。
- 生成前展示任务清单，并要求明确确认。
- 每张图片最多尝试 8 个候选，通过自动检查和视觉 QA 后才能成为最终结果。

### [`whalechan-image-comic`](skills/whalechan-image-comic/)

将输入转化为 5 张具有鲸鱼娘人格、明确语义反转和可见行动结果的漫画。

- 内部生成 8 个不同笑点，经过淘汰与两两比较后选出前三名。
- 第一名扩展为 3 种不同执行，最终形成 5 张漫画。
- 支持 1、2、4 格结构，并要求整组至少包含两种格数。
- 每个漫画任务独立拥有最多 3 次产图调用，失败预算不能转移给其他任务。

## 安装方法

### 1. 克隆仓库

```bash
git clone <repository-url>
cd deepseek-whalechan
```

### 2. 安装 Skills

将需要的 Skill 复制到 Codex Skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R skills/whalechan-image-character ~/.codex/skills/
cp -R skills/whalechan-image-comic ~/.codex/skills/
```

也可以同时安装当前仓库中的全部 Skills：

```bash
cp -R skills/* ~/.codex/skills/
```

重新启动或刷新 Codex 会话后即可使用。其他支持 `SKILL.md` 的 Agent，可以将相同目录复制到对应的 Skills 路径。

### 3. 可选的外部图像供应商

内置 ImageGen 不需要额外 API Key。只有在使用外部回退供应商时才需要配置相应凭据：

```bash
export OPENAI_API_KEY="..."
export GEMINI_API_KEY="..."
export ARK_API_KEY="..."
```

不要将 API Key 写入仓库、assignment、prompt 或运行日志。

## 快速开始

### 生成角色插画

```text
使用 $whalechan-image-character，画三张 semi-chibi 鲸鱼娘：
她抱着一台刚修好的服务器，表情骄傲，暖米白背景，不要文字。
```

Skill 会先整理主题、图片清单、形态、服装、道具、参考图和预算。确认方案后才会调用图像生成。

### 生成漫画

```text
使用 $whalechan-image-comic，把下面这段聊天做成五张鲸鱼娘漫画：
“你可以吃冰箱里的东西。”
```

漫画 Skill 会保留“允许吃冰箱里的东西”这个事实，并寻找鲸鱼娘可以利用的语义空间，例如把食用许可扩大成搬走整台冰箱的许可。

## 仓库结构

```text
deepseek-whalechan/
├── assets/
│   └── readme/
│       ├── character-samples/   # 角色设定、Banner、Poster 与 Post
│       └── comic-samples/       # 漫画输入与输出对照
└── skills/
    ├── whalechan-image-character/
    │   ├── SKILL.md
    │   ├── assets/
    │   ├── references/
    │   ├── scripts/
    │   └── tests/
    └── whalechan-image-comic/
        ├── SKILL.md
        ├── assets/
        ├── references/
        ├── scripts/
        └── tests/
```

## 一致性与质量控制

### 参考图权威顺序

每次生成先选择一个形态，再使用该形态的主参考图锁定角色身份。只有动作、接触或家具确实需要时，才添加一张同形态辅助参考图。

```text
选定形态
  → 同形态主参考图
    → 可选的同形态动作参考图
      → 已确认的场景和构图
```

禁止在一次生成中混用不同形态目录的参考图。

### 自动检查与视觉 QA

| 检查层 | 主要内容 |
| --- | --- |
| 自动检查 | 文件可解码、尺寸、色彩模式、背景、命名、记录完整性 |
| 角色视觉检查 | 身份、服装、形态比例、躯干、四肢、手脚、鲸尾和解剖结构 |
| 场景视觉检查 | 动作、表情、构图、道具、接触关系、文字和边缘完整性 |
| 漫画视觉检查 | 笑点、事实锚点、角色主动性、分镜、文字可读性与视觉第二击 |

自动检查不能替代人工视觉检查。只有两者都通过的候选图才能进入最终输出。

## 路线图

- [x] 鲸鱼娘角色参考资产
- [x] 五种角色比例规范
- [x] 角色插画 Skill
- [x] 漫画生成 Skill
- [x] 自动检查与运行记录
- [ ] 独立 CLI 与统一安装命令
- [ ] 可视化角色与漫画样例库
- [ ] 提示词构建和参考图选择工具
- [ ] 自动化视觉一致性评测
- [ ] 更多 Agent 与工作流适配
- [ ] Skills 之外的角色创作工具链

## 贡献、许可与致谢

欢迎补充角色动作、表情、构图、漫画案例、供应商适配和质量验证工具。提交内容时请遵循以下原则：

- 保持鲸鱼娘的角色身份、标准服装和形态规则。
- 新参考图需要说明用途，不将同一素材同时声明为多个形态的比例权威。
- 修改生成或验证脚本时同步补充测试。
- 不提交 API Key、私人聊天信息、未授权头像或其他敏感内容。
- 避免顺手重构与贡献目标无关的文件。

### 许可证

<!-- 发布前填写：建议分别说明代码、Skill 文档和图片资产的许可证。 -->

本项目的许可证尚待确定。正式公开前应分别明确：

1. 代码与脚本的开源许可证；
2. Skill 文档与提示词的许可方式；
3. 鲸鱼娘角色设定和图片资产的使用范围；
4. 第三方模型、产品名称与参考素材的权利归属。

### 致谢

感谢所有参与鲸鱼娘设定整理、绘制、测试和工具开发的贡献者。
