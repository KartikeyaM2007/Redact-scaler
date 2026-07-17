const workflowModel = [
  ["load", "Load DOCX"],
  ["preview", "Extract preview"],
  ["detect", "Detect PII"],
  ["redact", "Redact XML"],
  ["package", "Build DOCX"],
  ["download", "Prepare download"],
];

const piiLabels = ["name", "email", "phone", "company", "address", "ssn", "card", "dob", "ip"];
const fakeNames = ["Aarav Shah", "Arjun Singh", "Priya Menon", "Neha Kapoor", "Kabir Mehta"];
const replacements = new Map();
const state = { file: null, steps: new Map() };

const fileInput = document.querySelector("#fileInput");
const dropzone = document.querySelector("#dropzone");
const fileCard = document.querySelector("#fileCard");
const runButton = document.querySelector("#runButton");
const workflow = document.querySelector("#workflow");
const terminal = document.querySelector("#terminal");
const summary = document.querySelector("#summary");
const downloadLink = document.querySelector("#downloadLink");
const uploadedMeta = document.querySelector("#uploadedMeta");
const uploadedPreview = document.querySelector("#uploadedPreview");
const resultMeta = document.querySelector("#resultMeta");
const resultPreview = document.querySelector("#resultPreview");

function timestamp() {
  return new Date().toLocaleTimeString();
}

function log(message) {
  terminal.textContent += `\n[${timestamp()}] ${message}`;
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

function previewText(lines, max = 48) {
  const visible = lines.filter(Boolean).slice(0, max);
  const suffix = lines.length > max ? `\n\n... showing ${max} of ${lines.length} text lines. Download the DOCX for the full document.` : "";
  return visible.length ? `${visible.join("\n")}${suffix}` : "No paragraph text was extracted from this DOCX.";
}

function renderSummary(counts, changedNodes) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const items = [
    ["Text nodes changed", changedNodes],
    ["Total redactions", total],
    ["PII types found", Object.keys(counts).length],
  ];
  for (const key of Object.keys(counts).sort()) {
    items.push([key, counts[key]]);
  }
  summary.innerHTML = items.map(([label, value]) => `
    <div class="summary-item">
      <div class="summary-label">${label}</div>
      <div class="summary-value">${value}</div>
    </div>
  `).join("");
}

function selectFile(file) {
  state.file = file || null;
  downloadLink.classList.add("hidden");
  uploadedMeta.textContent = state.file ? "Selected" : "Waiting";
  resultMeta.textContent = "Waiting";
  uploadedPreview.textContent = state.file ? "Click Run redaction to extract the uploaded DOCX preview." : "Upload a DOCX to see the original text preview here.";
  resultPreview.textContent = "Run redaction to see the redacted output preview here.";
  summary.innerHTML = '<div class="summary-empty">No run yet.</div>';
  if (!state.file) {
    fileCard.textContent = "No file selected";
    runButton.disabled = true;
    return;
  }
  fileCard.textContent = `${state.file.name} (${Math.round(state.file.size / 1024).toLocaleString()} KB)`;
  runButton.disabled = !state.file.name.toLowerCase().endsWith(".docx");
}

function key(type, value) {
  return `${type}:${value.toLowerCase().replace(/\s+/g, " ").trim()}`;
}

function luhn(value) {
  const digits = value.replace(/\D/g, "");
  let total = 0;
  let alt = false;
  for (let i = digits.length - 1; i >= 0; i -= 1) {
    let n = Number(digits[i]);
    if (alt) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    total += n;
    alt = !alt;
  }
  return digits.length >= 13 && total % 10 === 0;
}

function replacement(type, value) {
  const id = key(type, value);
  if (replacements.has(id)) return replacements.get(id);
  const ordinal = replacements.size + 1;
  let fake = value;
  if (type === "email") fake = `contact${String(ordinal).padStart(3, "0")}@example.com`;
  if (type === "phone") fake = `+91 90000 ${String(ordinal).padStart(5, "0")}`;
  if (type === "ssn") fake = `900-01-${String(1000 + ordinal).slice(-4)}`;
  if (type === "card") fake = `4111 1111 1111 ${String(ordinal + 5).padStart(4, "0")}`;
  if (type === "ip") fake = `203.0.113.${Math.min(ordinal + 1, 254)}`;
  if (type === "dob") fake = `01/01/${1980 + (ordinal % 20)}`;
  if (type === "address") fake = `${100 + ordinal} Example Avenue, Sample City - 400001, India`;
  if (type === "company") fake = `Example Entity ${String(ordinal).padStart(3, "0")} Limited`;
  if (type === "name") fake = fakeNames[(ordinal - 1) % fakeNames.length];
  replacements.set(id, fake);
  return fake;
}

