"use strict";
const data = JSON.parse(document.getElementById("gallery-data").textContent);
const app = document.getElementById("app");
const dialog = document.getElementById("lightbox");
const largeImage = document.getElementById("large-image");
const stage = document.getElementById("image-stage");
const info = document.getElementById("lightbox-info");
let activeGroup = 0, view = "grid", currentPictures = [], currentIndex = 0, opener;
const roleNames = {candidate:"整图候选", component:"分格组件", composite:"本地合成"};
const roleLabels = {identity:"角色身份", style:"画风", proportion:"比例", typography:"文字样式", composition:"构图", costume:"服装", background:"背景", pose_action:"动作"};
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function button(text, action) {
  const node = el("button", "", text);
  node.type = "button";
  node.addEventListener("click", action);
  return node;
}
function details(title) {
  const node = el("details");
  node.append(el("summary", "", title));
  return node;
}
function text(value) { return value == null || value === "" ? "未记录" : typeof value === "string" ? value : JSON.stringify(value, null, 2); }
function badge(value, kind = "") { return el("span", `badge ${kind}`, value); }
function date(value) { return value ? value.replace("T", " ").replace(/\.\d+/, "") : "未记录"; }
function promptBlock(value) {
  const block = details("实际生图提示词");
  if (!value) { block.append(el("p", "muted", "未记录")); return block; }
  const area = el("textarea", "prompt");
  area.value = value;
  area.readOnly = true;
  area.setAttribute("aria-label", "实际生图提示词");
  const status = el("span", "copy-status");
  status.setAttribute("role", "status");
  const copy = button("复制提示词", async () => {
    try {
      await navigator.clipboard.writeText(value);
      status.textContent = "已复制";
    } catch {
      area.focus(); area.select();
      status.textContent = "已选中，请按 ⌘C / Ctrl+C 复制";
    }
  });
  block.append(area, copy, status);
  return block;
}
function attemptInfo(attempt, all = []) {
  const box = el("div");
  if (!attempt) { box.append(el("p", "muted", "成品来源未能唯一确认，请查看生成过程。")); return box; }
  const meta = el("div", "meta");
  meta.append(badge(roleNames[attempt.role] || attempt.role), badge(attempt.verdict || "未记录", attempt.verdict === "PASS" ? "good" : "warn"));
  box.append(meta);
  if (attempt.role === "composite") {
    box.append(el("p", "note", "由分格图片本地合成，不增加产图次数。"));
    for (const id of attempt.sources) {
      const source = all.find(item => item.id === id);
      const part = details(`分格 ${id}`);
      if (source) part.append(attemptInfo(source));
      else part.append(el("p", "muted", "分格来源未记录"));
      box.append(part);
    }
  } else {
    box.append(el("p", "note", `${text(attempt.provider)} / ${text(attempt.model)}`), promptBlock(attempt.prompt));
  }
  box.append(el("p", "note", `记录时间：${date(attempt.created_at)}`));
  const qa = details("验收记录");
  qa.append(el("p", "", `自动检查：${text(attempt.automatic)} · 视觉检查：${text(attempt.visual)}`));
  if (attempt.defects?.length) qa.append(el("p", "", text(attempt.defects)));
  if (attempt.verdict === "FAIL" && !attempt.defects?.length) qa.append(el("p", "muted", "失败原因未记录"));
  if (attempt.targeted_retry) qa.append(el("p", "", `修正建议：${text(attempt.targeted_retry)}`));
  box.append(qa);
  return box;
}
function imageButton(picture, collection, detailFactory) {
  if (!picture?.src) return el("div", "missing", picture ? "图片文件缺失" : "尚无通过验收的成品");
  const entry = {picture, detailFactory};
  collection.push(entry);
  const node = button("", () => {
    opener = node;
    currentPictures = collection;
    currentIndex = collection.indexOf(entry);
    updateLightbox();
    dialog.showModal();
    document.body.style.overflow = "hidden";
    document.getElementById("close-lightbox").focus();
  });
  node.className = "picture";
  node.setAttribute("aria-label", `放大 ${picture.label}`);
  const img = el("img");
  img.src = picture.src; img.alt = picture.label; img.loading = "lazy";
  node.append(img);
  return node;
}
function sourceStrip(pictures) {
  const strip = el("div", "source-strip");
  const collection = [];
  pictures.forEach(picture => {
    const figure = el("figure", "figure");
    figure.append(imageButton(picture, collection), el("figcaption", "", picture.label));
    if (picture.roles) figure.append(el("figcaption", "", picture.roles.map(role => roleLabels[role] || role).join(" · ")));
    strip.append(figure);
  });
  return strip;
}
function card(image, collection) {
  const article = el("article", "card");
  article.append(imageButton(image.final, collection, () => attemptInfo(image.origin, image.attempts)));
  const body = el("div", "card-content");
  body.append(el("h3", "", image.name));
  const meta = el("div", "meta");
  const delivered = image.status === "passed";
  meta.append(badge(delivered ? "已通过" : image.calls ? "未通过" : "未产出", delivered ? "good" : "warn"), badge(`产图 ${image.calls} 次`));
  if (image.final?.width) meta.append(badge(`${image.final.width} × ${image.final.height}`));
  body.append(meta);
  if (image.note) body.append(el("p", "note", image.note));
  if (delivered) body.append(attemptInfo(image.origin, image.attempts));
  const history = details(`生成过程 · ${image.calls} 次产图 · ${image.errors.length} 次接口错误`);
  const candidates = [];
  image.attempts.forEach(attempt => {
    const section = el("div", "attempt");
    section.append(el("p", "note", `${attempt.id} · ${roleNames[attempt.role] || attempt.role}`));
    section.append(imageButton(attempt.picture, candidates, () => attemptInfo(attempt, image.attempts)), attemptInfo(attempt, image.attempts));
    history.append(section);
  });
  if (!image.attempts.length) history.append(el("p", "muted", "没有产图记录"));
  image.errors.forEach(error => {
    const section = el("div", "attempt");
    section.append(el("p", "", `${text(error.provider)} / ${text(error.model)} · ${text(error.category)}`), el("p", "muted", text(error.details)), el("p", "muted", date(error.created_at)));
    history.append(section);
  });
  body.append(history); article.append(body);
  return article;
}
function renderGroup(group, panel) {
  panel.replaceChildren();
  const source = el("section", "source");
  source.append(el("div", "section-label", "THE STARTING POINT / 创作起点"), el("h2", "", group.title));
  source.append(el("p", "note", `${group.passed} / ${group.planned} 张已通过 · 产图 ${group.calls} 次 · ${group.errors} 次接口错误 · ${date(group.date)}`));
  if (group.request) {
    source.append(el("p", "section-label", "用户原始要求"), el("p", "source-text", group.request));
  } else source.append(el("p", "note", "用户原始文字要求未记录；输入素材见下方。"));
  if (group.originals.length) source.append(sourceStrip(group.originals));
  if (group.analysis) {
    const analysis = details("素材转述 · 非用户原话");
    analysis.append(el("p", "source-text", group.analysis)); source.append(analysis);
  }
  if (group.references.length) {
    const refs = details(`角色与视觉参考图 · ${group.references.length} 张`);
    refs.append(sourceStrip(group.references)); source.append(refs);
  }
  if (group.warnings.length) {
    const warnings = details(`记录提示 · ${group.warnings.length}`);
    warnings.className = "warnings";
    group.warnings.forEach(warning => warnings.append(el("p", "", warning)));
    source.append(warnings);
  }
  panel.append(source);
  const toolbar = el("div", "toolbar");
  toolbar.append(el("h2", "", `方案与作品 · ${group.proposals.length}`));
  const controls = el("div", "controls");
  const modes = [];
  for (const [mode, label] of [["grid", "▦ 网格"], ["list", "☰ 列表"]]) {
    const control = button(label, () => {
      view = mode; panel.classList.toggle("list", view === "list");
      modes.forEach(([key, node]) => node.setAttribute("aria-pressed", String(key === view)));
    });
    control.setAttribute("aria-pressed", String(view === mode));
    modes.push([mode, control]); controls.append(control);
  }
  toolbar.append(controls); panel.append(toolbar);
  panel.classList.toggle("list", view === "list");
  group.proposals.forEach(proposal => {
    if (!proposal.selected) {
      const folded = details(""); folded.className = "unselected";
      folded.firstChild.append(el("span", "letter", proposal.choice), el("span", "", proposal.title), badge("未生成"));
      folded.append(el("p", "", proposal.scene), el("p", "muted", proposal.detail)); panel.append(folded); return;
    }
    const section = el("section", "proposal");
    const heading = el("div", "proposal-heading");
    const passed = proposal.images.filter(image => image.status === "passed").length;
    heading.append(el("span", "letter", proposal.choice), el("h3", "", proposal.title), badge(`${passed} / ${proposal.planned} 张已通过`));
    section.append(heading, el("p", "proposal-desc", [proposal.scene, proposal.detail].filter(Boolean).join(" · ")));
    const cards = el("div", "cards"), collection = [];
    proposal.images.forEach(image => cards.append(card(image, collection)));
    section.append(cards); panel.append(section);
  });
}
const hero = el("section", "hero"), introduction = el("div");
introduction.append(el("div", "eyebrow", "A COLLECTION OF LITTLE IDEAS"), el("h1", "", data.skill === "comic" ? "鲸鱼娘 · 漫画图册" : "鲸鱼娘 · 角色图册"), el("p", "", "从一份素材，到一个灵感，再到一张作品。"));
const stats = el("div", "stats");
for (const [label, value] of [["素材 / 主题", data.groups.length], ["交付成品", data.groups.reduce((sum, group) => sum + group.passed, 0)], ["产图次数", data.groups.reduce((sum, group) => sum + group.calls, 0)]]) {
  const stat = el("div", "stat"); stat.append(el("strong", "", String(value).padStart(2, "0")), el("span", "", label)); stats.append(stat);
}
hero.append(introduction, stats); app.append(hero);
const tabs = el("nav", "tabs"); tabs.setAttribute("role", "tablist"); tabs.setAttribute("aria-label", "素材组或创作主题");
const panel = el("div"); panel.id = "group-panel"; panel.setAttribute("role", "tabpanel");
const tabButtons = data.groups.map((group, index) => {
  const tab = button(`${String(index + 1).padStart(2,"0")} / ${group.title}`, () => selectGroup(index));
  tab.id = `group-tab-${index}`; tab.setAttribute("role", "tab"); tab.setAttribute("aria-controls", panel.id);
  tab.addEventListener("keydown", event => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === "Home" ? 0 : event.key === "End" ? data.groups.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + data.groups.length) % data.groups.length;
    selectGroup(next); tabButtons[next].focus();
  });
  tabs.append(tab); return tab;
});
function selectGroup(index) {
  activeGroup = index;
  tabButtons.forEach((tab, i) => { tab.setAttribute("aria-selected", String(i === index)); tab.tabIndex = i === index ? 0 : -1; });
  panel.setAttribute("aria-labelledby", tabButtons[index].id);
  renderGroup(data.groups[index], panel);
}
app.append(tabs, panel); selectGroup(activeGroup);
function updateLightbox() {
  const entry = currentPictures[currentIndex];
  largeImage.src = entry.picture.src; largeImage.alt = entry.picture.label;
  document.getElementById("lightbox-title").textContent = entry.picture.label;
  document.getElementById("image-position").textContent = `${currentIndex + 1} / ${currentPictures.length} · ${entry.picture.width} × ${entry.picture.height}`;
  document.getElementById("previous").disabled = currentIndex === 0;
  document.getElementById("next").disabled = currentIndex === currentPictures.length - 1;
  stage.classList.remove("original"); stage.scrollTop = 0; stage.scrollLeft = 0;
  document.getElementById("size-toggle").textContent = "原始尺寸";
  info.replaceChildren(entry.detailFactory ? entry.detailFactory() : el("p", "note", "输入素材或视觉参考图"));
}
function move(delta) {
  const next = currentIndex + delta;
  if (next >= 0 && next < currentPictures.length) { currentIndex = next; updateLightbox(); }
}
document.getElementById("previous").onclick = () => move(-1);
document.getElementById("next").onclick = () => move(1);
document.getElementById("close-lightbox").onclick = () => dialog.close();
document.getElementById("size-toggle").onclick = event => {
  stage.classList.toggle("original");
  event.currentTarget.textContent = stage.classList.contains("original") ? "适应窗口" : "原始尺寸";
};
document.getElementById("info-toggle").onclick = event => {
  info.hidden = !info.hidden; event.currentTarget.setAttribute("aria-expanded", String(!info.hidden));
};
dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
dialog.addEventListener("close", () => { document.body.style.overflow = ""; opener?.focus(); });
dialog.addEventListener("keydown", event => {
  if (event.target.tagName === "TEXTAREA") return;
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") { event.preventDefault(); move(event.key === "ArrowLeft" ? -1 : 1); }
});
