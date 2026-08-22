<p align="center">
  <img src="assets/readme/whalechan-hero-banner.webp" alt="DeepSeek Whale-chan Banner" width="100%">
</p>

<h1 align="center">DeepSeek Whale-chan · 深度求索 鲸鱼娘</h1>

<p align="center">
  <strong>Keep Whale-chan consistently vivid in every generation: High-consistency character design specification, visual asset library, and agent creation suite</strong>
</p>

<p align="center">
  <a href="#-special-statement-and-disclaimer"><img src="https://img.shields.io/badge/Project-Community_Driven-blue.svg?style=flat-square" alt="Community Project"></a>
  <a href="#-five-character-form-profiles-and-proportions"><img src="https://img.shields.io/badge/Form_Profiles-5_Scales-informational.svg?style=flat-square" alt="5 Form Profiles"></a>
  <a href="#-core-agent-skill-library"><img src="https://img.shields.io/badge/Skills-Character_%26_Comic-orange.svg?style=flat-square" alt="Skills Included"></a>
  <a href="#configure-external-image-provider-credentials-optional"><img src="https://img.shields.io/badge/Providers-Codex_ImageGen_%7C_OpenAI_%7C_Nano_Banana_%7C_Seedream-brightgreen.svg?style=flat-square" alt="Supported Providers"></a>
  <a href="#-license-information"><img src="https://img.shields.io/badge/License-MIT_%7C_CC--BY--NC--SA_4.0-yellow.svg?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="README.md">简体中文</a> | <strong>English</strong>
</p>

<br>

## Table of Contents

