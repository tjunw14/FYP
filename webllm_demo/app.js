import { CreateMLCEngine, prebuiltAppConfig } from "https://esm.run/@mlc-ai/web-llm";

const $ = (id) => document.getElementById(id);
const state = {
  engine: null,
  selectedModel: null,
  selectedTarget: null,
  seedsValidated: false,
  lastSeedInfo: null,
  pollTimer: null,
  latestEvidence: null,
};

const els = {
  backendStatus: $("backendStatus"),
  modelSelect: $("modelSelect"),
  loadModelBtn: $("loadModelBtn"),
  modelStatus: $("modelStatus"),
  targetSelect: $("targetSelect"),
  targetDetails: $("targetDetails"),
  promptBox: $("promptBox"),
  generateBtn: $("generateBtn"),
  generatedSeeds: $("generatedSeeds"),
  validateBtn: $("validateBtn"),
  validationStatus: $("validationStatus"),
  seedTableBody: $("seedTableBody"),
  durationSelect: $("durationSelect"),
  dictionaryToggle: $("dictionaryToggle"),
  startBtn: $("startBtn"),
  stopBtn: $("stopBtn"),
  runState: $("runState"),
  progressBar: $("progressBar"),
  consoleBox: $("consoleBox"),
  analyseBtn: $("analyseBtn"),
  analysisBox: $("analysisBox"),
  exportBtn: $("exportBtn"),
  reportStatus: $("reportStatus"),
};

const metricIds = [
  "runtimeMetric", "execsMetric", "execRateMetric", "corpusMetric",
  "coverageMetric", "edgesMetric", "stabilityMetric", "timeoutsMetric",
  "crashesMetric", "hangsMetric", "depthMetric", "favoredMetric",
];

function api(path, options = {}) {
  return fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  });
}

function setStep(index, status) {
  const step = document.querySelector(`[data-step="${index}"]`);
  if (!step) return;
  step.classList.toggle("active", status === "active");
  step.classList.toggle("done", status === "done");
}

function modelId(entry) {
  return entry.model_id || entry.model || entry.id || String(entry);
}

function populateModels() {
  const ids = prebuiltAppConfig.model_list.map(modelId).filter(Boolean);
  for (const id of ids) {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = id;
    els.modelSelect.appendChild(option);
  }
  const preferred = ids.find((id) => /qwen.*0\.5b.*instruct.*mlc/i.test(id))
    || ids.find((id) => /qwen.*1\.5b.*instruct.*mlc/i.test(id))
    || ids[0];
  if (preferred) els.modelSelect.value = preferred;
}

async function checkBackend() {
  try {
    const health = await api("/api/health");
    els.backendStatus.textContent = health.ok ? "BACKEND CONNECTED" : "BACKEND UNKNOWN";
    els.backendStatus.className = "status-pill ok";
  } catch (error) {
    els.backendStatus.textContent = "BACKEND NOT CONNECTED";
    els.backendStatus.className = "status-pill bad";
    els.validationStatus.textContent = "Start the local Python workbench server instead of a plain http.server.";
  }
}

async function loadTargets() {
  try {
    const data = await api("/api/targets");
    els.targetSelect.innerHTML = "";
    for (const target of data.targets || []) {
      const option = document.createElement("option");
      option.value = target.target_id;
      option.textContent = `${target.target_id} — ${target.decoder_function}`;
      option.dataset.target = JSON.stringify(target);
      els.targetSelect.appendChild(option);
    }
    updateTargetDetails();
  } catch (error) {
    els.targetDetails.textContent = `Unable to load target configuration: ${error.message}`;
  }
}

function updateTargetDetails() {
  const option = els.targetSelect.selectedOptions[0];
  if (!option) return;
  const target = JSON.parse(option.dataset.target || "{}");
  state.selectedTarget = target;
  els.targetDetails.textContent = `${target.description || "Open5GS target"}\nFunction: ${target.decoder_function || "-"}\nHarness: ${target.harness_source || "-"}`;
  setStep(2, "done");
  setStep(3, "active");
}

async function loadModel() {
  if (!navigator.gpu) {
    els.modelStatus.textContent = "WebGPU is unavailable. Use a recent Chrome/Edge browser with hardware acceleration enabled.";
    return;
  }
  state.selectedModel = els.modelSelect.value;
  els.loadModelBtn.disabled = true;
  els.modelStatus.textContent = `Loading ${state.selectedModel}...`;
  try {
    state.engine = await CreateMLCEngine(state.selectedModel, {
      initProgressCallback: (progress) => {
        const message = typeof progress === "string" ? progress : (progress.text || JSON.stringify(progress));
        els.modelStatus.textContent = message;
      },
    });
    els.modelStatus.textContent = `Loaded locally in browser: ${state.selectedModel}`;
    els.generateBtn.disabled = false;
    setStep(1, "done");
    setStep(2, "active");
  } catch (error) {
    els.modelStatus.textContent = `Model load failed: ${error.message || error}`;
    els.loadModelBtn.disabled = false;
  }
}

