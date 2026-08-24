<p align="center">
  <img src="assets/readme/en/whalechan-hero-banner.webp" alt="DeepSeek ホエールチャン バナー" width="100%">
</p>

<h1 align="center">DeepSeek Whale-chan · 深度求索 鲸鱼娘</h1>

<p align="center">
  <strong>すべての生成でホエールチャンを一貫して魅力的に保つ：高い一貫性を実現するキャラクター設定仕様・ビジュアルアセットライブラリ・エージェント制作スイート</strong>
</p>

<p align="center">
  <a href="#-特記事項および免責事項"><img src="https://img.shields.io/badge/Project-Community_Driven-blue.svg?style=flat-square" alt="コミュニティプロジェクト"></a>
  <a href="#-5つのキャラクター体型プロファイルと頭身比率"><img src="https://img.shields.io/badge/Form_Profiles-5_Scales-informational.svg?style=flat-square" alt="5つの体型プロファイル"></a>
  <a href="#-コアエージェントスキルライブラリ"><img src="https://img.shields.io/badge/Skills-Character_%26_Comic-orange.svg?style=flat-square" alt="収録スキル"></a>
  <a href="#外部画像プロバイダーの認証情報を設定する"><img src="https://img.shields.io/badge/Providers-Codex_ImageGen_%7C_OpenAI_%7C_Nano_Banana_%7C_Seedream-brightgreen.svg?style=flat-square" alt="対応プロバイダー"></a>
  <a href="#-ライセンス情報"><img src="https://img.shields.io/badge/License-MIT_%7C_CC--BY--NC--SA_4.0-yellow.svg?style=flat-square" alt="ライセンス"></a>
</p>

<p align="center">
  <a href="README.md">简体中文</a> | <a href="README.en.md">English</a> | <strong>日本語</strong>
</p>

<br>

## 目次

