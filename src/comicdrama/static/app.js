const sampleText = `# 雨夜来信

林舟在旧城南街的钟楼下等了三小时，雨水顺着黑伞边缘落成一串细线。午夜十二点，一封没有署名的信从钟楼门缝里滑出来，信纸上只有一句话：“别相信明天早上的自己。”

他刚想离开，青梅竹马的苏晴从巷口跑来，手里握着一枚裂开的玉佩。苏晴喘着气说：“我在你父亲留下的书房里找到了这个，墙后面还有一扇门。”

林舟想起父亲失踪前的最后一通电话。电话里，父亲让他无论如何都不要回老宅。可现在，信、玉佩和苏晴的出现，把他推回了那个被封存十年的夜晚。

老宅书房里满是灰尘，墙后的暗门通向地下。地下室中央摆着一台仍在运行的旧式放映机，银幕上正播放着林舟明天清晨走进钟楼的画面。

苏晴低声说：“如果这是真的，我们还有六个小时改变结局。”`;

const state = {
  activeTab: "overview",
  result: null,
  sourceFormat: "md",
  currentPreset: "all",
  enabledFeatures: ["simplify", "extract_elements", "convert_script", "batch_process", "assist_adaptation"],
};

const supportedUploadExtensions = new Set(["txt", "md", "markdown", "pdf", "docx", "html", "htm", "csv", "json", "rtf", "xlsx"]);
const presetLabels = {
  all: "全流程",
  simplify: "小说简炼",
  extract: "人物场景提取",
  script: "剧本转换",
  batch: "批量处理",
  assist: "辅助创作",
};

const presetTabs = {
  all: ["overview", "characters", "script", "storyboard", "batch", "assist", "json"],
  simplify: ["overview", "json"],
  extract: ["characters", "json"],
  script: ["script", "storyboard", "characters", "json"],
  batch: ["batch", "json"],
  assist: ["assist", "characters", "json"],
};

const els = {
  title: document.querySelector("#titleInput"),
  source: document.querySelector("#sourceText"),
  characterReference: document.querySelector("#characterReference"),
  rights: document.querySelector("#rightsConfirm"),
  style: document.querySelector("#styleSelect"),
  format: document.querySelector("#formatSelect"),
  pov: document.querySelector("#povSelect"),
  detail: document.querySelector("#detailSelect"),
  ratio: document.querySelector("#ratioInput"),
  ratioValue: document.querySelector("#ratioValue"),
  chapterRange: document.querySelector("#chapterRangeInput"),
  targetChapter: document.querySelector("#targetChapterInput"),
  targetChars: document.querySelector("#targetCharsInput"),
  outputFormat: document.querySelector("#outputFormatSelect"),
  file: document.querySelector("#fileInput"),
  fileMeta: document.querySelector("#fileMeta"),
  upload: document.querySelector("#uploadButton"),
  run: document.querySelector("#runButton"),
  download: document.querySelector("#downloadButton"),
  loadSample: document.querySelector("#loadSample"),
  status: document.querySelector("#status"),
  paramHint: document.querySelector("#paramHint"),
  params: document.querySelectorAll("[data-param]"),
  resultBody: document.querySelector("#resultBody"),
  tabs: document.querySelectorAll(".tab"),
  modes: document.querySelectorAll(".mode-button"),
};

els.source.value = sampleText;

els.ratio.addEventListener("input", () => {
  els.ratioValue.textContent = `${els.ratio.value}%`;
});

els.loadSample.addEventListener("click", () => {
  els.title.value = "雨夜来信";
  els.source.value = sampleText;
  els.file.value = "";
  els.fileMeta.textContent = "已载入示例";
  state.sourceFormat = "md";
});

els.upload.addEventListener("click", () => {
  els.file.click();
});