function extractSeedLines(text) {
  const lines = [];
  const seen = new Set();
  for (const raw of text.split(/\r?\n/)) {
    const match = raw.trim().match(/^seed[_-]?(\d{1,3})\s*:\s*([0-9a-fA-F]{4,8192})\s*$/i);
    if (!match) continue;
    let hex = match[2].toLowerCase();
    if (hex.length % 2) continue;
    if (seen.has(hex)) continue;
    seen.add(hex);
    lines.push(`seed_${String(lines.length + 1).padStart(3, "0")}: ${hex}`);
  }
  return lines.join("\n");
}

async function generateSeeds() {
  if (!state.engine) return;
  els.generateBtn.disabled = true;
  els.validationStatus.textContent = "Generating candidate seeds locally with WebLLM...";
  try {
    const reply = await state.engine.chat.completions.create({
      messages: [
        {
          role: "system",
          content: "You generate defensive fuzzing seed inputs only. Output only labelled compact hexadecimal seed lines. Do not provide exploit instructions or prose.",
        },
        { role: "user", content: els.promptBox.value },
      ],
      temperature: 0.2,
      max_tokens: 1000,
    });
    const raw = reply.choices?.[0]?.message?.content || "";
    const parsed = extractSeedLines(raw);
    els.generatedSeeds.value = parsed || raw;
    state.seedsValidated = false;
    els.validateBtn.disabled = !parsed;
    els.startBtn.disabled = true;
    els.validationStatus.textContent = parsed
      ? `WebLLM generated ${parsed.split(/\r?\n/).length} parseable seed line(s). Review them, then validate.`
      : "WebLLM returned output, but no strict seed lines were parsed. Edit the output into 'seed_001: <hex>' format.";
    setStep(3, "done");
    setStep(4, "active");
  } catch (error) {
    els.validationStatus.textContent = `Generation failed: ${error.message || error}`;
  } finally {
    els.generateBtn.disabled = false;
  }
}

function renderSeedPreview(preview) {
  els.seedTableBody.innerHTML = "";
  for (const seed of preview || []) {
    const tr = document.createElement("tr");
    for (const value of [seed.filename, `${seed.size_bytes} B`, seed.hex]) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    }
    els.seedTableBody.appendChild(tr);
  }
}

async function validateSeeds() {
  const seedText = extractSeedLines(els.generatedSeeds.value);
  if (!seedText) {
    els.validationStatus.textContent = "No strict seed lines to validate.";
    return;
  }
  els.validateBtn.disabled = true;
  els.validationStatus.textContent = "Validating binary seeds and preparing a clean AFL++ corpus...";
  try {
    const info = await api("/api/seeds/validate", {
      method: "POST",
      body: JSON.stringify({ seed_text: seedText }),
    });
    state.seedsValidated = true;
    state.lastSeedInfo = info;
    renderSeedPreview(info.preview);
    els.validationStatus.textContent = `Validated ${info.clean_seed_count} unique binary seed(s). Clean corpus ready.`;
    els.startBtn.disabled = false;
    setStep(4, "done");
    setStep(5, "active");
  } catch (error) {
    els.validationStatus.textContent = `Validation failed: ${error.message}`;
  } finally {
    els.validateBtn.disabled = false;
  }
}

function value(stats, key, fallback = "—") {
  const item = stats?.[key];
  return item === undefined || item === null || item === "" ? fallback : item;
}

function formatSeconds(total) {
  total = Number(total || 0);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return [h, m, s].map((n) => String(n).padStart(2, "0")).join(":");
}

function updateMetrics(status) {
  const stats = status.stats || {};
  $("runtimeMetric").textContent = formatSeconds(value(stats, "run_time", status.elapsed_seconds || 0));
  $("execsMetric").textContent = value(stats, "execs_done");
  $("execRateMetric").textContent = value(stats, "execs_per_sec");
  $("corpusMetric").textContent = value(stats, "corpus_count");
  $("coverageMetric").textContent = value(stats, "bitmap_cvg");
  const edges = value(stats, "edges_found");
  const totalEdges = value(stats, "total_edges", "?");
  $("edgesMetric").textContent = `${edges} / ${totalEdges}`;
  $("stabilityMetric").textContent = value(stats, "stability");
  $("timeoutsMetric").textContent = value(stats, "total_tmouts", value(stats, "total_tmout"));
  $("crashesMetric").textContent = String(status.crash_files ?? value(stats, "saved_crashes", 0));
  $("hangsMetric").textContent = String(status.hang_files ?? value(stats, "saved_hangs", 0));
  $("depthMetric").textContent = value(stats, "max_depth");
  $("favoredMetric").textContent = value(stats, "corpus_favored");

  const elapsed = Number(status.elapsed_seconds || 0);
  const duration = Number(status.requested_duration_seconds || 1);
  els.progressBar.style.width = `${Math.min(100, (elapsed / duration) * 100)}%`;
  els.runState.textContent = String(status.state || "idle").toUpperCase();
  els.consoleBox.textContent = (status.log_tail || []).join("\n") || "Waiting for AFL++ output...";
  els.consoleBox.scrollTop = els.consoleBox.scrollHeight;

  const running = Boolean(status.running);
  els.startBtn.disabled = running || !state.seedsValidated;
  els.stopBtn.disabled = !running;
  els.analyseBtn.disabled = running || !state.engine || !stats.run_time;
  if (!running && ["completed", "stopped", "failed"].includes(status.state)) {
    setStep(5, "done");
    setStep(6, "done");
    setStep(7, "active");
  }
}

