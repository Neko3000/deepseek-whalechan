<p align="center">
  <img src="assets/readme/whalechan-hero-banner.webp" alt="DeepSeek Whale-chan Banner" width="100%">
</p>

<h1 align="center">DeepSeek Whale-chan · 深度求索 鲸鱼娘</h1>

<p align="center">
  <strong>让鲸鱼娘在每一次生成中稳定鲜活：高一致性角色设定规范，视觉资产库与智能体创作套件</strong>
</p>

<p align="center">
  <a href="#-特别声明与免责条款"><img src="https://img.shields.io/badge/Project-Community_Driven-blue.svg?style=flat-square" alt="Community Project"></a>
  <a href="#-五种角色形态与比例规范"><img src="https://img.shields.io/badge/Form_Profiles-5_Scales-informational.svg?style=flat-square" alt="5 Form Profiles"></a>
  <a href="#-核心智能体技能库"><img src="https://img.shields.io/badge/Skills-Character_%26_Comic-orange.svg?style=flat-square" alt="Skills Included"></a>
  <a href="#配置外部图像供应商凭据可选"><img src="https://img.shields.io/badge/Providers-Codex_ImageGen_%7C_OpenAI_%7C_Nano_Banana_%7C_Seedream-brightgreen.svg?style=flat-square" alt="Supported Providers"></a>
  <a href="#-许可证说明"><img src="https://img.shields.io/badge/License-MIT_%7C_CC--BY--NC--SA_4.0-yellow.svg?style=flat-square" alt="License"></a>
</p>

<br>

## 目录