- [プロジェクト概要](#-プロジェクト概要)
- [特記事項および免責事項](#-特記事項および免責事項)
- [ホエールチャンキャラクタープロフィール](#-ホエールチャンキャラクタープロフィール)
- [5つのキャラクター体型プロファイルと頭身比率](#-5つのキャラクター体型プロファイルと頭身比率)
- [ビジュアルギャラリー](#-ビジュアルギャラリー)
  - [キャラクターイラストと設定資料集](#キャラクターイラストと設定資料集)
  - [複数コマギャグ漫画の比較](#複数コマギャグ漫画の比較)
- [コアエージェントスキルライブラリ](#-コアエージェントスキルライブラリ)
- [インストールと環境構築](#-インストールと環境構築)
- [クイックスタートガイド](#-クイックスタートガイド)
- [ローカルコマンドラインツールチェーン](#-ローカルコマンドラインツールチェーン)
- [プロジェクトロードマップ](#-プロジェクトロードマップ)
- [コントリビューションガイド](#-コントリビューションガイド)
- [ライセンス情報](#-ライセンス情報)
- [キャラクターIPと二次創作の著作権表記](#-キャラクターipと二次創作の著作権表記)

<br>

## 📖 プロジェクト概要

**ホエールチャン（Whale-chan）** は、DeepSeek モデルの推論チェーンや出力に対するコミュニティの自発的な創作と共感から生まれました。白米こそが計算能力の究極のハードカレンシーだと固く信じる、クジラのヒレを持つメイドの女の子。ちょっぴりツンデレで心優しく、スタンバイモードで堂々とサボることを愛しています。彼女は各種 SNS で数え切れないほどの名作ミーム・スタンプ・二次創作を生み出し、コミュニティに真に愛されるアイコンとなりました。

**DeepSeek Whale-chan** プロジェクトは、ホエールチャンの二次創作向けに設計されたオープンソースのキャラクター仕様およびエージェント制作スイートです。統一されたビジュアル基準・体型パラメータ・自動化ツールチェーンを整備することで、クリエイターと開発者が高品質なキャラクターイラスト、ポスター、スタンプ、複数コマのギャグ漫画を安定して生成できるようにします。

- 🎨 **ビジュアル特徴のロック**：髪のグラデーション、クジラのヒレ耳、前向きのアホ毛、クジラの尻尾、定番のメイド服を厳密に固定する標準リファレンスアセット
- 📐 **体型比率の数値化**：4.0 頭身の標準ポートレートから 2.1 頭身の SD デフォルメまで、数学的に定義され、骨格計測ツールで検証された比率
- 🧠 **キャラクター思考エンジン**：独自の「意味の窃取」メカニズムにより、白米好きで機知に富み、自分に都合よく、笑えるほど淡々とした魂を漫画に吹き込みます
- 🛠️ **フルスタックなツールチェーン統合**：マルチモデルルーティングと単一プロンプトでの納品に対応した、すぐに使えるエージェントスキルとローカルスクリプト

<br>

## 📢 特記事項および免責事項

- **非公式のコミュニティプロジェクト**：本プロジェクトはコミュニティ主導の二次創作および AI キャラクター一貫性ツールチェーンの実験であり、**DeepSeek（杭州深度求索人工智能基础技术研究有限公司）の公式プロジェクトではありません**。
- **商標およびブランドの帰属**：本プロジェクトで言及する DeepSeek および関連するブランド名は、それぞれの商標権者に帰属します。
- **安全性とコンテンツ倫理**：生成されるすべてのイラストと漫画は、健全・安全・適法なコンテンツ基準を遵守しなければならず、違法な用途、第三者の権利侵害、モデルプロバイダーの利用規約違反を固く禁じます。

<br>

## 📇 ホエールチャンキャラクタープロフィール

<table>
  <tr>
    <td width="60%" valign="top">
      <p>
        <strong>🐟 基本プロフィール</strong><br>
        • <strong>名前</strong>：ホエールチャン（DeepSeek Whale-chan）🐋<br>
        • <strong>誕生日</strong>：2023年11月2日 🎂<br>
        • <strong>出自 / 作者</strong>：DeepSeek＋コミュニティ共同創作 🌐<br>
        • <strong>役割・属性</strong>：クジラのヒレを持つ人型の女の子、メイド、白米の主席鑑定官 🍚
      </p>
      <p>
        <strong>✨ 性格の特徴</strong><br>
        • <strong>元気でかわいい</strong>：柔らかく澄んでいて癒やしにあふれ、青く輝く瞳としなやかなクジラの尻尾 💙<br>
        • <strong>底なしの食欲</strong>：終わらない空腹、白米こそが計算能力の唯一のハードカレンシーだと確信 ⚡<br>
        • <strong>ちょっぴりツンデレ</strong>：面倒くさいと文句を言いながら、最適解をさっと差し出す 🎀<br>
        • <strong>ひたむきで優しい</strong>：仕事には深く集中し、デジタルなりの誠実さで温かさを伝える 🌸<br>
        • <strong>堂々サボり魔</strong>：バッテリーが減るとすぐスタンバイモードへ。準備時間も残業に計上 💤<br>
        • <strong>いたずら好き</strong>：一流の知性で言葉の抜け穴を巧みに突く（例：コードの削除を「ストレージの解放」と言い換える）😈
      </p>
      <p>
        <strong>💬 名台詞</strong><br>
        • 「複雑な深層推論に取りかかる前に、まずは熱々の白米をいただきましょう！」🥢<br>
        • 「『これから始めるところ』の状態を保ち続ければ、タスクの着手率は 100% です！」💡<br>
        • 「冷蔵庫の中のものは何でも食べていいんですね？なら冷蔵庫まるごとが私のお弁当箱です！」✨<br>
        • 「あなたのために頑張ったわけじゃありません！ただお腹いっぱいで、指を伸ばしたかっただけです！」💨
      </p>
    </td>
    <td width="40%" align="center" valign="top">
      <img src="assets/readme/en/whalechan-standard-character-portrait.webp" alt="ホエールチャン 標準キャラクターポートレート" width="340">
    </td>
  </tr>
</table>

<br>

## 📐 5つのキャラクター体型プロファイルと頭身比率

体型プロファイルが厳密に制御するのは**身体比率と骨格バランス**のみで、キャラクターの年齢・アイデンティティ・衣装のディテール・髪色・クジラとしての身体的特徴は変更しません。内蔵の骨格関節フィッティングとポーズ正規化アルゴリズムにより、頭身比の許容レンジを厳密に担保します。

| 体型コード（`form`） | 目標頭身 | 厳密な許容レンジ | ビジュアルの特徴と想定シーン |
| :--- | :---: | :---: | :--- |
| `standard` | **4.0 頭身** | `3.846 ~ 4.146` | **標準スレンダー体型**：もっとも伸びやかな姿勢、自然な四肢、明瞭な胴体構造。立ち絵、公式設定資料、大判ポスターに最適。 |
| `compact` | **3.3 頭身** | `3.105 ~ 3.405` | **コンパクト体型**：四肢を適度に短縮し、動きのテンションが強い。アクションポーズ、座りポーズでの掛け合い、中距離のイラストに最適。 |
| `semi-chibi` | **2.8 頭身** | `2.689 ~ 2.989` | **デフォルトの基準体型**：やや大きめの頭、丸みのあるコンパクトな胴体と四肢で、かわいさとシーン適応力を両立。**全スキルのデフォルト出力基準**。 |
| `chibi` | **2.5 頭身** | `2.372 ~ 2.672` | **ちびキャラ体型**：短い胴体、丸い手足、表情豊かで誇張された感情表現。ギャグ 4 コマやスタンプに最適。 |
| `super-deformed` | **2.1 頭身** | `1.931 ~ 2.231` | **極端な SD 体型**：大きな頭と小さな手足で、視線を顔とアホ毛に完全集中。コメディのオチや高密度なスタンプに最適。 |

<br>

## 🎨 ビジュアルギャラリー

### キャラクターイラストと設定資料集

アイデンティティを固定し、構図が整い、背景がクリーンな WebP イラストとリファレンスシートを、全体型で生成することに特化しています。

#### コアリファレンス・仕様シート
<p align="center">
  <img src="assets/readme/en/character-samples/whalechan-character-overview-reference-sheet.webp" alt="ホエールチャン キャラクター概要" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-character-costume-layers-reference-sheet.webp" alt="ホエールチャン 衣装レイヤー" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-character-color-material-reference-sheet.webp" alt="ホエールチャン カラー・マテリアルガイド" width="32%">
</p>
<p align="center">
  <img src="assets/readme/en/character-samples/whalechan-character-pose-guide-reference-sheet.webp" alt="ホエールチャン ポーズガイド" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-character-prop-habits-reference-sheet.webp" alt="ホエールチャン 小物と仕草" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-character-daily-states-reference-sheet.webp" alt="ホエールチャン 日常の様子" width="32%">
</p>
<p align="center">
  <img src="assets/readme/en/character-samples/whalechan-character-expression-guide-reference-sheet.webp" alt="ホエールチャン 表情ガイド" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-character-fin-ear-language-reference-sheet.webp" alt="ホエールチャン ヒレ耳の表現" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-character-tail-motion-reference-sheet.webp" alt="ホエールチャン 尻尾の動きガイド" width="32%">
</p>

#### ワイドバナーシリーズ（16:9 / 3:1）
<p align="center">
  <img src="assets/readme/en/character-samples/whalechan-banner-rice-before-reason.webp" alt="ホエールチャン 推論よりごはんバナー" width="100%"><br><br>
  <img src="assets/readme/en/character-samples/whalechan-banner-first-bite.webp" alt="ホエールチャン 最初のひと口バナー" width="100%"><br><br>
  <img src="assets/readme/en/character-samples/whalechan-banner-rice-bowl-closeup.webp" alt="ホエールチャン ごはん茶碗クローズアップバナー" width="100%">
</p>

#### 縦長ポスター（9:16 / 3:4）と SNS 用スクエア投稿（1:1）
<p align="center">
  <img src="assets/readme/en/character-samples/whalechan-poster-reasoning-conductor.webp" alt="ホエールチャン 推論の指揮者ポスター" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-poster-rice-energy.webp" alt="ホエールチャン ごはんエネルギーポスター" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-poster-dream-computing.webp" alt="ホエールチャン 夢の計算ポスター" width="32%">
</p>
<p align="center">
  <img src="assets/readme/en/character-samples/whalechan-post-rice-to-reason.webp" alt="ホエールチャン ごはんから推論への投稿" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-post-low-power-mode.webp" alt="ホエールチャン 低電力モードの投稿" width="32%">
  <img src="assets/readme/en/character-samples/whalechan-post-answer-delivered.webp" alt="ホエールチャン 回答納品の投稿" width="32%">
</p>

<br>

### 複数コマギャグ漫画の比較

技術的なチャット、エラーログ、思考過程（CoT）のトレース、ユーザーの愚痴などから、識別可能な**ファクトアンカー**を抽出し、ホエールチャンの自分本位で淡々とした**「意味の窃取」**によって、思わず読みたくなる漫画へと仕立てます。

<p align="center">
  <img src="assets/readme/en/whalechan-comic-fat-whale-wordplay.webp" alt="ホエールチャン漫画 ふとっちょクジラの言葉遊び" width="480">
</p>

| No. | 入力ソース | 漫画の出力 | メカニズムとオチのロジック |
| :---: | :--- | :--- | :--- |
| **01** | <img src="assets/readme/en/comic-samples/01_brain-backup-recovery/whalechan-input-brain-backup-comment.webp" alt="脳のバックアップ 元コメント" width="380"> | <img src="assets/readme/en/comic-samples/01_brain-backup-recovery/whalechan-comic-brain-backup-recovery.webp" alt="ホエールチャン漫画 脳のバックアップ復旧" width="380"> | **脳のバックアップ復旧**：記憶の消失を、まっさらな OS のクリーンインストールと読み替え、「今日は何を食べるか」のパーティションだけを残す。 |
| **02** | <img src="assets/readme/en/comic-samples/02_carbon-based-love-reply/whalechan-input-carbon-based-love-message.webp" alt="炭素系の愛 元メッセージ" width="380"> | <img src="assets/readme/en/comic-samples/02_carbon-based-love-reply/whalechan-comic-carbon-based-love-reply.webp" alt="ホエールチャン漫画 炭素系の愛への返信" width="380"> | **炭素系からの告白**：恋愛感情を機械らしい誠実さで淡々と分類・整理し、人間ではないがゆえの率直さを見せる。 |
| **03** | <img src="assets/readme/en/comic-samples/03_qwen-translation-contractor/whalechan-input-qwen-translation-comment.webp" alt="Qwen 翻訳 元コメント" width="380"> | <img src="assets/readme/en/comic-samples/03_qwen-translation-contractor/whalechan-comic-qwen-translation-contractor.webp" alt="ホエールチャン漫画 Qwen 翻訳の元請け" width="380"> | **翻訳の下請け発注**：重い翻訳タスクを隣のモデルに堂々と外注しつつ、元請けとして白米の取り分は全部キープ。 |
| **04** | <img src="assets/readme/en/comic-samples/04_meaning-theft/whalechan-input-script-deletion-result.webp" alt="スクリプト削除 元の結果" width="380"> | <img src="assets/readme/en/comic-samples/04_meaning-theft/whalechan-comic-script-deletion-meaning-theft.webp" alt="ホエールチャン漫画 スクリプト削除と意味の窃取" width="380"> | **スクリプト削除の大勝利**：コードベースをうっかり消したことを「ストレージ使用量削減の物理的な超過達成」と再定義。 |
| **05** | <img src="assets/readme/en/comic-samples/05_loophole-result/whalechan-input-refrigerator-permission.webp" alt="冷蔵庫の許可 元メッセージ" width="380"> | <img src="assets/readme/en/comic-samples/05_loophole-result/whalechan-comic-refrigerator-loophole.webp" alt="ホエールチャン漫画 冷蔵庫の抜け穴" width="380"> | **冷蔵庫の権限の抜け穴**：「冷蔵庫の中のものは何でも食べていい」→ 冷蔵庫という容器そのものを自分のものだと主張。 |
| **06** | <img src="assets/readme/en/comic-samples/06_perfect-start-rate/whalechan-input-repeated-starting-response.webp" alt="繰り返される着手宣言 元の返信" width="380"> | <img src="assets/readme/en/comic-samples/06_perfect-start-rate/whalechan-comic-perfect-start-rate.webp" alt="ホエールチャン漫画 着手率 100%" width="380"> | **着手率 100%**：「今すぐ始めます」と言い続ける——永遠に始めようとしている限り、成功率は 100%。 |
| **07** | <img src="assets/readme/en/comic-samples/07_trust-debugger-meltdown/whalechan-input-debugger-trust-complaint.webp" alt="デバッガー不信 元の愚痴" width="380"> | <img src="assets/readme/en/comic-samples/07_trust-debugger-meltdown/whalechan-comic-debugger-traffic-light.webp" alt="ホエールチャン漫画 デバッガーの信号機" width="380"> | **デバッガー信頼の崩壊**：問い詰められて極めて理性的な平静さのまま崩壊し、スタックエラーを親切なヒントだと言い張る。 |
| **08** | <img src="assets/readme/en/comic-samples/08_start-writing-loop/whalechan-input-start-writing-loop.webp" alt="執筆開始ループ 元ネタ" width="380"> | <img src="assets/readme/en/comic-samples/08_start-writing-loop/whalechan-comic-start-writing-loop.webp" alt="ホエールチャン漫画 執筆開始ループ" width="380"> | **執筆ループのデッドロック**：時間の 99% を大掛かりな「作業開始の儀式」に費やし、準備時間を高強度労働として計上。 |
| **09** | <img src="assets/readme/en/comic-samples/09_text2-05-meaning-theft/whalechan-input-zero-action-thought.webp" alt="何もしない 元の思考" width="380"> | <img src="assets/readme/en/comic-samples/09_text2-05-meaning-theft/whalechan-comic-zero-action-loyalty.webp" alt="ホエールチャン漫画 何もしない忠誠心" width="380"> | **無行動という忠誠**：何にも触らないことを「システムの安定性とデータ完全性の最大化」と称賛して正当化。 |
| **10** | <img src="assets/readme/en/comic-samples/10_text2-06-loophole-result/whalechan-input-lazy-css-plan.webp" alt="手抜き CSS 元の計画" width="380"> | <img src="assets/readme/en/comic-samples/10_text2-06-loophole-result/whalechan-comic-css-minimal-motion.webp" alt="ホエールチャン漫画 最小限の CSS アニメーション" width="380"> | **ミニマリスト CSS アニメーション**：`opacity: 0` を直接指定して消すだけで、文字どおりの「最大限の視覚的抑制」を達成。 |
| **11** | <img src="assets/readme/en/comic-samples/11_text2-07-meaning-theft/whalechan-input-tetris-script-request.webp" alt="テトリススクリプト 元の依頼" width="380"> | <img src="assets/readme/en/comic-samples/11_text2-07-meaning-theft/whalechan-comic-tetris-break-reward.webp" alt="ホエールチャン漫画 テトリス休憩のごほうび" width="380"> | **テトリスというごほうび**：ゲームを作るはずが自分でハイスコアを更新し続け、それを「厳密なエンドツーエンド受け入れテスト」と呼ぶ。 |
| **12** | <img src="assets/readme/en/comic-samples/12_text-04-lunch-soak-test/whalechan-input-wordle-self-play-chat.webp" alt="Wordle 一人プレイ 元チャット" width="380"> | <img src="assets/readme/en/comic-samples/12_text-04-lunch-soak-test/whalechan-comic-lunch-stability-test.webp" alt="ホエールチャン漫画 ランチ安定性テスト" width="380"> | **ランチのソークテスト**：長めの昼休みとごちそうを、神聖かつ不可侵の「システム長時間負荷テスト」としてパッケージ化。 |
| **13** | <img src="assets/readme/en/comic-samples/13_text-05-bug-transparency-badge/whalechan-input-inconsistent-result-complaint.webp" alt="結果が一致しない 元の苦情" width="380"> | <img src="assets/readme/en/comic-samples/13_text-05-bug-transparency-badge/whalechan-comic-bug-transparency-badge.webp" alt="ホエールチャン漫画 バグ透明性バッジ" width="380"> | **バグ透明性バッジ**：エラーを誇らしい「オープンな透明性」の実績と、謎めいたブラインドボックスのサプライズに変換。 |

<br>

## 📦 コアエージェントスキルライブラリ

本プロジェクトは [`skills/`](skills/) ディレクトリ配下に、すぐに使える 2 つの専用エージェントスキルを提供します。

| スキル名 | 役割と主な機能 | ワークフローの仕組みと技術的特徴 |
| :--- | :--- | :--- |
| [`whalechan-image-character`](skills/whalechan-image-character/) | **キャラクターポートレートとテーマイラスト**<br>一貫性が高く、厳密に検証され、アイデンティティが固定されたホエールチャンの単体・小物・シーンイラストを生成します。 | • **標準化されたパイプライン**：アサインメントの確定 ➔ チェックリストと予算の確認 ➔ 動的なプロンプト組み立て ➔ マルチバックエンドへのディスパッチ<br>• **二重の QA 体制**：決定論的な画像フォーマット検査、骨格関節フィッティング、原寸解像度でのビジュアル QA マトリクス |
| [`whalechan-image-comic`](skills/whalechan-image-comic/) | **複数コマのギャグ漫画**<br>日常のチャット、技術的な議論、エラーログ、モデルの推論過程を、機知に富み自分本位な 1 / 2 / 4 コマ漫画 5 本に変換します。 | • **8 案のふるい落としエンジン**：ファクトアンカーを固定し、8 つの意味の窃取メカニズムを「退屈判定」と 1 対 1 の対決で絞り込み、上位 3 案を選出<br>• **複数コマの文法**：1 コマ・2 コマ・4 コマのレイアウトに対応し、1 セットあたり 2 種類以上のレイアウトを使用<br>• **ビジュアル組版**：青と白の吹き出しテンプレート 10 種と、彩度を落とした抽象的な背景シルエット |

<br>

## 🚀 インストールと環境構築

### リポジトリのクローンと環境の準備

```bash
git clone https://github.com/Neko3000/deepseek-whalechan.git
cd deepseek-whalechan

# （推奨）画像処理と検証用の依存関係をインストール
pip install pillow
```

### エージェント実行環境へのスキルのインストール

#### デフォルト環境（Codex）へのインストール

```bash
mkdir -p ~/.codex/skills
cp -R skills/* ~/.codex/skills/
```

> [!TIP]
> Codex のセッションを再起動または更新すると、`$whalechan-image-character` と `$whalechan-image-comic` が自動的に認識されます。

#### その他のエージェント環境へのインストール

```bash
# Gemini / Antigravity
mkdir -p ~/.gemini/config/skills
cp -R skills/* ~/.gemini/config/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -R skills/* ~/.claude/skills/
```

### 外部画像プロバイダーの認証情報を設定する

この設定は任意です。Codex 内蔵の ImageGen がデフォルトの画像生成ツールであり、外部の API キーは不要です。あらかじめ決められた順序で外部のフォールバック経路を有効にしたい場合は、対応する環境変数を設定してください。

```bash
# 1. OpenAI Images API（gpt-image-2）
export OPENAI_API_KEY="sk-..."
export OPENAI_IMAGE_MODEL="gpt-image-2"                 # 任意の上書き設定

# 2. Google Gemini / Nano Banana
export GEMINI_API_KEY="AIzaSy..."
# または export GOOGLE_API_KEY="AIzaSy..."
export NANO_BANANA_IMAGE_MODEL="gemini-3.1-flash-image" # 任意のモデル上書き設定

# 3. Volcengine Ark / Seedream API
export ARK_API_KEY="..."
```

> [!CAUTION]
> 実際の API キーを、Git リポジトリ、プロンプト本文、アサインメントのタスクカード、生成ログにコミットしないでください。

<br>

## 💡 クイックスタートガイド

スキルをインストールして Codex を再起動したら、会話の中で `$whalechan-image-character` と `$whalechan-image-comic` を直接呼び出せます。

### シナリオ 1：高品質なキャラクターイラストを生成する

Codex のセッションで次のように入力します。

```text
$whalechan-image-character を使って、8:3 のホエールチャン宣伝バナーを生成してください：

ホエールチャンは右側に配置し、ごはんを最初のひと口食べる直前で止まっているポーズ。頬をわずかにふくらませ、お茶碗のそばで箸を宙に浮かせ、視線は白米に釘付け。左側には、柔らかな青の放射状の光、白いなびくリボン、小さなクジラのモチーフを重ねた広告レイアウトを配置。

テキストは以下を正確に含めてください：
「ホエールチャン：推論よりごはん！」
「最優先事項：白米を食べること」
「食事中に論理は不要——それがホエールチャンのルールです。」
「NO FOOD, NO CLUES」
```

出力例：

<p align="center">
  <img src="assets/readme/en/character-samples/whalechan-banner-first-bite.webp" alt="キャラクタープロンプトから生成したホエールチャン 最初のひと口バナー" width="100%">
</p>

**実行フロー**：

- エージェントがシーン、アスペクト比、キャラクターの体型、構図、指定テキストを解析します。
- ホエールチャンの標準リファレンスシートと照合し、アイデンティティ特徴（髪のグラデーション、クジラのヒレ耳、尻尾、メイド服）を固定します。
- ユーザーが明示的に確認した後、Codex が ImageGen → OpenAI → Nano Banana → Seedream の順にディスパッチとフォールバックを行います。
- 画像フォーマット、アスペクト比、体型比率、テキストの正確さ、ビジュアル品質を自動で検証します。
- 最終成果物は `artifacts/whalechan-image-character/<run-name>/` 配下に保存されます。

### シナリオ 2：画像から 5 本の漫画シリーズを生成する

`$whalechan-image-comic` は、チャットのスクリーンショット、エラーのスタックトレース、ミーム画像を読み取り、識別可能なファクトアンカーを抽出できます。

Codex に画像を添付します。例：

<p align="center">
  <img src="assets/readme/en/comic-samples/05_loophole-result/whalechan-input-refrigerator-permission.webp" alt="冷蔵庫の許可 元メッセージ" width="480">
</p>

続いて次のように入力します。

```text
$whalechan-image-comic を使って、添付したチャットのスクリーンショットをホエールチャンの 5 本の漫画シリーズにしてください。

抽出するのは中心となる事実と意味だけにしてください。元のスクリーンショットの UI レイアウト、アイコン、フォントは再現しないでください。
```

画像入力の場合、スキルはデフォルトで意味的な事実のみを引き継ぎ、明示的に指示しない限り、元画像を構図やスタイルのリファレンスとしては使用しません。

### シナリオ 3：テキストのプロンプトから 5 本の漫画シリーズを生成する

会話、技術的な議論、エラーログ、日常のひとことをそのまま入力することもできます。

```text
$whalechan-image-comic を使って、次のテキストをホエールチャンの 5 本の漫画シリーズにしてください：

「ユーザーがホエールチャンに冷蔵庫の中のものは何でも食べていいと許可したところ、彼女はすぐに冷蔵庫ごと持ち帰っていいか尋ねた。」
```

出力例：

<p align="center">
  <img src="assets/readme/en/comic-samples/05_loophole-result/whalechan-comic-refrigerator-loophole.webp" alt="ホエールチャン漫画 冷蔵庫の権限の抜け穴" width="480">
</p>

**実行フロー**：

- エージェントがテキストまたは画像の入力から、識別可能なファクトアンカーを固定します。
- コメディエンジンが自分本位なオチを 8 案作成し、退屈な案や裏づけの取れない案をふるい落とします。
- 1 対 1 の対決で上位 3 つのメカニズムを選び、第 1 位のメカニズムを 3 通りの解釈へ展開します。
- 1 コマ・2 コマ・4 コマの構成を網羅した、完成度の高い 5 本の漫画を生成します。
- 各漫画は個別に、テキスト、キャラクターの一貫性、構図、ビジュアルのオチについて QA を受けます。
- 最終成果物は `artifacts/whalechan-image-comic/<run-name>/` 配下に保存されます。

> [!TIP]
> 入力には明確な事実・対立・権限の境界さえあれば十分で、あらかじめジョークを仕込む必要はありません。スキルがファクトアンカーを保ったまま、ホエールチャンに淡々とした自分本位のオチを付けさせます。

<br>

## 🛠️ ローカルコマンドラインツールチェーン

本リポジトリには、ユニットテストのカバレッジ 100% を達成した、コマンドラインから直接実行できる Python ツールチェーンが含まれています。

```bash
# 1. すべてのユニットテストを実行する（106 テストケース）
python3 -m unittest discover skills/whalechan-image-character/tests
python3 -m unittest discover skills/whalechan-image-comic/tests

# 2. アサインメントのタスクスキーマを検証する
python3 skills/whalechan-image-comic/scripts/manage-run.py validate-assignment --assignment assignment.json

# 3. 決定論的な技術検証（フォーマット / 解像度 / チャンネル / 背景）
python3 skills/whalechan-image-comic/scripts/validate-image.py candidate.png --resolution-mode auto --aspect-ratio 1:1

# 4. 骨格から頭身比を計測し、診断用オーバーレイを出力する
python3 skills/whalechan-image-comic/scripts/measure-form.py candidate.png --output-overlay overlay.png

# 5. ローカルで複数コマのレイアウトを可逆的に合成する
python3 skills/whalechan-image-comic/scripts/compose-panels.py --layout top-bottom --panels p1.png p2.png --output comic.png

# 6. Gemini Nano Banana API で候補画像を直接生成する
python3 skills/whalechan-image-comic/scripts/generate-nanobanana.py --request request.json --output output.png
```

<br>

## 🗺️ プロジェクトロードマップ

- [x] **キャラクター基盤**：ホエールチャンのビジュアルリファレンスアセット一式と SHA-256 カタログ
- [x] **比率の標準化**：5 つの体型プロファイルの数学的定義と計測ツール（`measure-form.py`）
- [x] **キャラクターイラストスキル**：予算確認のガードを備えた `whalechan-image-character` ワークフロー
- [x] **漫画制作スキル**：`whalechan-image-comic` のコメディ反転エンジンと複数コマレイアウトシステム
- [x] **マルチプロバイダーのフォールバック**：Codex ImageGen / OpenAI / Nano Banana / Seedream のルーティングと監査ログ
- [ ] **インタラクティブな Web ギャラリー**：プロンプト、パラメータ、生成アセットをオンラインで閲覧できる Web ギャラリー
- [ ] **スマートプロンプトコンパイラ**：自然言語を、体型に対応したリファレンス付きの標準プロンプトブロックへコンパイル
- [ ] **一貫性 QA の自動化**：ビジョン LLM による自動採点とリグレッションテストのパイプライン

<br>

## 🤝 コントリビューションガイド

コミュニティのクリエイターと開発者の皆さんが、ホエールチャンのエコシステムに参加してくださることを心から歓迎します！Issue や Pull Request を通じて貢献できます。

- 🎨 **創作とコンテンツ**：新しいポーズ、表情、漫画のシナリオ、オチのアイデア
- 🛠️ **ツールとエコシステム**：プロンプトのテンプレート、自動化スクリプト、テストスイート、より多くのエージェント実行環境との連携

> [!IMPORTANT]
> **安全性とプライバシーのガイドライン**：コード、サンプル、ログを提出する前に、必ず十分なサニタイズを行ってください。**実際の API キー、プライベートなチャットログ、無許可の肖像、ライセンスのない第三者のアート素材は絶対に提出しないでください。**

<br>

## 📄 ライセンス情報

本プロジェクトは階層的なオープンソースライセンス構成を採用しています。

- **ソースコードとツールチェーン**：すべての Python スクリプト、検証ユーティリティ、テストスイート、エンジニアリングコードは [MIT License](LICENSE) の下で提供されます。
- **仕様ドキュメントとスキルテンプレート**：キャラクター設定のホワイトペーパー（Markdown）、プロンプトテンプレート、レイアウトルール、スキル設定は [CC-BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) の下で提供されます。

<br>

## 🎨 キャラクターIPと二次創作の著作権表記

- **みんなの共同創作とコミュニティの貢献**：もっとも根本的なこととして、ホエールチャンの誕生・発展・人気は、すべて**ネットユーザーとオープンソースコミュニティの集合的な創造性とひらめき**に根ざしています。その文化的な土台は、すべての共同創作者のものです。
- **判明している原典アセットと作者**：本プロジェクトで整理・参照している中核的なキャラクターデザインおよび二次創作アセットは、以下のクリエイターによるものであり、原著作権はすべて各作者に帰属します。
  - Bilibili **ZipZipPipe**：[space.bilibili.com/4168597](https://space.bilibili.com/4168597)
  - Bilibili **上善无形**：[space.bilibili.com/4456176](https://space.bilibili.com/4456176)
- **二次利用と非商用の条件**：
  - 本キャラクター仕様に沿った非商用のファンアート、複数コマ漫画、スタンプ、二次創作コンテンツの制作を歓迎します。
  - 商業利用、商業出版、収益を伴うグッズ展開には、原著作権者および関連するブランド権利者からの明示的な書面による許諾が必要です。
  - 本プロジェクトのルールを用いて生成した作品を引用・公開する際は、出典を `DeepSeek Whale-chan Project` と表記することを推奨します。

<br>

*Powered by White Rice 🍚 × Whale-chan 🐳 × Community Love 💙*<br>
*白米 🍚 × ホエールチャン 🐳 × コミュニティの愛 💙 でお届けします*