function detectAndReplace(text, counts) {
  const patterns = [
    ["email", /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi],
    ["ssn", /\b\d{3}-\d{2}-\d{4}\b/g],
    ["ip", /\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b/g],
    ["phone", /(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?)?\d{5}[\s-]?\d{5}\b/g],
    ["dob", /\b(?:Date of Birth|DOB|Birth Date)[:\s-]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b/gi],
    ["address", /\b(?:Registered Office|Address|Mailing address)[:\s-]*[^.]{10,120}(?:\d{3}\s?\d{3}|\d{5})[^.]*/gi],
    ["company", /\b[A-Z][A-Za-z&., ]{2,80}\s(?:Limited|Ltd|Private Limited|LLP|Inc|Corporation|Company)\b/g],
    ["name", /\b(?:Contact Person|Backup contact|Name|Mr\.|Ms\.|Mrs\.|Dr\.)[:\s-]*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b/g],
  ];
  let output = text;
  for (const [type, pattern] of patterns) {
    output = output.replace(pattern, (match) => {
      if (type === "phone" && match.replace(/\D/g, "").length < 10) return match;
      counts[type] = (counts[type] || 0) + 1;
      if (type === "dob") return match.replace(/\d{1,2}[/-]\d{1,2}[/-]\d{2,4}/, replacement(type, match));
      return replacement(type, match);
    });
  }
  output = output.replace(/\b(?:\d[ -]?){13,19}\b/g, (match) => {
    if (!luhn(match)) return match;
    counts.card = (counts.card || 0) + 1;
    return replacement("card", match);
  });
  return output;
}

async function collectText(zip, xmlFiles) {
  const lines = [];
  for (const file of xmlFiles) {
    const xml = await zip.file(file).async("text");
    const doc = new DOMParser().parseFromString(xml, "application/xml");
    for (const node of [...doc.getElementsByTagName("w:t")]) {
      const text = node.textContent.trim();
      if (text) lines.push(text);
    }
  }
  return lines;
}

async function runRedaction() {
  if (!state.file) return;
  replacements.clear();
  state.steps.clear();
  renderWorkflow();
  terminal.textContent = "Starting browser-side redaction request...";
  downloadLink.classList.add("hidden");
  runButton.disabled = true;
  const counts = {};
  let changedNodes = 0;

  try {
    setNode("load", "running", "Reading uploaded DOCX archive.");
    const buffer = await state.file.arrayBuffer();
    const zip = await JSZip.loadAsync(buffer);
    const xmlFiles = Object.keys(zip.files).filter((name) => /^word\/(document|header|footer).*\.xml$/.test(name));
    if (!xmlFiles.length) throw new Error("No Word document XML files were found.");
    setNode("load", "done", `${xmlFiles.length} Word XML files loaded.`);

    setNode("preview", "running", "Extracting uploaded document text.");
    const inputLines = await collectText(zip, xmlFiles);
    uploadedMeta.textContent = `${inputLines.length} lines`;
    uploadedPreview.textContent = previewText(inputLines);
    setNode("preview", "done", `${inputLines.length} text lines extracted.`);

    setNode("detect", "running", "Scanning text nodes for PII patterns.");
    for (const file of xmlFiles) {
      const xml = await zip.file(file).async("text");
      const doc = new DOMParser().parseFromString(xml, "application/xml");
      for (const node of [...doc.getElementsByTagName("w:t")]) {
        const original = node.textContent;
        const replaced = detectAndReplace(original, counts);
        if (replaced !== original) {
          node.textContent = replaced;
          changedNodes += 1;
        }
      }
      const serialized = new XMLSerializer().serializeToString(doc);
      zip.file(file, serialized);
    }
    setNode("detect", "done", `${Object.values(counts).reduce((a, b) => a + b, 0)} replacements detected.`);

    setNode("redact", "done", `${changedNodes} DOCX text nodes changed.`);
    const outputLines = await collectText(zip, xmlFiles);
    resultMeta.textContent = `${outputLines.length} lines`;
    resultPreview.textContent = previewText(outputLines);

    setNode("package", "running", "Generating redacted DOCX download.");
    const blob = await zip.generateAsync({ type: "blob" });
    const outputName = state.file.name.replace(/\.docx$/i, " - Redacted.docx");
    const url = URL.createObjectURL(blob);
    downloadLink.href = url;
    downloadLink.download = outputName;
    downloadLink.textContent = `Download ${outputName}`;
    downloadLink.classList.remove("hidden");
    setNode("package", "done", `${Math.round(blob.size / 1024).toLocaleString()} KB DOCX generated.`);
    setNode("download", "done", outputName);

    renderSummary(counts, changedNodes);
    document.querySelector(".preview-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    log(`Redaction completed with ${Object.values(counts).reduce((a, b) => a + b, 0)} replacements.`);
  } catch (error) {
    setNode("load", "error", error.message);
    log(`ERROR: ${error.message}`);
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