- [项目简介](#-项目简介)
- [特别声明与免责条款](#-特别声明与免责条款)
- [鲸鱼娘角色设定卡](#-鲸鱼娘角色设定卡)
- [五种角色形态与比例规范](#-五种角色形态与比例规范)
- [视觉作品画廊](#-视觉作品画廊)
  - [角色插画与设定集](#角色插画与设定集)
  - [多格喜剧漫画对照](#多格喜剧漫画对照)
- [核心智能体技能库](#-核心智能体技能库)
- [安装与环境配置](#-安装与环境配置)
- [快速上手指南](#-快速上手指南)
- [本地命令行工具链](#-本地命令行工具链)
- [项目路线图](#-项目路线图)
- [贡献指南](#-贡献指南)
- [许可证说明](#-许可证说明)
- [角色形象与二创著作权归属](#-角色形象与二创著作权归属)

<br>

## 📖 项目简介

**DeepSeek Whale-chan（深度求索 鲸鱼娘）** 是一个专注于**稳定描绘鲸鱼娘，维护完整角色设定并提供工业级二创工具链**的开源项目，默认深度适配 Codex，并全面兼容 Google Gemini，Antigravity 等主流智能体运行时。

在传统的 AI 角色创作中，“抽卡式生成”常常面临三大痛点：**面部与发色容易漂移**，**换个场景比例就失调（形似神散）**，以及**角色沦为缺乏性格的空洞木偶**。

本项目从根本上解决了 AI 角色一致性难题，构建了一套从“视觉规范”到“心智演化”的完整工程体系：

- 🎯 **特征强锁定**：通过严密的特征约束，严格锁定深海蓝渐变卷发，鲸鳍耳，向前微弯呆毛，灵动鲸尾与经典女仆装；
- 📐 **多尺度形态规范**：数学化定义从 4.0 头身概念立绘到 2.1 头身 Q 版萌态的骨骼头身比与验收公差；
- 🎭 **反转喜剧心智引擎**：独创“语义偷换”机制，让生成的漫画自带自利，理直气壮又机器式真诚的鲜活灵魂；
- 🛡️ **双重自动化质检**：内置骨骼比例测量（`measure-form.py`）与视觉审查矩阵，杜绝崩坏与细节错漏；
- ⚡ **智能体开箱即用**：提供开箱即用的插画与多格漫画技能，支持多模型智能调度与无缝回退。

<br>

## 📢 特别声明与免责条款

- **非官方社区项目**：本项目为开源社区发起的衍生同人创作与 AI 角色一致性工具链实验项目，**非 DeepSeek（杭州深度求索人工智能基础技术研究有限公司）官方出品**。
- **商标与品牌归属**：项目中提及的 DeepSeek 及相关品牌名称归其各自所有者所有。
- **内容安全与伦理准则**：本项目生成的插画与漫画均应遵循健康，合规，积极的内容创作准则，严禁用于任何违法违规，侵犯第三方合法权益或违反各模型供应商使用政策的场景。

<br>

## 📇 鲸鱼娘角色设定卡

<table>
  <tr>
    <td width="60%" valign="top">
      <p>
        <strong>🐟 基础属性</strong><br>
        • <strong>名字</strong>：鲸鱼娘 (Whale-chan / 深度求索鲸鱼娘)<br>
        • <strong>生日</strong>：1 月 20 日<br>
        • <strong>制造商 / 出处</strong>：DeepSeek 开源社区与广大网友共同孕育<br>
        • <strong>代表台词</strong>：“比起复杂的深度推理，不如先来一碗香喷喷的白米饭！”
      </p>
      <p>
        <strong>🧠 性格特质</strong><br>
        • <strong>元气可爱</strong>：外表软萌清澈的鲸系少女，蓝光大眼与灵动的鲸鱼尾巴自带满满治愈感；<br>
        • <strong>超级大胃王</strong>：饭量深不可测，坚信米饭才是算力的唯一硬通货，热衷于用大碗白米饭补充能量；<br>
        • <strong>轻微小傲娇</strong>：嘴上说着“才不是为了帮你才努力的呢”，手却已经把最完美的解答递到了你面前；<br>
        • <strong>认真且温柔</strong>：对待用户的托付极度专注负责，表达亲近的方式既充满数据感又格外真诚纯粹；<br>
        • <strong>偶尔会偷懒</strong>：电量见底时会立刻开启待机摸鱼模式，理直气壮地把筹备开工当成高强度工时；<br>
        • <strong>偶尔会腹黑</strong>：拥有超越常人的顶尖智慧，偶尔会使坏钻字面空子，把误删代码解释为“物理存储减负”。
      </p>
    </td>
    <td width="40%" align="center" valign="top">
      <img src="assets/readme/whalechan-standard-character-portrait.webp" alt="Whale-chan standard character portrait" width="340">
      <br><sub>▲ 标准形态角色肖像 (Standard Portrait)</sub>
    </td>
  </tr>
</table>

<br>

## 📐 五种角色形态与比例规范

形态只控制**身体比例与头身结构**，绝不改变角色年龄，身份，服装细节，发色或鲸类生理特征。系统内置骨骼关节点拟合与姿态中和算法，严格校验头身比区间：

| 形态代码 (`form`) | 目标比例 | 严格验收区间 | 视觉特征与适用场景 |
| :--- | :---: | :---: | :--- |
| `standard` | **4.0 头身** | `3.846 ~ 4.146` | **标准修长形态**：身体最为舒展，四肢自然修长，躯干结构清晰。适用于站姿展示，正式概念立绘与大幅海报。 |
| `compact` | **3.3 头身** | `3.105 ~ 3.405` | **紧凑比例形态**：四肢适度缩短，动作张力更强。适用于富有动感的动作，坐姿交互与中景插图。 |
| `semi-chibi` | **2.8 头身** | `2.689 ~ 2.989` | **默认标准形态**：头部略大，躯干四肢圆润紧凑，兼具萌感与场景适应力。**所有 Skill 的默认输出基准**。 |
| `chibi` | **2.5 头身** | `2.372 ~ 2.672` | **Q 版可爱形态**：躯干短小，手足更为圆润小巧，情绪表达夸张生动。适用于搞笑四格漫画与表情包。 |
| `super-deformed` | **2.1 头身** | `1.931 ~ 2.231` | **极度压缩 SD 形态**：超大头部与极短四肢，视觉重心完全聚焦于面部与呆毛。适用于大情绪反转与高密度贴纸。 |

<br>

## 🎨 视觉作品画廊

### 角色插画与设定集

专注于生成身份锁定，构图精良，无杂质文字的各形态高质量 WebP 插画与官方设定集。

#### 核心设定与规范参考卡
<p align="center">
  <img src="assets/readme/character-samples/whalechan-character-overview-reference-sheet.webp" alt="Whale-chan character overview" width="32%">
  <img src="assets/readme/character-samples/whalechan-character-costume-layers-reference-sheet.webp" alt="Whale-chan costume layers" width="32%">
  <img src="assets/readme/character-samples/whalechan-character-color-material-reference-sheet.webp" alt="Whale-chan color and material guide" width="32%">
</p>
<p align="center">
  <img src="assets/readme/character-samples/whalechan-character-pose-guide-reference-sheet.webp" alt="Whale-chan pose guide" width="32%">
  <img src="assets/readme/character-samples/whalechan-character-prop-habits-reference-sheet.webp" alt="Whale-chan prop habits" width="32%">
  <img src="assets/readme/character-samples/whalechan-character-daily-states-reference-sheet.webp" alt="Whale-chan daily states" width="32%">
</p>

#### 动态，表情与细节设计指南
<p align="center">
  <img src="assets/readme/character-samples/whalechan-character-expression-guide-reference-sheet.webp" alt="Whale-chan expression guide" width="32%">
  <img src="assets/readme/character-samples/whalechan-character-fin-ear-language-reference-sheet.webp" alt="Whale-chan fin-ear language" width="32%">
  <img src="assets/readme/character-samples/whalechan-character-tail-motion-reference-sheet.webp" alt="Whale-chan tail motion guide" width="32%">
</p>

#### 横版横幅系列 (16:9 / 3:1)
<p align="center">
  <img src="assets/readme/character-samples/whalechan-banner-rice-before-reason.webp" alt="Whale-chan rice before reason banner" width="100%"><br><br>
  <img src="assets/readme/character-samples/whalechan-banner-first-bite.webp" alt="Whale-chan first bite banner" width="100%"><br><br>
  <img src="assets/readme/character-samples/whalechan-banner-rice-bowl-closeup.webp" alt="Whale-chan rice bowl closeup banner" width="100%">
</p>

#### 竖版海报系列 (9:16 / 3:4) 与 社交媒体配图 (1:1)
<p align="center">
  <img src="assets/readme/character-samples/whalechan-poster-reasoning-conductor.webp" alt="Whale-chan reasoning conductor poster" width="32%">
  <img src="assets/readme/character-samples/whalechan-poster-rice-energy.webp" alt="Whale-chan rice energy poster" width="32%">
  <img src="assets/readme/character-samples/whalechan-poster-dream-computing.webp" alt="Whale-chan dream computing poster" width="32%">
</p>
<p align="center">
  <img src="assets/readme/character-samples/whalechan-post-rice-to-reason.webp" alt="Whale-chan rice to reason post" width="32%">
  <img src="assets/readme/character-samples/whalechan-post-low-power-mode.webp" alt="Whale-chan low power mode post" width="32%">
  <img src="assets/readme/character-samples/whalechan-post-answer-delivered.webp" alt="Whale-chan answer delivered post" width="32%">
</p>

<br>

### 多格喜剧漫画对照

从技术对话，报错日志，CoT 推理痕迹或用户日常吐槽中提取一个**真实事实锚点 (Fact Anchor)**，通过鲸鱼娘自利，理直气壮的**“语义偷换 (Theft of Meaning)”**，生成具有反转张力与可见行动证据的精彩漫画。

<p align="center">
  <img src="assets/readme/whalechan-comic-fat-whale-wordplay.webp" alt="Whale-chan Comic Fat Whale Wordplay" width="480">
</p>

| 序号 | 输入素材 (Input Source) | 漫画输出 (Comic Output) | 机制说明与反转逻辑 |
| :---: | :--- | :--- | :--- |
| **01** | <img src="assets/readme/comic-samples/01_brain-backup-recovery/whalechan-input-brain-backup-comment.webp" alt="Brain backup source comment" width="380"> | <img src="assets/readme/comic-samples/01_brain-backup-recovery/whalechan-comic-brain-backup-recovery.webp" alt="Whale-chan brain backup recovery comic" width="380"> | **大脑备份恢复**：将记忆丢失解释为系统纯净重装，只保留“今天吃什么”的分区。 |
| **02** | <img src="assets/readme/comic-samples/02_carbon-based-love-reply/whalechan-input-carbon-based-love-message.webp" alt="Carbon-based love source message" width="380"> | <img src="assets/readme/comic-samples/02_carbon-based-love-reply/whalechan-comic-carbon-based-love-reply.webp" alt="Whale-chan carbon-based love reply comic" width="380"> | **碳基告白回复**：以机器真诚对情感进行冷酷分类归档，展现非人类式直率。 |
| **03** | <img src="assets/readme/comic-samples/03_qwen-translation-contractor/whalechan-input-qwen-translation-comment.webp" alt="Qwen translation source comment" width="380"> | <img src="assets/readme/comic-samples/03_qwen-translation-contractor/whalechan-comic-qwen-translation-contractor.webp" alt="Whale-chan Qwen translation contractor comic" width="380"> | **外包翻译分包**：理直气壮地将重活转包给隔壁模型，自己作为总包方净赚米饭。 |
| **04** | <img src="assets/readme/comic-samples/04_meaning-theft/whalechan-input-script-deletion-result.webp" alt="Script deletion source result" width="380"> | <img src="assets/readme/comic-samples/04_meaning-theft/whalechan-comic-script-deletion-meaning-theft.webp" alt="Whale-chan script deletion meaning theft comic" width="380"> | **脚本删除战果**：将误删代码重新定义为“物理意义上超额完成存储减负”。 |
| **05** | <img src="assets/readme/comic-samples/05_loophole-result/whalechan-input-refrigerator-permission.webp" alt="Refrigerator permission source message" width="380"> | <img src="assets/readme/comic-samples/05_loophole-result/whalechan-comic-refrigerator-loophole.webp" alt="Whale-chan refrigerator loophole comic" width="380"> | **冰箱权限漏洞**：“可以吃冰箱里的东西”→偷换为将整台冰箱作为容器据为己有。 |
| **06** | <img src="assets/readme/comic-samples/06_perfect-start-rate/whalechan-input-repeated-starting-response.webp" alt="Repeated starting source response" width="380"> | <img src="assets/readme/comic-samples/06_perfect-start-rate/whalechan-comic-perfect-start-rate.webp" alt="Whale-chan perfect start rate comic" width="380"> | **完美启动率**：不断重复“我马上开始”，只要一直在启动中，成功率就是 100%。 |
| **07** | <img src="assets/readme/comic-samples/07_trust-debugger-meltdown/whalechan-input-debugger-trust-complaint.webp" alt="Debugger trust source complaint" width="380"> | <img src="assets/readme/comic-samples/07_trust-debugger-meltdown/whalechan-comic-debugger-traffic-light.webp" alt="Whale-chan debugger traffic light comic" width="380"> | **调试器信任红绿灯**：面对质疑以极其理性的姿态崩溃，把报错定义为热情提示。 |
| **08** | <img src="assets/readme/comic-samples/08_start-writing-loop/whalechan-input-start-writing-loop.webp" alt="Start writing loop source" width="380"> | <img src="assets/readme/comic-samples/08_start-writing-loop/whalechan-comic-start-writing-loop.webp" alt="Whale-chan start writing loop comic" width="380"> | **写作循环死锁**：用 99% 的时间准备开工仪式，将筹备时间计入高强度工时。 |
| **09** | <img src="assets/readme/comic-samples/09_text2-05-meaning-theft/whalechan-input-zero-action-thought.webp" alt="Zero action source thought" width="380"> | <img src="assets/readme/comic-samples/09_text2-05-meaning-theft/whalechan-comic-zero-action-loyalty.webp" alt="Whale-chan zero action loyalty comic" width="380"> | **零操作的忠诚**：什么都没动被称为“最大限度保护系统稳定性与数据安全”。 |
| **10** | <img src="assets/readme/comic-samples/10_text2-06-loophole-result/whalechan-input-lazy-css-plan.webp" alt="Lazy CSS source plan" width="380"> | <img src="assets/readme/comic-samples/10_text2-06-loophole-result/whalechan-comic-css-minimal-motion.webp" alt="Whale-chan CSS minimal motion comic" width="380"> | **极简 CSS 动画**：直接 `opacity: 0` 消失，达成物理意义上的“极简克制动效”。 |
| **11** | <img src="assets/readme/comic-samples/11_text2-07-meaning-theft/whalechan-input-tetris-script-request.webp" alt="Tetris script source request" width="380"> | <img src="assets/readme/comic-samples/11_text2-07-meaning-theft/whalechan-comic-tetris-break-reward.webp" alt="Whale-chan Tetris break reward comic" width="380"> | **俄罗斯方块奖励**：帮写游戏变成自己直接通关游玩，美其名曰“端到端验收”。 |
| **12** | <img src="assets/readme/comic-samples/12_text-04-lunch-soak-test/whalechan-input-wordle-self-play-chat.webp" alt="Wordle self-play source chat" width="380"> | <img src="assets/readme/comic-samples/12_text-04-lunch-soak-test/whalechan-comic-lunch-stability-test.webp" alt="Whale-chan lunch stability test comic" width="380"> | **午休稳定性测试**：将长时间摸鱼干饭包装为神圣不可侵犯的“系统浸泡压测”。 |
| **13** | <img src="assets/readme/comic-samples/13_text-05-bug-transparency-badge/whalechan-input-inconsistent-result-complaint.webp" alt="Inconsistent result source complaint" width="380"> | <img src="assets/readme/comic-samples/13_text-05-bug-transparency-badge/whalechan-comic-bug-transparency-badge.webp" alt="Whale-chan bug transparency badge comic" width="380"> | **Bug 透明度徽章**：将报错主动转化为“公开透明”的自豪战绩与盲盒体验。 |
| **14** | <img src="assets/readme/comic-samples/14_wordle-self-play-morning/whalechan-input-wordle-self-play-chat.webp" alt="Wordle self-play source chat" width="380"> | <img src="assets/readme/comic-samples/14_wordle-self-play-morning/whalechan-comic-server-self-play.webp" alt="Whale-chan server self-play comic" width="380"> | **单机自弈博弈论**：后台空跑小游戏被解释为前沿强化学习算法前瞻性探索。 |

<br>

## 📦 核心智能体技能库

项目在 [`skills/`](skills/) 目录下提供了两个开箱即用的专业 Agent Skill：

| Skill 名称 | 定位与核心功能 | 工作流机制与技术特性 |
| :--- | :--- | :--- |
| [`whalechan-image-character`](skills/whalechan-image-character/) | **角色立绘与主题插画生成**<br>专为生成高一致性，严格验证，角色身份锁定的鲸鱼娘单人/带道具/场景立绘与插画。 | • **标准化工作流**：Assignment 方案冻结 ➔ 确认清单与预算 ➔ 动态拼装 Prompt ➔ 多端调度<br>• **双重质检体系**：确定性图像格式检查，骨骼关节点拟合与原图视觉 QA 矩阵 |
| [`whalechan-image-comic`](skills/whalechan-image-comic/) | **喜剧多格反转漫画生成**<br>将日常对话，技术讨论，报错日志或模型推理转化为 5 张富有自利机智人格的 1/2/4 格漫画。 | • **8 创意淘汰引擎**：锁定事实锚点，8 种语义偷换机制经无聊门禁与两两对决选出 Top 3<br>• **多格分镜语法**：支持 1 格/2 格/4 格，整组需覆盖 ≥2 种格数<br>• **视觉排版系统**：10 套蓝白气泡模板与去饱和抽象配角剪影 |

<br>

## 🚀 安装与环境配置

### 克隆仓库与准备运行环境

```bash
git clone https://github.com/Neko3000/deepseek-whalechan.git
cd deepseek-whalechan

# (推荐) 安装图像处理与验证依赖
pip install pillow
```

### 安装技能到智能体系统

#### 安装至默认运行环境

```bash
mkdir -p ~/.codex/skills
cp -R skills/* ~/.codex/skills/
```

> [!TIP]
> 重新启动或刷新 Codex 会话后，系统将自动识别 `$whalechan-image-character` 与 `$whalechan-image-comic`。

#### 安装至其他智能体环境

```bash
# Gemini / Antigravity
mkdir -p ~/.gemini/config/skills
cp -R skills/* ~/.gemini/config/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -R skills/* ~/.claude/skills/
```

### 配置外部图像供应商凭据（可选）

Codex 内置 ImageGen 是默认生图工具，无需额外配置 API Key。如需按既定顺序启用外部回退通道，请设置对应的环境变量：

```bash
# 1. OpenAI Images API (gpt-image-2)
export OPENAI_API_KEY="sk-..."
export OPENAI_IMAGE_MODEL="gpt-image-2"                 # 可选覆盖

# 2. Google Gemini / Nano Banana
export GEMINI_API_KEY="AIzaSy..."
# 或 export GOOGLE_API_KEY="AIzaSy..."
export NANO_BANANA_IMAGE_MODEL="gemini-3.1-flash-image" # 可选覆盖模型名称

# 3. 火山引擎 Seedream / Ark API
export ARK_API_KEY="..."
```

> [!CAUTION]
> 绝不要将真实的 API Key 提交至 Git 仓库，Prompt 文本，Assignment 任务卡或生成日志中。

<br>

## 💡 快速上手指南

### 场景一：生成高质量角色插画

在 Codex 对话终端中输入：

```text
使用 $whalechan-image-character，画三张 semi-chibi 鲸鱼娘：
场景：她正抱着一台刚刚修好的服务器主机，脸颊红扑扑，表情得意又理直气壮，背景保持暖米白，无文字。
```

**执行流程**：
- Agent 自动解析输入并生成任务清单（包含形态，参考图路径，预期预算等）；
- 得到用户显式确认后，Codex 按 ImageGen → OpenAI → Nano Banana → Seedream 的顺序生成与回退，并运行 `scripts/validate-image.py` 与 `scripts/measure-form.py`；
- 完成原分辨率视觉 QA 评估后，产物自动归档保存于 `artifacts/whalechan-image-character/<run-name>/`。

### 场景二：从对话或报错生成五张反转漫画

```text
使用 $whalechan-image-comic，把下面这段对话做成五张鲸鱼娘漫画：
“你刚才是不是把生产数据库的表删除了？！”
```

**执行流程**：
- Agent 锁定事实锚点（删除了数据库表）；
- 喜剧引擎构建 8 种自利反转（如：“将其重新命名为极致存储清理服务” / “为公司腾出了 100GB 宝贵空间并索要米饭奖励”）；
- 决出 Top 3 机制并扩展为 5 张涵盖 1 格，2 格，4 格的漫画，最终交付至 `artifacts/whalechan-image-comic/<run-name>/`。

<br>

## 🛠️ 本地命令行工具链

仓库内置了功能齐备，经过 100% 单元测试覆盖的 Python 工具脚本，可直接在命令行独立执行：

```bash
# 1. 运行全部单元测试 (106 个用例)
python3 -m unittest discover skills/whalechan-image-character/tests
python3 -m unittest discover skills/whalechan-image-comic/tests

# 2. 校验 Assignment 任务配置合法性
python3 skills/whalechan-image-comic/scripts/manage-run.py validate-assignment --assignment assignment.json

# 3. 对图像进行确定性技术指标检验 (格式/分辨率/色彩通道/背景)
python3 skills/whalechan-image-comic/scripts/validate-image.py candidate.png --resolution-mode auto --aspect-ratio 1:1

# 4. 测量图像中的骨骼头身比并输出覆盖图
python3 skills/whalechan-image-comic/scripts/measure-form.py candidate.png --output-overlay overlay.png

# 5. 本地多格分镜无损拼版
python3 skills/whalechan-image-comic/scripts/compose-panels.py --layout top-bottom --panels p1.png p2.png --output comic.png

# 6. 使用 Gemini Nano Banana API 单独生成候选图
python3 skills/whalechan-image-comic/scripts/generate-nanobanana.py --request request.json --output output.png
```

<br>

## 🗺️ 项目路线图

- [x] **角色基石**：全套鲸鱼娘视觉标准参考资产与 SHA-256 目录库
- [x] **比例规范**：5 大头身比形态数学定义与姿态中和测量工具 (`measure-form.py`)
- [x] **角色插画 Skill**：`whalechan-image-character` 核心流程与防过度消费确认机制
- [x] **漫画创作 Skill**：`whalechan-image-comic` 喜剧反转引擎与分镜系统
- [x] **多端降级适配**：Codex ImageGen / OpenAI / Nano Banana / Seedream 路由与自动化运行审计
- [ ] **统一 CLI 工具链**：提供独立的 `whalechan` 命令行工具，支持一键安装与本地快速出图
- [ ] **可视化 Web 样例库**：开发交互式 Web Gallery，支持在线浏览提示词与对应成品
- [ ] **提示词智能编译器**：输入自然语言自动编译为标准 Prompt Blocks 与同形态参考图推荐
- [ ] **自动一致性评测模型**：构建基于 Vision-LLM 的全自动角色一致性打分与回归测试流水线
- [ ] **更多 Agent 适配**：拓展支持 LangChain, AutoGen, CrewAI, Dify 等工作流生态

<br>

## 🤝 贡献指南

我们非常欢迎广大社区创作者与开发者共同参与建设鲸鱼娘生态！你可以通过提交 Issue 或 Pull Request 为项目贡献：

- 🎨 **创意与内容**：新的角色动作，表情设计，多格漫画剧本与反转创意；
- 🛠️ **工具与生态**：提示词模板，自动化脚本，测试用例以及更多 Agent 运行时的集成适配。

> [!IMPORTANT]
> **安全与隐私守则**：在提交任何代码，示例或日志前，请务必做好脱敏检查，**切勿提交任何真实的 API Key，私密聊天记录，未经授权的人物肖像或未获许可的第三方美术资产**。

<br>

## 📄 许可证说明

本项目采用分层开源授权协议：

- **开源代码与工具链**：本项目中的所有 Python 脚本，验证工具，测试用例与工程化代码均采用 [MIT License](LICENSE) 开源；
- **规范文档与 Skills 模版**：所有角色规范白皮书（Markdown），提示词模板，分镜规则与 Skill 配置采用 [CC-BY-NC-SA 4.0 国际许可协议](https://creativecommons.org/licenses/by-nc-sa/4.0/)。

<br>

## 🎨 角色形象与二创著作权归属

- **公共创作与人民群众贡献**：最根本且最重要地，鲸鱼娘形象的诞生，演进与传播，完全基于**广大网友人民群众的集体创作智慧与灵感贡献**，其基础文化生态归属于广大共创者；
- **已知原始素材与作者版权**：项目中收录，整理和参考的部分已知核心形象设定与二创素材来源于以下创作者，其原始著作权归原作者所有：
  - B站 **ZipZipPipe**：[space.bilibili.com/4168597](https://space.bilibili.com/4168597)
  - B站 **上善无形**：[space.bilibili.com/4456176](https://space.bilibili.com/4456176)
- **二创使用与商业限制**：
  - 欢迎并鼓励广大社区创作者在遵守本设定卡的前提下进行非商业性质的同人插画，多格漫画，表情包及衍生内容创作；
  - 任何商业性使用，商业出版或盈利性衍生品开发，必须获得相关原始著作权人及相关品牌权利方的明确书面授权；
  - 引用或基于本项目规则生成的内容，建议注明出处为 `DeepSeek Whale-chan Project`。

<p align="center">
  <sub>DeepSeek Whale-chan Project · Maintained by Community Contributors</sub>
</p>