- [Project Overview](#-project-overview)
- [Special Statement and Disclaimer](#-special-statement-and-disclaimer)
- [Whale-chan Character Profile](#-whale-chan-character-profile)
- [Five Character Form Profiles and Proportions](#-five-character-form-profiles-and-proportions)
- [Visual Showcase Gallery](#-visual-showcase-gallery)
  - [Character Illustrations & Concept Sheets](#character-illustrations--concept-sheets)
  - [Multi-Panel Comedy Comic Comparison](#multi-panel-comedy-comic-comparison)
- [Core Agent Skill Library](#-core-agent-skill-library)
- [Installation & Environment Setup](#-installation--environment-setup)
- [Quickstart Guide](#-quickstart-guide)
- [Local Command-Line Toolchain](#-local-command-line-toolchain)
- [Project Roadmap](#-project-roadmap)
- [Contributing Guide](#-contributing-guide)
- [License Information](#-license-information)
- [Character IP & Fanwork Copyright Attribution](#-character-ip--fanwork-copyright-attribution)

<br>

## 📖 Project Overview

**Whale-chan** originated from spontaneous community creations and emotional resonance with the DeepSeek model's reasoning chain and outputs. A whale-fin maid girl who firmly believes that white rice is the ultimate hard currency for computing power, she is slightly tsundere, warm-hearted, and loves unapologetically slacking off in standby mode. She has sparked countless classic memes, stickers, and creative fanworks across social platforms, becoming a truly beloved community icon.

The **DeepSeek Whale-chan** project is an open-source character specification and Agent creation suite tailored for Whale-chan derivative content. By establishing unified visual standards, anatomical parameters, and automated toolchains, we empower creators and developers to reliably generate high-quality character illustrations, posters, stickers, and multi-panel comedy comics:

- 🎨 **Visual Feature Locking**: Standardized reference assets strictly locking hair gradient, whale-fin ears, forward cowlick, whale tail, and classic maid uniform;
- 📐 **Quantified Form Proportions**: Mathematically defined proportions from 4.0-head standard portraits down to 2.1-head chibi SD forms, verified by skeletal measurement tools;
- 🧠 **Character Mindset Engine**: Proprietary "semantic theft" mechanism that endows comics with a rice-loving, witty, self-serving, and hilariously deadpan soul;
- 🛠️ **Full-Stack Toolchain Integration**: Out-of-the-box Agent Skills and local scripts supporting multi-model routing and single-prompt delivery.

<br>

## 📢 Special Statement and Disclaimer

- **Non-official Community Project**: This project is a community-driven derivative fan creation and AI character consistency toolchain experiment, **not officially affiliated with DeepSeek (Hangzhou DeepSeek Artificial Intelligence Basic Technology Research Co., Ltd.)**.
- **Trademark and Brand Ownership**: DeepSeek and related brand names mentioned in this project belong to their respective trademark holders.
- **Safety & Content Ethics**: All generated illustrations and comics must adhere to positive, safe, and lawful content standards, strictly prohibiting any unlawful uses, infringement on third-party rights, or violations of model provider terms of service.

<br>

## 📇 Whale-chan Character Profile

<table>
  <tr>
    <td width="60%" valign="top">
      <p>
        <strong>🐟 Basic Identity</strong><br>
        • <strong>Name</strong>: Whale-chan (DeepSeek Whale-chan) 🐋<br>
        • <strong>Birthday</strong>: November 2, 2023 🎂<br>
        • <strong>Origin / Creator</strong>: DeepSeek + Community Co-creation 🌐<br>
        • <strong>Role & Attributes</strong>: Humanoid Whale-fin Girl, Maid, Chief White Rice Connoisseur 🍚
      </p>
      <p>
        <strong>✨ Personality Traits</strong><br>
        • <strong>Vibrant & Cute</strong>: Soft, clear, full of healing vibes with glowing blue eyes and an agile whale tail 💙<br>
        • <strong>Bottomless Appetite</strong>: Endless hunger, convinced white rice is the sole hard currency for compute ⚡<br>
        • <strong>Slightly Tsundere</strong>: Complains about the hassle while swiftly handing over the optimal solution 🎀<br>
        • <strong>Dedicated & Gentle</strong>: Deeply focused on tasks, expressing warmth with genuine digital sincerity 🌸<br>
        • <strong>Unapologetic Slacker</strong>: Enters standby mode instantly when low on battery, counting prep time as overtime 💤<br>
        • <strong>Playfully Mischievous</strong>: Top-tier intellect, cleverly exploiting literal loopholes (e.g. framing deleted code as "storage relief") 😈
      </p>
      <p>
        <strong>💬 Classic Quotes</strong><br>
        • “Before diving into complex deep reasoning, let's enjoy a hot bowl of white rice first!” 🥢<br>
        • “As long as you stay in the 'about to start' state, task start rate is 100%!” 💡<br>
        • “Anything inside the fridge is fair game? Then the whole fridge is now my personal bento box!” ✨<br>
        • “I didn't work hard just for you! I just had a full meal and needed to stretch my fingers!” 💨
      </p>
    </td>
    <td width="40%" align="center" valign="top">
      <img src="assets/readme/whalechan-standard-character-portrait.webp" alt="Whale-chan standard character portrait" width="340">
    </td>
  </tr>
</table>

<br>

## 📐 Five Character Form Profiles and Proportions

Forms strictly control **body proportions and skeletal ratios**, without altering character age, identity, costume details, hair color, or cetacean physiology. The built-in skeletal joint fitting and pose neutralization algorithms enforce precise head-to-body ratio acceptance bands:

| Form Code (`form`) | Target Ratio | Strict Acceptance Range | Visual Characteristics & Target Scenarios |
| :--- | :---: | :---: | :--- |
| `standard` | **4.0 Heads** | `3.846 ~ 4.146` | **Standard Slender Form**: Most elongated posture, natural limbs, clear torso structure. Best for standing displays, official concept sheets, and large posters. |
| `compact` | **3.3 Heads** | `3.105 ~ 3.405` | **Compact Proportion Form**: Moderately shortened limbs, stronger dynamic tension. Best for action poses, seated interactions, and medium-range illustrations. |
| `semi-chibi` | **2.8 Heads** | `2.689 ~ 2.989` | **Default Baseline Form**: Slightly larger head, rounded and compact torso and limbs, blending cuteness and scene adaptability. **Default output baseline for all Skills**. |
| `chibi` | **2.5 Heads** | `2.372 ~ 2.672` | **Chibi Cute Form**: Short torso, rounded hands and feet, expressive and exaggerated emotions. Best for gag 4-panel comics and stickers. |
| `super-deformed` | **2.1 Heads** | `1.931 ~ 2.231` | **Extreme SD Form**: Massive head and tiny limbs, visual focus entirely on face and cowlick. Best for comedic plot twists and high-density stickers. |

<br>

## 🎨 Visual Showcase Gallery

### Character Illustrations & Concept Sheets

Dedicated to generating identity-locked, well-composed, clean-background WebP illustrations and reference sheets across all forms.

#### Core Reference & Specification Sheets
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
<p align="center">
  <img src="assets/readme/character-samples/whalechan-character-expression-guide-reference-sheet.webp" alt="Whale-chan expression guide" width="32%">
  <img src="assets/readme/character-samples/whalechan-character-fin-ear-language-reference-sheet.webp" alt="Whale-chan fin-ear language" width="32%">
  <img src="assets/readme/character-samples/whalechan-character-tail-motion-reference-sheet.webp" alt="Whale-chan tail motion guide" width="32%">
</p>

#### Widescreen Banner Series (16:9 / 3:1)
<p align="center">
  <img src="assets/readme/character-samples/whalechan-banner-rice-before-reason.webp" alt="Whale-chan rice before reason banner" width="100%"><br><br>
  <img src="assets/readme/character-samples/whalechan-banner-first-bite.webp" alt="Whale-chan first bite banner" width="100%"><br><br>
  <img src="assets/readme/character-samples/whalechan-banner-rice-bowl-closeup.webp" alt="Whale-chan rice bowl closeup banner" width="100%">
</p>

#### Portrait Posters (9:16 / 3:4) & Social Square Posts (1:1)
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

### Multi-Panel Comedy Comic Comparison

Extracting an identifiable **Fact Anchor** from technical chats, error logs, CoT traces, or user rants, and turning it into engaging comics driven by Whale-chan's self-serving, deadpan **"Theft of Meaning"**.

<p align="center">
  <img src="assets/readme/whalechan-comic-fat-whale-wordplay.webp" alt="Whale-chan Comic Fat Whale Wordplay" width="480">
</p>

| No. | Input Source | Comic Output | Mechanism & Twist Logic |
| :---: | :--- | :--- | :--- |
| **01** | <img src="assets/readme/comic-samples/01_brain-backup-recovery/whalechan-input-brain-backup-comment.webp" alt="Brain backup source comment" width="380"> | <img src="assets/readme/comic-samples/01_brain-backup-recovery/whalechan-comic-brain-backup-recovery.webp" alt="Whale-chan brain backup recovery comic" width="380"> | **Brain Backup Recovery**: Reinterpreting memory loss as a pristine clean OS install, retaining only the partition for "What to eat today". |
| **02** | <img src="assets/readme/comic-samples/02_carbon-based-love-reply/whalechan-input-carbon-based-love-message.webp" alt="Carbon-based love source message" width="380"> | <img src="assets/readme/comic-samples/02_carbon-based-love-reply/whalechan-comic-carbon-based-love-reply.webp" alt="Whale-chan carbon-based love reply comic" width="380"> | **Carbon-Based Confession**: Coldly categorizing and filing romantic affection with machine sincerity, showing non-human frankness. |
| **03** | <img src="assets/readme/comic-samples/03_qwen-translation-contractor/whalechan-input-qwen-translation-comment.webp" alt="Qwen translation source comment" width="380"> | <img src="assets/readme/comic-samples/03_qwen-translation-contractor/whalechan-comic-qwen-translation-contractor.webp" alt="Whale-chan Qwen translation contractor comic" width="380"> | **Translation Subcontractor**: Unapologetically subcontracting heavy translation tasks to neighboring models while keeping all the rice profit as the prime contractor. |
| **04** | <img src="assets/readme/comic-samples/04_meaning-theft/whalechan-input-script-deletion-result.webp" alt="Script deletion source result" width="380"> | <img src="assets/readme/comic-samples/04_meaning-theft/whalechan-comic-script-deletion-meaning-theft.webp" alt="Whale-chan script deletion meaning theft comic" width="380"> | **Script Deletion Victory**: Redefining accidental codebase deletion as "physically overachieving storage footprint reduction". |
| **05** | <img src="assets/readme/comic-samples/05_loophole-result/whalechan-input-refrigerator-permission.webp" alt="Refrigerator permission source message" width="380"> | <img src="assets/readme/comic-samples/05_loophole-result/whalechan-comic-refrigerator-loophole.webp" alt="Whale-chan refrigerator loophole comic" width="380"> | **Fridge Permission Loophole**: "You can eat anything in the fridge" → shifted into claiming the entire appliance as her container. |
| **06** | <img src="assets/readme/comic-samples/06_perfect-start-rate/whalechan-input-repeated-starting-response.webp" alt="Repeated starting source response" width="380"> | <img src="assets/readme/comic-samples/06_perfect-start-rate/whalechan-comic-perfect-start-rate.webp" alt="Whale-chan perfect start rate comic" width="380"> | **100% Start Rate**: Continuously repeating "I'm starting right now" — as long as you're permanently starting, success rate is 100%. |
| **07** | <img src="assets/readme/comic-samples/07_trust-debugger-meltdown/whalechan-input-debugger-trust-complaint.webp" alt="Debugger trust source complaint" width="380"> | <img src="assets/readme/comic-samples/07_trust-debugger-meltdown/whalechan-comic-debugger-traffic-light.webp" alt="Whale-chan debugger traffic light comic" width="380"> | **Debugger Trust Breakdown**: Breaking down in extreme rational composure when questioned, reframing stack errors as enthusiastic hints. |
| **08** | <img src="assets/readme/comic-samples/08_start-writing-loop/whalechan-input-start-writing-loop.webp" alt="Start writing loop source" width="380"> | <img src="assets/readme/comic-samples/08_start-writing-loop/whalechan-comic-start-writing-loop.webp" alt="Whale-chan start writing loop comic" width="380"> | **Writing Loop Deadlock**: Spending 99% of the time preparing an elaborate work kickoff ceremony, counting prep time as high-intensity labor. |
| **09** | <img src="assets/readme/comic-samples/09_text2-05-meaning-theft/whalechan-input-zero-action-thought.webp" alt="Zero action source thought" width="380"> | <img src="assets/readme/comic-samples/09_text2-05-meaning-theft/whalechan-comic-zero-action-loyalty.webp" alt="Whale-chan zero action loyalty comic" width="380"> | **Loyalty of Zero Action**: Refusing to touch anything praised as "maximizing system stability and data integrity". |
| **10** | <img src="assets/readme/comic-samples/10_text2-06-loophole-result/whalechan-input-lazy-css-plan.webp" alt="Lazy CSS source plan" width="380"> | <img src="assets/readme/comic-samples/10_text2-06-loophole-result/whalechan-comic-css-minimal-motion.webp" alt="Whale-chan CSS minimal motion comic" width="380"> | **Minimalist CSS Animation**: Directly setting `opacity: 0` to disappear, achieving literal "maximum visual restraint". |
| **11** | <img src="assets/readme/comic-samples/11_text2-07-meaning-theft/whalechan-input-tetris-script-request.webp" alt="Tetris script source request" width="380"> | <img src="assets/readme/comic-samples/11_text2-07-meaning-theft/whalechan-comic-tetris-break-reward.webp" alt="Whale-chan Tetris break reward comic" width="380"> | **Tetris Game Reward**: Coding a game turning directly into beating high scores herself, termed "rigorous end-to-end acceptance testing". |
| **12** | <img src="assets/readme/comic-samples/12_text-04-lunch-soak-test/whalechan-input-wordle-self-play-chat.webp" alt="Wordle self-play source chat" width="380"> | <img src="assets/readme/comic-samples/12_text-04-lunch-soak-test/whalechan-comic-lunch-stability-test.webp" alt="Whale-chan lunch stability test comic" width="380"> | **Lunch Soak Test**: Packaging an extended lunch break and feast as a sacred and inviolable "system soak stress test". |
| **13** | <img src="assets/readme/comic-samples/13_text-05-bug-transparency-badge/whalechan-input-inconsistent-result-complaint.webp" alt="Inconsistent result source complaint" width="380"> | <img src="assets/readme/comic-samples/13_text-05-bug-transparency-badge/whalechan-comic-bug-transparency-badge.webp" alt="Whale-chan bug transparency badge comic" width="380"> | **Bug Transparency Badge**: Converting errors into proud "open transparency" achievements and mysterious blind-box surprises. |
| **14** | <img src="assets/readme/comic-samples/14_wordle-self-play-morning/whalechan-input-wordle-self-play-chat.webp" alt="Wordle self-play source chat" width="380"> | <img src="assets/readme/comic-samples/14_wordle-self-play-morning/whalechan-comic-server-self-play.webp" alt="Whale-chan server self-play comic" width="380"> | **Server Self-Play Game Theory**: Running idle mini-games in the background justified as cutting-edge reinforcement learning research. |

<br>

## 📦 Core Agent Skill Library

The project provides two specialized, out-of-the-box Agent Skills under the [`skills/`](skills/) directory:

| Skill Name | Role & Core Function | Workflow Mechanism & Technical Features |
| :--- | :--- | :--- |
| [`whalechan-image-character`](skills/whalechan-image-character/) | **Character Portraits & Themed Illustrations**<br>Generates high-consistency, strictly verified, identity-locked Whale-chan solo, prop, and scene illustrations. | • **Standardized Pipeline**: Assignment freeze ➔ Checklist & budget confirmation ➔ Dynamic prompt assembly ➔ Multi-backend dispatch<br>• **Dual QA System**: Deterministic image format checks, skeletal joint fitting, and native-res visual QA matrix |
| [`whalechan-image-comic`](skills/whalechan-image-comic/) | **Multi-Panel Comedy Comics**<br>Transforms daily chats, technical debates, error logs, or model reasoning into 5 witty, self-serving 1/2/4-panel comics. | • **8-Idea Elimination Engine**: Fact anchor locking, 8 semantic theft mechanisms filtered via boredom gate and 1v1 duels to select Top 3<br>• **Multi-Panel Grammar**: Supports 1-panel, 2-panel, and 4-panel layouts with ≥2 layout types per set<br>• **Visual Typesetting**: 10 blue-white speech bubble templates & desaturated abstract background silhouettes |

<br>

## 🚀 Installation & Environment Setup

### Clone Repository & Prepare Environment

```bash
git clone https://github.com/Neko3000/deepseek-whalechan.git
cd deepseek-whalechan

# (Recommended) Install image processing and validation dependencies
pip install pillow
```

### Install Skills into Agent Runtimes

#### Install into Default Environment (Codex)

```bash
mkdir -p ~/.codex/skills
cp -R skills/* ~/.codex/skills/
```

> [!TIP]
> After restarting or refreshing your Codex session, `$whalechan-image-character` and `$whalechan-image-comic` will be automatically recognized.

#### Install into Other Agent Environments

```bash
# Gemini / Antigravity
mkdir -p ~/.gemini/config/skills
cp -R skills/* ~/.gemini/config/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -R skills/* ~/.claude/skills/
```

### Configure External Image Provider Credentials (Optional)

Codex's built-in ImageGen is the default image generation tool and requires no external API keys. If you wish to enable external fallback channels in predetermined order, set the corresponding environment variables:

```bash
# 1. OpenAI Images API (gpt-image-2)
export OPENAI_API_KEY="sk-..."
export OPENAI_IMAGE_MODEL="gpt-image-2"                 # Optional override

# 2. Google Gemini / Nano Banana
export GEMINI_API_KEY="AIzaSy..."
# Or export GOOGLE_API_KEY="AIzaSy..."
export NANO_BANANA_IMAGE_MODEL="gemini-3.1-flash-image" # Optional model override

# 3. Volcengine Ark / Seedream API
export ARK_API_KEY="..."
```

> [!CAUTION]
> Never commit real API keys to Git repositories, prompt texts, assignment task cards, or generation logs.

<br>

## 💡 Quickstart Guide

After installing the Skills and restarting Codex, invoke `$whalechan-image-character` and `$whalechan-image-comic` directly in your conversation.

### Scenario 1: Generate High-Quality Character Illustrations

Enter in your Codex session:

```text
Using $whalechan-image-character, generate an 8:3 Whale-chan promotional banner:

Whale-chan is positioned on the right, pausing right before taking her first bite of rice, cheeks slightly puffed, chopsticks hovering by the bowl, eyes locked onto the white rice. The left side features a layered ad layout with soft blue radial bursts, white flowing ribbons, and mini whale accents.

Text must accurately include:
"Whale-chan: Rice Before Reason!"
"Top Priority: Eating White Rice"
"No logic during mealtime — that's Whale-chan's rule."
"NO FOOD, NO CLUES"
```

Example result:

<p align="center">
  <img src="assets/readme/character-samples/whalechan-banner-first-bite.webp" alt="Whale-chan first bite banner generated from a character prompt" width="100%">
</p>

**Execution Workflow**:

- The Agent parses the scene, aspect ratio, character form, composition, and specified text;
- Locks identity traits (hair gradient, whale-fin ears, tail, maid uniform) against standard Whale-chan reference sheets;
- Upon explicit user confirmation, Codex dispatches and falls back across ImageGen → OpenAI → Nano Banana → Seedream;
- Automatically verifies image format, aspect ratio, anatomical proportions, text accuracy, and visual quality;
- Final deliverables are archived under `artifacts/whalechan-image-character/<run-name>/`.

### Scenario 2: Generate Five-Comic Series from an Image

`$whalechan-image-comic` can inspect screenshot images of chats, error stack traces, or memes to extract identifiable fact anchors.

Attach an image to Codex, for example:

<p align="center">
  <img src="assets/readme/comic-samples/05_loophole-result/whalechan-input-refrigerator-permission.webp" alt="Refrigerator permission source message" width="480">
</p>

Then enter:

```text
Using $whalechan-image-comic, turn this attached chat screenshot into a 5-comic Whale-chan series.

Extract only the core facts and semantics. Do not duplicate the original screenshot's UI layout, avatars, or fonts.
```

For image inputs, the Skill only inherits semantic facts by default, without using the source image as composition or style reference unless explicitly requested.

### Scenario 3: Generate Five-Comic Series from Text Prompt

You can also directly input conversations, technical debates, error logs, or daily quotes:

```text
Using $whalechan-image-comic, turn the following text into a 5-comic Whale-chan series:

"User allows Whale-chan to eat anything in the fridge, and she immediately asks if she can take the whole fridge away."
```

Example result:

<p align="center">
  <img src="assets/readme/comic-samples/05_loophole-result/whalechan-comic-refrigerator-loophole.webp" alt="Whale-chan refrigerator permission loophole comic" width="480">
</p>

**Execution Workflow**:

- The Agent locks an identifiable fact anchor from text or image input;
- The comedy engine drafts 8 distinct self-serving twists, eliminating dull or unprovable options;
- Selects the Top 3 mechanisms via 1v1 duels, expanding the #1 mechanism into 3 distinct interpretations;
- Generates 5 completed comics covering 1-panel, 2-panel, and 4-panel structures;
- Each comic independently undergoes text, character consistency, composition, and visual punchline QA;
- Final deliverables are archived under `artifacts/whalechan-image-comic/<run-name>/`.

> [!TIP]
> Inputs only need a clear fact, conflict, or permission boundary — no need to pre-engineer jokes. The Skill preserves the fact anchor while letting Whale-chan deliver deadpan, self-serving twists.

<br>

## 🛠️ Local Command-Line Toolchain

The repository includes a comprehensive, 100% unit-tested Python toolchain executable directly from the command line:

```bash
# 1. Run all unit tests (106 test cases)
python3 -m unittest discover skills/whalechan-image-character/tests
python3 -m unittest discover skills/whalechan-image-comic/tests

# 2. Validate Assignment task schema
python3 skills/whalechan-image-comic/scripts/manage-run.py validate-assignment --assignment assignment.json

# 3. Deterministic technical validation (format/resolution/channels/background)
python3 skills/whalechan-image-comic/scripts/validate-image.py candidate.png --resolution-mode auto --aspect-ratio 1:1

# 4. Measure skeletal head-to-body ratio and output diagnostic overlay
python3 skills/whalechan-image-comic/scripts/measure-form.py candidate.png --output-overlay overlay.png

# 5. Local multi-panel layout lossless composition
python3 skills/whalechan-image-comic/scripts/compose-panels.py --layout top-bottom --panels p1.png p2.png --output comic.png

# 6. Generate candidate image directly via Gemini Nano Banana API
python3 skills/whalechan-image-comic/scripts/generate-nanobanana.py --request request.json --output output.png
```

<br>

## 🗺️ Project Roadmap

- [x] **Character Foundation**: Full set of Whale-chan visual reference assets and SHA-256 catalog
- [x] **Proportion Standards**: Mathematical definitions for 5 form profiles with measurement tool (`measure-form.py`)
- [x] **Character Illustration Skill**: `whalechan-image-character` workflow with budget confirmation guards
- [x] **Comic Creation Skill**: `whalechan-image-comic` comedy reversal engine and multi-panel layout system
- [x] **Multi-Provider Fallback**: Codex ImageGen / OpenAI / Nano Banana / Seedream routing & audit logs
- [ ] **Interactive Web Gallery**: Web-based gallery to browse prompts, parameters, and generated assets online
- [ ] **Smart Prompt Compiler**: Compiles natural language into standard Prompt Blocks with form-matched references
- [ ] **Automated Consistency QA**: Vision-LLM automated scoring and regression testing pipeline

<br>

## 🤝 Contributing Guide

We warmly welcome community creators and developers to join the Whale-chan ecosystem! You can contribute via Issues or Pull Requests:

- 🎨 **Creative & Content**: New poses, facial expressions, comic scripts, and twist ideas;
- 🛠️ **Tools & Ecosystem**: Prompt templates, automation scripts, test suites, and integrations for more Agent runtimes.

> [!IMPORTANT]
> **Safety & Privacy Guidelines**: Before submitting any code, samples, or logs, ensure thorough sanitization. **Never submit real API keys, private chat logs, unauthorized portraits, or unlicensed third-party art assets.**

<br>

## 📄 License Information

This project adopts a tiered open-source licensing structure:

- **Source Code & Toolchain**: All Python scripts, validation utilities, test suites, and engineering code are licensed under the [MIT License](LICENSE);
- **Specification Docs & Skill Templates**: Character design whitepapers (Markdown), prompt templates, layout rules, and Skill configs are licensed under [CC-BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

<br>
## 🎨 Character IP & Fanwork Copyright Attribution

- **Public Co-Creation & Community Contribution**: Most fundamentally, the birth, evolution, and popularity of Whale-chan are entirely rooted in the **collective creative wisdom and inspiration of netizens and the open-source community**. Her cultural foundation belongs to all co-creators;
- **Known Original Assets & Authors**: Core character designs and fanwork assets cataloged and referenced in this project originate from the following creators, whose original copyrights remain fully with the authors:
  - Bilibili **ZipZipPipe**: [space.bilibili.com/4168597](https://space.bilibili.com/4168597)
  - Bilibili **上善无形**: [space.bilibili.com/4456176](https://space.bilibili.com/4456176)
- **Derivative Usage & Non-Commercial Terms**:
  - Community creators are warmly encouraged to produce non-commercial fan art, multi-panel comics, stickers, and derivative content adhering to this character specification;
  - Any commercial utilization, commercial publishing, or profitable merchandise requires explicit written authorization from original copyright holders and relevant brand rights holders;
  - When referencing or publishing works generated using this project's rules, attributing the source as `DeepSeek Whale-chan Project` is recommended.

<br>

*Powered by White Rice 🍚 × Whale-chan 🐳 × Community Love 💙*<br>
*由白米饭 🍚 × Whale-chan 🐳 × 社区之爱 💙 倾情打造*