els.file.addEventListener("change", async () => {
  const file = els.file.files && els.file.files[0];
  if (!file) {
    els.fileMeta.textContent = "未选择附件";
    return;
  }
  const extension = file.name.split(".").pop().toLowerCase();
  if (!supportedUploadExtensions.has(extension)) {
    els.file.value = "";
    els.fileMeta.textContent = "格式不支持";
    setStatus("附件格式不支持", "running");
    return;
  }
  try {
    setStatus("读取附件", "running");
    const extracted = await extractServerSide(file);
    els.source.value = extracted.text;
    els.title.value = extracted.title;
    state.sourceFormat = extracted.source_format || extension;
    els.fileMeta.textContent = [
      file.name,
      formatBytes(file.size),
      extracted.pages ? `${extracted.pages} 页` : "",
      extracted.sheets ? `${extracted.sheets} 个表` : "",
    ].filter(Boolean).join(" · ");
    state.result = null;
    els.download.disabled = true;
    setStatus(extracted.text.trim() ? "附件已导入" : "需 OCR", extracted.text.trim() ? "done" : "running");
    render();
    if (extracted.notices && extracted.notices.length) {
      els.resultBody.innerHTML = `<div class="empty-state">${escapeHtml(extracted.notices.join(" "))}</div>`;
    }
  } catch (error) {
    els.fileMeta.textContent = "附件读取失败";
    setStatus("读取失败", "running");
  }
});

els.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    state.activeTab = tab.dataset.tab;
    els.tabs.forEach((item) => item.classList.toggle("active", item === tab));
    render();
  });
});

els.modes.forEach((mode) => {
  mode.addEventListener("click", () => {
    applyPreset(mode.dataset.preset);
    els.modes.forEach((item) => item.classList.toggle("active", item === mode));
  });
});

els.run.addEventListener("click", async () => {
  await runWorkflow();
});

