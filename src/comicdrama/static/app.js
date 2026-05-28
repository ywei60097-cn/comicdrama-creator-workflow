const sampleText = `# 雨夜来信

林舟在旧城南街的钟楼下等了三小时，雨水顺着黑伞边缘落成一串细线。午夜十二点，一封没有署名的信从钟楼门缝里滑出来，信纸上只有一句话：“别相信明天早上的自己。”

他刚想离开，青梅竹马的苏晴从巷口跑来，手里握着一枚裂开的玉佩。苏晴喘着气说：“我在你父亲留下的书房里找到了这个，墙后面还有一扇门。”

林舟想起父亲失踪前的最后一通电话。电话里，父亲让他无论如何都不要回老宅。可现在，信、玉佩和苏晴的出现，把他推回了那个被封存十年的夜晚。

老宅书房里满是灰尘，墙后的暗门通向地下。地下室中央摆着一台仍在运行的旧式放映机，银幕上正播放着林舟明天清晨走进钟楼的画面。

苏晴低声说：“如果这是真的，我们还有六个小时改变结局。”`;

const state = {
  activeTab: "overview",
  result: null,
};

const els = {
  title: document.querySelector("#titleInput"),
  source: document.querySelector("#sourceText"),
  rights: document.querySelector("#rightsConfirm"),
  style: document.querySelector("#styleSelect"),
  format: document.querySelector("#formatSelect"),
  pov: document.querySelector("#povSelect"),
  detail: document.querySelector("#detailSelect"),
  ratio: document.querySelector("#ratioInput"),
  ratioValue: document.querySelector("#ratioValue"),
  file: document.querySelector("#fileInput"),
  fileMeta: document.querySelector("#fileMeta"),
  upload: document.querySelector("#uploadButton"),
  run: document.querySelector("#runButton"),
  download: document.querySelector("#downloadButton"),
  loadSample: document.querySelector("#loadSample"),
  status: document.querySelector("#status"),
  resultBody: document.querySelector("#resultBody"),
  tabs: document.querySelectorAll(".tab"),
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
  if (!["txt", "md"].includes(extension)) {
    els.file.value = "";
    els.fileMeta.textContent = "仅支持 TXT / MD";
    setStatus("附件格式不支持", "running");
    return;
  }
  try {
    const text = await file.text();
    els.source.value = text;
    els.title.value = stripExtension(file.name);
    els.fileMeta.textContent = `${file.name} · ${formatBytes(file.size)}`;
    state.result = null;
    els.download.disabled = true;
    setStatus("附件已导入", "done");
    render();
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

  setStatus("Running", "running");
  els.run.disabled = true;
  try {
    const response = await fetch("/api/v1/workflows/comicdrama", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document: {
          title: els.title.value || "Untitled Novel",
          source_format: "md",
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
    els.resultBody.innerHTML = '<div class="empty-state">点击运行后查看精简小说、剧本和分镜结果。</div>';
    return;
  }
  const renderers = {
    overview: renderOverview,
    characters: renderCharacters,
    script: renderScript,
    storyboard: renderStoryboard,
    json: renderJson,
  };
  els.resultBody.innerHTML = renderers[state.activeTab]();
}

function renderOverview() {
  const result = state.result;
  return `
    <div class="summary-grid">
      <div class="metric"><strong>${result.analysis.story_beats.length}</strong><span>剧情节拍</span></div>
      <div class="metric"><strong>${result.analysis.characters.length}</strong><span>人物</span></div>
      <div class="metric"><strong>${result.storyboard.length}</strong><span>分镜行</span></div>
    </div>
    <div class="prose">
      <h3>故事梗概</h3>
      ${paragraphs(result.analysis.synopsis)}
      <h3>精简小说</h3>
      ${paragraphs(result.simplified_novel)}
      <h3>提示</h3>
      <ul>${result.notices.map((notice) => `<li>${escapeHtml(notice)}</li>`).join("")}</ul>
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
  return state.result.script.map((block) => `
    <div class="script-block">
      <strong>${escapeHtml(block.block_type)}</strong>
      ${block.speaker ? `${escapeHtml(block.speaker)}：` : ""}
      ${escapeHtml(block.content)}
    </div>
  `).join("");
}

function renderStoryboard() {
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
