const workflowModel = [
  ["upload", "Upload received"],
  ["save", "Save file"],
  ["validate", "Validate DOCX"],
  ["redact", "Run redactor"],
  ["output", "Create output"],
  ["download", "Prepare download"],
];

const state = {
  file: null,
  steps: new Map(),
};

const fileInput = document.querySelector("#fileInput");
const dropzone = document.querySelector("#dropzone");
const fileCard = document.querySelector("#fileCard");
const runButton = document.querySelector("#runButton");
const workflow = document.querySelector("#workflow");
const terminal = document.querySelector("#terminal");
const summary = document.querySelector("#summary");
const downloadLink = document.querySelector("#downloadLink");
const serviceStatus = document.querySelector("#serviceStatus");
const resultMeta = document.querySelector("#resultMeta");
const resultPreview = document.querySelector("#resultPreview");

function line(message) {
  const stamp = new Date().toLocaleTimeString();
  terminal.textContent += `\n[${stamp}] ${message}`;
  terminal.scrollTop = terminal.scrollHeight;
}

function setNode(id, status, detail = "") {
  state.steps.set(id, { status, detail });
  renderWorkflow();
}

function renderWorkflow() {
  workflow.innerHTML = "";
  for (const [id, label] of workflowModel) {
    const step = state.steps.get(id) || { status: "idle", detail: "Waiting" };
    const node = document.createElement("article");
    node.className = `node ${step.status}`;
    node.innerHTML = `
      <span class="node-status">${step.status}</span>
      <div class="node-title">${label}</div>
      <div class="node-detail">${step.detail || "Waiting"}</div>
    `;
    workflow.appendChild(node);
  }
}

function renderSummary(data) {
  if (!data) {
    summary.innerHTML = '<div class="summary-empty">No run yet.</div>';
    return;
  }
  const counts = data.summary.redactions || {};
  const items = [
    ["Changed paragraphs", data.summary.changed_paragraphs],
    ["Unique replacements", data.summary.unique_replacements],
    ["Total redactions", Object.values(counts).reduce((a, b) => a + b, 0)],
    ["PII types found", Object.keys(counts).length],
    ["Job ID", data.jobId],
  ];
  for (const [key, value] of Object.entries(counts)) {
    items.push([key, value]);
  }
  summary.innerHTML = items.map(([label, value]) => `
    <div class="summary-item">
      <div class="summary-label">${label}</div>
      <div class="summary-value">${value}</div>
    </div>
  `).join("");
}

function renderResult(data) {
  if (!data) {
    resultMeta.textContent = "No redacted document yet.";
    resultPreview.textContent = "Upload a DOCX and run redaction to see the output here.";
    return;
  }
  resultMeta.textContent = `Output: ${data.outputPath} | Download: ${data.downloadUrl}`;
  const lines = data.preview?.lines || [];
  const suffix = data.preview?.truncated ? "\n\n... preview truncated. Download the DOCX for the full result." : "";
  resultPreview.textContent = lines.length
    ? `${lines.join("\n")}${suffix}`
    : "The redacted DOCX was generated, but no paragraph text was extracted for preview.";
}

function selectFile(file) {
  state.file = file || null;
  downloadLink.classList.add("hidden");
  renderResult(null);
  if (!state.file) {
    fileCard.textContent = "No file selected";
    runButton.disabled = true;
    return;
  }
  fileCard.textContent = `${state.file.name} (${Math.round(state.file.size / 1024).toLocaleString()} KB)`;
  runButton.disabled = !state.file.name.toLowerCase().endsWith(".docx");
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    serviceStatus.textContent = "Backend ready";
    serviceStatus.className = "status-pill ok";
  } catch (error) {
    serviceStatus.textContent = "Backend unavailable";
    serviceStatus.className = "status-pill error";
  }
}

async function runRedaction() {
  if (!state.file) return;
  state.steps.clear();
  renderWorkflow();
  renderSummary(null);
  renderResult(null);
  terminal.textContent = "Starting local redaction request...";
  downloadLink.classList.add("hidden");
  runButton.disabled = true;
  setNode("upload", "running", "Browser is sending the selected DOCX.");

  const formData = new FormData();
  formData.append("document", state.file);

  try {
    const response = await fetch("/api/redact", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    for (const step of data.steps) {
      setNode(step.id, step.status, step.detail);
    }
    terminal.textContent = data.terminal.join("\n");
    renderSummary(data);
    renderResult(data);
    downloadLink.href = data.downloadUrl;
    downloadLink.textContent = `Download ${data.outputName}`;
    downloadLink.classList.remove("hidden");
    line("Browser received a successful backend response.");
  } catch (error) {
    setNode("upload", "error", error.message);
    line(`ERROR: ${error.message}`);
  } finally {
    runButton.disabled = !state.file;
  }
}

fileInput.addEventListener("change", () => selectFile(fileInput.files[0]));
runButton.addEventListener("click", runRedaction);

for (const eventName of ["dragenter", "dragover"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragging");
  });
}

dropzone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  selectFile(file);
});

renderWorkflow();
checkHealth();