async function pollStatus() {
  try {
    const status = await api("/api/fuzz/status");
    state.latestEvidence = status;
    updateMetrics(status);
    if (!status.running && state.pollTimer) {
      clearInterval(state.pollTimer);
      state.pollTimer = null;
    }
  } catch (error) {
    els.consoleBox.textContent = `Status error: ${error.message}`;
  }
}

async function startFuzzing() {
  if (!state.seedsValidated) return;
  els.startBtn.disabled = true;
  els.consoleBox.textContent = "Starting local Docker/AFL++ session...";
  setStep(5, "active");
  try {
    const status = await api("/api/fuzz/start", {
      method: "POST",
      body: JSON.stringify({
        target_id: els.targetSelect.value,
        duration_seconds: Number(els.durationSelect.value),
        dictionary_enabled: els.dictionaryToggle.checked,
      }),
    });
    updateMetrics(status);
    setStep(5, "done");
    setStep(6, "active");
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = setInterval(pollStatus, 2000);
  } catch (error) {
    els.consoleBox.textContent = `Unable to start fuzzing: ${error.message}`;
    els.startBtn.disabled = false;
  }
}

async function stopFuzzing() {
  els.stopBtn.disabled = true;
  try {
    const status = await api("/api/fuzz/stop", { method: "POST", body: "{}" });
    updateMetrics(status);
    setTimeout(pollStatus, 1200);
  } catch (error) {
    els.consoleBox.textContent += `\nStop error: ${error.message}`;
  }
}

async function analyseWithWebLLM() {
  if (!state.engine) return;
  els.analyseBtn.disabled = true;
  els.analysisBox.value = "Preparing guarded evidence prompt...";
  try {
    const bundle = await api("/api/triage/evidence");
    state.latestEvidence = bundle.evidence;
    const reply = await state.engine.chat.completions.create({
      messages: [
        {
          role: "system",
          content: "You are a defensive software-testing assistant. Analyse only supplied evidence. Never label a fuzzing crash as a confirmed vulnerability without reproduction, sanitizer/source evidence, and human verification. Do not provide exploitation instructions.",
        },
        { role: "user", content: bundle.prompt },
      ],
      temperature: 0.2,
      max_tokens: 1000,
    });
    els.analysisBox.value = reply.choices?.[0]?.message?.content || "No analysis returned.";
    els.exportBtn.disabled = false;
    setStep(7, "done");
    setStep(8, "active");
  } catch (error) {
    els.analysisBox.value = `Analysis failed: ${error.message}`;
  } finally {
    els.analyseBtn.disabled = false;
  }
}

function downloadText(filename, content) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function exportReport() {
  els.exportBtn.disabled = true;
  els.reportStatus.textContent = "Building report from recorded evidence and guarded WebLLM analysis...";
  try {
    const result = await api("/api/report/export", {
      method: "POST",
      body: JSON.stringify({ analysis: els.analysisBox.value }),
    });
    downloadText("webllm_open5gs_fuzzing_report.md", result.markdown);
    els.reportStatus.textContent = `Report saved locally at ${result.path} and downloaded as Markdown.`;
    setStep(8, "done");
  } catch (error) {
    els.reportStatus.textContent = `Report export failed: ${error.message}`;
  } finally {
    els.exportBtn.disabled = false;
  }
}

populateModels();
checkBackend();
loadTargets();
els.targetSelect.addEventListener("change", updateTargetDetails);
els.loadModelBtn.addEventListener("click", loadModel);
els.generateBtn.addEventListener("click", generateSeeds);
els.validateBtn.addEventListener("click", validateSeeds);
els.startBtn.addEventListener("click", startFuzzing);
els.stopBtn.addEventListener("click", stopFuzzing);
els.analyseBtn.addEventListener("click", analyseWithWebLLM);
els.exportBtn.addEventListener("click", exportReport);

for (const id of metricIds) $(id).textContent = "—";
setStep(1, "active");
pollStatus();
