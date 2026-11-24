// Programming Error Explanation - VS Code extension (plain JavaScript, no build step).
const vscode = require("vscode");

const LANGUAGES = { python: "Python", java: "Java", c: "C", cpp: "C++" };
let diagnostics, panel, lastAttempt = null, lastDocument = null, lastFix = null;

function config() { return vscode.workspace.getConfiguration("pees"); }
function server() { return config().get("serverUrl").replace(/\/$/, ""); }

async function api(path, body) {
  let response;
  try {
    response = await fetch(server() + path, {
      method: body ? "POST" : "GET", headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error(`Cannot reach the backend at ${server()}. Start it with: python app.py`);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function page(content) {
  const nonce = Math.random().toString(36).slice(2);
  return `<!DOCTYPE html><html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
<style>
 body{font-family:var(--vscode-font-family);padding:12px 16px;line-height:1.5}
 h2{margin:0 0 2px} h3{margin:16px 0 4px;font-size:13px}
 .where{opacity:.75;margin-bottom:10px}
 .specific{border-left:4px solid #e0b100;background:rgba(224,177,0,.15);padding:8px 10px;margin:8px 0}
 pre{background:var(--vscode-textCodeBlock-background);padding:8px 10px;overflow:auto;white-space:pre-wrap}
 .hint{border:1px solid var(--vscode-panel-border);padding:6px 10px;margin:6px 0}
 .plus{background:rgba(30,160,90,.2);display:block}.minus{background:rgba(200,50,40,.2);display:block}
 button{background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:0;padding:5px 12px;margin:6px 6px 0 0;cursor:pointer}
 button:disabled{opacity:.5;cursor:not-allowed}
</style></head><body>${content}
<script nonce="${nonce}">
 const vs = acquireVsCodeApi();
 document.addEventListener("click", e => {
   const b = e.target.closest("[data-cmd]");
   if (b && !b.disabled) vs.postMessage({ cmd: b.dataset.cmd });
 });
 window.addEventListener("message", e => {
   const m = e.data, box = document.getElementById(m.target); if (!box) return;
   if (m.html !== undefined) box.insertAdjacentHTML("beforeend", m.html);
   if (m.hideButton) document.getElementById(m.hideButton).hidden = true;
   if (m.enable) document.getElementById(m.enable).disabled = false;
 });
</script></body></html>`;
}

function render(data, document) {
  const a = data.analysis, ex = data.explanation || {};
  if (a.status === "unsupported" || a.status === "unavailable") {
    return page(`<h2>Not available</h2><p>${esc(a.message)}</p>`);
  }
  if (a.status === "correct") {
    return page(`<h2>No error found</h2><p>Your program ran correctly.</p>${a.actual_output ? `<h3>Output</h3><pre>${esc(a.actual_output)}</pre>` : ""}`);
  }
  if (a.status === "logical_error") {
    return page(`<h2>Output differs</h2><div class="specific">${esc(ex.specific)}</div>
      <h3>Your output</h3><pre>${esc(a.actual_output)}</pre><h3>Expected</h3><pre>${esc(a.expected_output)}</pre>`);
  }
  const e = a.error;
  return page(`
    <h2>${esc(e.error_name)}</h2>
    <div class="where">${esc(e.category)}${e.line_number ? `, line ${e.line_number}` : ""} in ${esc(document.fileName.split(/[\\/]/).pop())}</div>
    ${ex.specific ? `<div class="specific">${esc(ex.specific)}</div>` : ""}
    <h3>What went wrong</h3><div>${esc(ex.cause)}</div>
    <h3>Understand the concept</h3><div>${esc(ex.why_it_happened)}</div>
    <h3>How to approach it</h3><div>${esc(ex.approach)}</div>
    <h3>Think about it</h3><div>${esc(ex.learning_question)}</div>
    <h3>Original message</h3><pre>${esc(e.raw_message || e.message)}</pre>
    <h3>Try a hint first</h3><div id="hints"></div>
    <button id="hintBtn" data-cmd="hint">Show a hint</button>
    <button id="fixBtn" data-cmd="fix" disabled title="Request at least one hint first">Show a possible fix</button>
    <div id="fix"></div>`);
}

function showDiagnostic(document, error) {
  if (!error || !error.line_number) return diagnostics.set(document.uri, []);
  const line = Math.min(error.line_number - 1, document.lineCount - 1);
  const range = document.lineAt(line).range;
  const item = new vscode.Diagnostic(range, `${error.error_name}: ${error.message}`, vscode.DiagnosticSeverity.Error);
  item.source = "Error Explanation";
  diagnostics.set(document.uri, [item]);
}

let hintLevel = 0;
async function analyze() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return vscode.window.showInformationMessage("Open a source file first.");
  const document = editor.document;
  const language = LANGUAGES[document.languageId];
  if (!language) return vscode.window.showWarningMessage("Supported languages: Python, Java, C and C++.");
  if (document.isDirty) await document.save();

  await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: "Explaining errors..." }, async () => {
    try {
      const data = await api("/api/explain", { language, code: document.getText(), skill_level: config().get("skillLevel") });
      lastAttempt = data.attempt_id; lastDocument = document; lastFix = null; hintLevel = 0;
      showDiagnostic(document, data.analysis.error);
      if (!panel) {
        panel = vscode.window.createWebviewPanel("peesExplanation", "Error Explanation", vscode.ViewColumn.Beside, { enableScripts: true });
        panel.onDidDispose(() => (panel = null));
        panel.webview.onDidReceiveMessage(onMessage);
      }
      panel.webview.html = render(data, document);
    } catch (error) {
      vscode.window.showErrorMessage(error.message);
    }
  });
}

async function onMessage(message) {
  try {
    if (message.cmd === "hint" && lastAttempt && hintLevel < 3) {
      hintLevel += 1;
      const { hint } = await api("/api/hints", { attempt_id: lastAttempt, level: hintLevel });
      panel.webview.postMessage({ target: "hints", html: `<div class="hint">Hint ${hintLevel}: ${esc(hint)}</div>`, enable: "fixBtn", hideButton: hintLevel >= 3 ? "hintBtn" : undefined });
    } else if (message.cmd === "fix" && lastAttempt) {
      const { solution } = await api("/api/solution", { attempt_id: lastAttempt });
      let html = `<h3>${esc(solution.description || solution.solution)}</h3>`;
      if (solution.corrected_code) {
        lastFix = solution.corrected_code;
        html += `<pre><span class="minus">- line ${solution.changed_line}: ${esc(solution.before)}</span><span class="plus">+ line ${solution.changed_line}: ${esc(solution.after)}</span></pre>
          <div>${esc(solution.note)}</div><button data-cmd="apply" id="applyBtn">Apply to file</button>`;
      } else {
        html += `<div>${esc(solution.solution)}</div>`;
      }
      panel.webview.postMessage({ target: "fix", html, hideButton: "fixBtn" });
    } else if (message.cmd === "apply" && lastFix && lastDocument) {
      const edit = new vscode.WorkspaceEdit();
      const full = new vscode.Range(0, 0, lastDocument.lineCount, 0);
      edit.replace(lastDocument.uri, full, lastFix);
      await vscode.workspace.applyEdit(edit);
      vscode.window.showInformationMessage("Correction applied. Run Explain Errors again to check it.");
    }
  } catch (error) {
    vscode.window.showErrorMessage(error.message);
  }
}

function activate(context) {
  diagnostics = vscode.languages.createDiagnosticCollection("pees");
  context.subscriptions.push(
    diagnostics,
    vscode.commands.registerCommand("pees.analyzeCurrentFile", analyze),
    vscode.commands.registerCommand("pees.clear", () => { diagnostics.clear(); if (panel) panel.dispose(); }),
    vscode.workspace.onDidSaveTextDocument((doc) => {
      if (config().get("analyzeOnSave") && LANGUAGES[doc.languageId] && vscode.window.activeTextEditor?.document === doc) analyze();
    }),
  );
}
function deactivate() {}
module.exports = { activate, deactivate };