els.download.addEventListener("click", () => {
  if (!state.result) return;
  const blob = new Blob([JSON.stringify(state.result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${safeName(els.title.value || "comicdrama")}-workflow.json`;
  link.click();
  URL.revokeObjectURL(url);
});

async function runWorkflow() {
  const text = els.source.value.trim();
  if (!text) {
    setStatus("请输入素材", "running");
    return;
  }
  if (!els.rights.checked) {
    setStatus("需确认授权", "running");
    return;
  }
  const enabledFeatures = selectedFeatures();
  if (!enabledFeatures.length) {
    setStatus("请选择功能", "running");
    return;
  }

  setStatus("Running", "running");
  els.run.disabled = true;
  try {
    const response = await fetch("/api/v1/workflows/comicdrama", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document: {
          title: els.title.value || "Untitled Novel",
          source_format: state.sourceFormat,
          text,
        },
        config: {
          style: els.style.value,
          target_format: els.format.value,
          dialogue_retention_ratio: Number(els.ratio.value) / 100,
          narration_pov: els.pov.value,
          storyboard_detail: els.detail.value,
          episode_length: "short",
          copyright_confirmation: els.rights.checked,
          enabled_features: enabledFeatures,
          character_reference: els.characterReference.value.trim() || null,
          source_chapter_range: els.chapterRange.value.trim() || null,
          target_chapter_count: Number(els.targetChapter.value || 3),
          target_chars_per_chapter: Number(els.targetChars.value || 1000),
          length_tolerance_ratio: 0.15,
          output_format: els.outputFormat.value,
        },
      }),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `HTTP ${response.status}`);
    }
    state.result = await response.json();
    els.download.disabled = false;
    setStatus("Done", "done");
    render();
  } catch (error) {
    setStatus("Error", "running");
    els.resultBody.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  } finally {
    els.run.disabled = false;
  }
}

function render() {
  if (!state.result) {
    els.resultBody.innerHTML = `<div class="empty-state">点击“${escapeHtml(els.run.textContent)}”后查看${escapeHtml(presetLabels[state.currentPreset])}结果。</div>`;
    return;
  }
  const renderers = {
    overview: renderOverview,
    characters: renderCharacters,
    script: renderScript,
    storyboard: renderStoryboard,
    batch: renderBatch,
    assist: renderAssist,
    json: renderJson,
  };
  els.resultBody.innerHTML = renderers[state.activeTab]();
}

function renderOverview() {
  const result = state.result;
  return `
    <div class="overview-panel">
      <div class="overview-topline">
        <div class="feature-chips">
          ${featureChips(result.config.enabled_features)}
        </div>
        <div class="notice-strip">${result.notices.map((notice) => `<span>${escapeHtml(notice)}</span>`).join("")}</div>
      </div>
      <div class="summary-grid">
        <div class="metric"><strong>${result.analysis.story_beats.length}</strong><span>剧情节拍</span></div>
        <div class="metric"><strong>${result.analysis.characters.length}</strong><span>人物</span></div>
        <div class="metric"><strong>${result.storyboard.length}</strong><span>分镜行</span></div>
      </div>
      <div class="overview-preview-grid">
        <section class="preview-card">
          <div class="preview-head">
            <h3>故事梗概</h3>
          </div>
          <div class="preview-scroll prose">${paragraphs(result.analysis.synopsis)}</div>
        </section>
        ${result.simplified_novel ? `
          <section class="preview-card">
            <div class="preview-head">
              <h3>精简小说预览</h3>
              <span>完整内容见导出结果</span>
            </div>
            <div class="preview-scroll prose">${paragraphs(result.simplified_novel)}</div>
          </section>
        ` : ""}
      </div>
    </div>
  `;
}

function renderCharacters() {
  const { characters, elements } = state.result.analysis;
  return `
    <div class="prose">
      <h3>人物</h3>
      <div class="item-list">
        ${characters.map((item) => `
          <article class="item">
            <div class="item-title">${escapeHtml(item.name)}</div>
            <div class="muted">${escapeHtml(item.first_seen || "待补充人物首次出现信息")}</div>
          </article>
        `).join("") || '<div class="empty-state">暂无人物</div>'}
      </div>
      <h3>场景与道具</h3>
      <div class="item-list">
        ${elements.map((item) => `
          <article class="item">
            <div class="item-title">${escapeHtml(item.name)} · ${escapeHtml(item.kind)}</div>
            <div class="muted">${escapeHtml(item.description || "待补充描述")}</div>
          </article>
        `).join("") || '<div class="empty-state">暂无元素</div>'}
      </div>
    </div>
  `;
}

function renderScript() {
  if (!state.result.script.length) {
    return '<div class="empty-state">未选择剧本格式转换，或当前素材没有生成剧本。</div>';
  }
  return state.result.script.map((block) => `
    <div class="script-block">
      <strong>${escapeHtml(block.block_type)}</strong>
      ${block.speaker ? `${escapeHtml(block.speaker)}：` : ""}
      ${escapeHtml(block.content)}
    </div>
  `).join("");
}

function renderStoryboard() {
  if (!state.result.storyboard.length) {
    return '<div class="empty-state">需要选择剧本格式转换后才会生成分镜草案。</div>';
  }
  return `
    <table>
      <thead>
        <tr>
          <th>镜头</th>
          <th>场景</th>
          <th>机位</th>
          <th>画面/旁白</th>
          <th>对白</th>
        </tr>
      </thead>
      <tbody>
        ${state.result.storyboard.map((shot) => `
          <tr>
            <td>${escapeHtml(shot.shot_id)}</td>
            <td>${escapeHtml(shot.scene)}</td>
            <td>${escapeHtml(shot.camera)}</td>
            <td>${escapeHtml(shot.action || shot.narration)}</td>
            <td>${escapeHtml(shot.dialogue)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderBatch() {
  const items = state.result.batch_operations || [];
  if (!items.length) {
    return '<div class="empty-state">未选择批量内容处理。</div>';
  }
  return `
    <div class="item-list">
      ${items.map((item) => `
        <article class="item">
          <div class="item-title">${escapeHtml(item.action)} · ${escapeHtml(item.status)}</div>
          <div class="muted">${escapeHtml(item.detail)}</div>
        </article>
      `).join("")}
    </div>
  `;
}

function renderAssist() {
  const items = state.result.adaptation_suggestions || [];
  if (!items.length) {
    return '<div class="empty-state">未选择小说辅助创作。</div>';
  }
  return `
    <div class="item-list">
      ${items.map((item) => `
        <article class="item">
          <div class="item-title">${escapeHtml(item.category)} · ${escapeHtml(item.priority)}</div>
          <div class="muted">${escapeHtml(item.suggestion)}</div>
        </article>
      `).join("")}
    </div>
  `;
}

function renderJson() {
  return `<pre>${escapeHtml(JSON.stringify(state.result, null, 2))}</pre>`;
}

function paragraphs(text) {
  return text.split(/\n{1,}/).filter(Boolean).map((line) => `<p>${escapeHtml(line)}</p>`).join("");
}

function setStatus(text, className) {
  els.status.textContent = text;
  els.status.className = `status ${className || ""}`.trim();
}

function safeName(value) {
  return value.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/gi, "-").replace(/^-|-$/g, "") || "comicdrama";
}

function selectedFeatures() {
  return state.enabledFeatures;
}

function applyPreset(preset) {
  const presets = {
    simplify: ["simplify"],
    extract: ["extract_elements"],
    script: ["simplify", "extract_elements", "convert_script"],
    batch: ["batch_process"],
    assist: ["extract_elements", "assist_adaptation"],
    all: ["simplify", "extract_elements", "convert_script", "batch_process", "assist_adaptation"],
  };
  state.currentPreset = preset in presets ? preset : "all";
  state.enabledFeatures = presets[preset] || presets.all;
  updateVisibleParams(preset);
  updateVisibleTabs(preset);
  updateRunButton(preset);
  const targetTab = {
    simplify: "overview",
    extract: "characters",
    script: "script",
    batch: "batch",
    assist: "assist",
    all: "overview",
  }[preset] || "overview";
  setActiveTab(targetTab);
}

function updateVisibleTabs(preset) {
  const visible = presetTabs[preset] || presetTabs.all;
  els.tabs.forEach((tab) => {
    tab.classList.toggle("hidden", !visible.includes(tab.dataset.tab));
  });
  if (!visible.includes(state.activeTab)) {
    state.activeTab = visible[0];
  }
}

function updateRunButton(preset) {
  els.run.textContent = `运行${presetLabels[preset] || "工作流"}`;
}

function updateVisibleParams(preset) {
  const visible = {
    all: ["style", "script", "storyboard", "ratio", "simplify"],
    simplify: ["ratio", "simplify"],
    extract: [],
    script: ["style", "script", "storyboard", "ratio"],
    batch: [],
    assist: ["style"],
  }[preset] || ["style", "script", "storyboard", "ratio"];
  els.params.forEach((param) => {
    param.classList.toggle("hidden", !visible.includes(param.dataset.param));
  });
  els.paramHint.classList.toggle("hidden", visible.length > 0);
}

function setActiveTab(tabName) {
  state.activeTab = tabName;
  els.tabs.forEach((item) => item.classList.toggle("active", item.dataset.tab === tabName));
  render();
}

function featureChips(features) {
  const labels = {
    simplify: "小说精炼",
    extract_elements: "人物场景提取",
    convert_script: "剧本格式转换",
    batch_process: "批量内容处理",
    assist_adaptation: "小说辅助创作",
  };
  return (features || []).map((feature) => `<span class="chip">${escapeHtml(labels[feature] || feature)}</span>`).join("");
}

async function extractServerSide(file) {
  const response = await fetch("/api/v1/files/extract-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      filename: file.name,
      content_base64: await fileToBase64(file),
    }),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const value = String(reader.result || "");
      resolve(value.includes(",") ? value.split(",")[1] : value);
    };
    reader.onerror = () => reject(reader.error || new Error("Could not read file."));
    reader.readAsDataURL(file);
  });
}

function stripExtension(name) {
  return name.replace(/\.[^.]+$/, "") || "Untitled Novel";
}

function formatBytes(size) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

updateVisibleParams("all");
updateVisibleTabs("all");
updateRunButton("all");
