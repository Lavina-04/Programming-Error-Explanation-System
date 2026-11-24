(() => {
  "use strict";
  const API = (window.PEES_API || (location.protocol === "file:" ? "http://127.0.0.1:5001" : "")).replace(/\/$/, "");
  const main = document.getElementById("main");

  /* ---------- helpers ---------- */
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else if (["value", "checked", "disabled", "selected", "open"].includes(k)) el[k] = v;
      else el.setAttribute(k, v === true ? "" : v);
    }
    const add = (kid) => {
      if (kid == null || kid === false) return;
      if (Array.isArray(kid)) return kid.forEach(add);
      el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
    };
    kids.forEach(add);
    return el;
  }
  async function api(path, options) {
    let response;
    try {
      response = await fetch(API + path, {
        headers: { "Content-Type": "application/json" }, ...options,
        body: options && options.body ? JSON.stringify(options.body) : undefined,
      });
    } catch (e) {
      throw new Error("Could not reach the backend. Start it with `python app.py` and reload this page.");
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
    return data;
  }
  const clear = (el) => { while (el.firstChild) el.removeChild(el.firstChild); return el; };
  const spinner = () => h("span", { class: "spinner", "aria-hidden": "true" });
  function busy(button, label, work) {
    const original = Array.from(button.childNodes);
    button.disabled = true; clear(button).append(spinner(), " " + label);
    return work().finally(() => { button.disabled = false; clear(button).append(...original); });
  }
  const errBox = (e) => h("div", { class: "alert", role: "alert", text: e.message });

  /* ---------- syntax highlighting ---------- */
  const WORDS = {
    Python: "and as assert break class continue def del elif else except finally for from global if import in is lambda None nonlocal not or pass raise return try while with yield True False",
    Java: "abstract boolean break byte case catch char class continue default do double else enum extends final finally float for if implements import instanceof int interface long new package private protected public return short static super switch this throw throws try void while null true false String",
  };
  WORDS.C = "auto break case char const continue default do double else enum extern float for goto if int long register return short signed sizeof static struct switch typedef union unsigned void volatile while NULL";
  WORDS["C++"] = WORDS.C + " bool catch class delete namespace new private protected public template this throw try using virtual true false nullptr string vector cout cin endl std";
  const RULES = {};
  function rule(lang) {
    if (RULES[lang]) return RULES[lang];
    const py = lang === "Python";
    const parts = [
      py ? String.raw`(?<c>#[^\n]*)` : String.raw`(?<c>\/\/[^\n]*|\/\*[\s\S]*?\*\/)`,
      py ? String.raw`(?<s>"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')`
         : String.raw`(?<s>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')`,
      py ? null : String.raw`(?<p>^[ \t]*#[^\n]*)`,
      String.raw`(?<n>\b\d+(?:\.\d+)?\b)`,
      String.raw`(?<w>[A-Za-z_]\w*)`,
    ].filter(Boolean);
    return (RULES[lang] = { re: new RegExp(parts.join("|"), "gm"), words: new Set((WORDS[lang] || "").split(" ")) });
  }
  function tokenize(text, lang) {
    const { re, words } = rule(lang), out = []; let last = 0; re.lastIndex = 0;
    for (let m; (m = re.exec(text)); ) {
      if (m.index > last) out.push({ t: "", s: text.slice(last, m.index) });
      const g = m.groups; let t = "";
      if (g.c) t = "c"; else if (g.s) t = "s"; else if (g.p) t = "p"; else if (g.n) t = "n";
      else if (g.w && words.has(g.w)) t = "k";
      out.push({ t, s: m[0] }); last = m.index + m[0].length;
      if (m[0].length === 0) re.lastIndex++;
    }
    if (last < text.length) out.push({ t: "", s: text.slice(last) });
    return out;
  }
  function toLines(tokens) {
    const lines = [[]];
    for (const tok of tokens) tok.s.split("\n").forEach((part, i) => {
      if (i > 0) lines.push([]);
      if (part) lines[lines.length - 1].push({ t: tok.t, s: part });
    });
    return lines;
  }

  /* ---------- code editor (textarea over a highlighted layer) ---------- */
  function createEditor({ language, value = "", readOnly = false, onChange, onRun }) {
    let lang = language, errLine = null;
    const gutter = h("div", { class: "gutter", "aria-hidden": "true" });
    const hl = h("pre", { class: "hl", "aria-hidden": "true" });
    const ta = h("textarea", { spellcheck: "false", autocapitalize: "off", autocomplete: "off", wrap: "off",
      "aria-label": "Code editor", readonly: readOnly || null });
    ta.value = value;
    const el = h("div", { class: "editor" }, h("div", { class: "scroller" }, gutter, h("div", { class: "code" }, hl, ta)));
    function paint() {
      const lines = toLines(tokenize(ta.value, lang));
      clear(hl); clear(gutter);
      lines.forEach((parts, i) => {
        const n = i + 1;
        hl.append(h("span", { class: "ln" + (n === errLine ? " err" : "") },
          parts.length ? parts.map((p) => h("span", { class: p.t ? "tok-" + p.t : null, text: p.s })) : "\u200b"));
        gutter.append(h("div", { class: n === errLine ? "err" : null, text: String(n) }));
      });
    }
    ta.addEventListener("input", () => { errLine = null; paint(); onChange && onChange(ta.value); });
    ta.addEventListener("keydown", (e) => {
      if (readOnly) return;
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); onRun && onRun(); return; }
      const s = ta.selectionStart, t = ta.selectionEnd, v = ta.value;
      const edit = (text, caret) => { ta.setRangeText(text, s, t, "end"); if (caret != null) ta.selectionStart = ta.selectionEnd = caret; ta.dispatchEvent(new Event("input")); };
      if (e.key === "Tab") { e.preventDefault(); edit("    "); }
      else if (e.key === "Enter") {
        const before = v.slice(0, s), line = before.slice(before.lastIndexOf("\n") + 1);
        let indent = line.match(/^\s*/)[0];
        if (/[:{]\s*$/.test(line)) indent += "    ";
        e.preventDefault(); edit("\n" + indent);
      }
    });
    paint();
    return {
      el, getValue: () => ta.value,
      setValue(v) { ta.value = v; errLine = null; paint(); },
      setLanguage(l) { lang = l; paint(); },
      markLine(n) { errLine = n || null; paint(); },
      focus: () => ta.focus(),
    };
  }

  /* ---------- shared state ---------- */
  const state = {
    languages: [],
    u: { language: "Python", code: "numbers = [10, 20, 30]\nprint(numbers[5])\n", expected: "", stdin: "", level: "beginner", data: null, hints: [], hintCount: 0, attemptId: null, retries: 0 },
  };
  const EXAMPLES = [
    { title: "List index out of range", note: "Python", language: "Python", code: "numbers = [10, 20, 30]\nprint(numbers[5])\n" },
    { title: "Misspelled variable", note: "Python", language: "Python", code: "total = 10\nprint(totl)\n" },
    { title: "Missing semicolon", note: "Java", language: "Java", code: "public class Main {\n    public static void main(String[] args) {\n        int x = 5\n        System.out.println(x);\n    }\n}\n" },
    { title: "Null pointer", note: "C", language: "C", code: "#include <stdio.h>\n\nint main() {\n    int *p = NULL;\n    *p = 5;\n    return 0;\n}\n" },
    { title: "Variable out of scope", note: "C++", language: "C++", code: "#include <iostream>\nusing namespace std;\n\nint main() {\n    for (int i = 0; i < 3; i++) { }\n    cout << i;\n    return 0;\n}\n" },
  ];
  async function loadLanguages() {
    if (state.languages.length) return state.languages;
    try { state.languages = (await api("/api/languages")).details; }
    catch { state.languages = ["Python", "Java", "C", "C++"].map((name) => ({ name, available: true, note: "" })); }
    return state.languages;
  }
  const langSelect = (value, onChange) => {
    const sel = h("select", { "aria-label": "Programming language", onchange: () => onChange(sel.value) },
      state.languages.map((l) => h("option", { value: l.name, selected: l.name === value, text: l.name + (l.available ? "" : " (compiler missing)") })));
    return sel;
  };
  const catClass = (c) => ({ "Syntax Error": "cat-syntax", "Compilation Error": "cat-compile", "Type Error": "cat-type",
    "Runtime Error": "cat-runtime", "Memory Error": "cat-memory", "Time Limit Error": "cat-time" }[c] || "");

  /* ---------- Home ---------- */
  async function home() {
    await loadLanguages();
    const recent = h("div", { class: "list" }, h("div", { class: "item muted", text: "Loading..." }));
    const specimen = h("div", { class: "specimen", role: "img", "aria-label": "Example: a Python line highlighted with a note explaining that index 5 does not exist in a three-item list" },
      h("pre", {}, [["1", "numbers = [10, 20, 30]", false], ["2", "print(numbers[5])", true]].map(([n, t, hit]) =>
        h("div", { class: "l" + (hit ? " hit" : "") }, h("span", { class: "n", text: n }), h("span", { text: t })))),
      h("div", { class: "note" }, h("strong", { text: "Index 5 does not exist" }),
        "Your list has three items, so the valid indexes are 0, 1 and 2. Lists start counting at zero."));
    main.append(
      h("section", { class: "hero" },
        h("div", {}, h("h1", { text: "Understand your error, then fix it yourself." }),
          h("p", { class: "lead", text: "Paste a Python, Java, C or C++ program. You get the line that failed, the reason in plain language, and hints that guide you before any answer is shown." }),
          h("div", { class: "actions" },
            h("a", { class: "btn primary", href: "#/understand", text: "Start learning" }),
            h("a", { class: "btn", href: "#/practice", text: "Try a practice question" }))),
        specimen),
      h("section", { class: "section" }, h("h2", { text: "Learn from a common mistake" }),
        h("div", { class: "chips" }, EXAMPLES.map((ex) => h("button", { class: "chip", type: "button", onclick: () => {
          Object.assign(state.u, { language: ex.language, code: ex.code, data: null, hints: [], hintCount: 0, attemptId: null, retries: 0 });
          location.hash = "#/understand";
        } }, h("b", { text: ex.title }), h("span", { text: ex.note }))))),
      h("section", { class: "section" }, h("h2", { text: "Languages" }),
        h("div", { class: "langs" }, state.languages.map((l) => h("div", {}, h("b", { text: l.name }),
          h("span", { class: l.available ? "ok" : "no", text: l.available ? "Ready" : "Compiler not found" }),
          l.available ? null : h("div", { class: "muted", style: "font-size:13px", text: l.note }))))),
      h("section", { class: "section" }, h("h2", { text: "Recently analysed programs" }), recent));
    try {
      const { attempts } = await api("/api/attempts?limit=6");
      clear(recent);
      if (!attempts.length) recent.append(h("div", { class: "item muted", text: "Nothing yet. Analyse a program and it will appear here." }));
      attempts.forEach((a) => recent.append(h("div", { class: "item" },
        h("b", { text: a.language }), h("span", { class: "grow", text: a.error_name || ({ correct: "Ran correctly", logical_error: "Output did not match" }[a.status] || a.status) }),
        h("span", { class: "pill " + (a.solved ? "good" : ""), text: a.solved ? "Solved" : a.source }),
        a.source === "code" ? h("button", { class: "btn small", type: "button", onclick: () => openAttempt(a) , text: "Open" }) : null)));
    } catch (e) { clear(recent).append(h("div", { class: "item" }, e.message)); }
  }
  function openAttempt(a) {
    Object.assign(state.u, { language: a.language, code: a.latest_code || a.code, expected: a.expected_output || "", data: null, hints: [], hintCount: 0, attemptId: null, retries: 0 });
    location.hash = "#/understand";
  }

  /* ---------- Understand an error ---------- */
  async function understand() {
    await loadLanguages();
    const u = state.u;
    const result = h("div", { class: "notes", "aria-live": "polite" });
    const analyzeBtn = h("button", { class: "btn primary", type: "button", text: "Explain my error" });
    const retryBtn = h("button", { class: "btn", type: "button", text: "Check my changes", hidden: !u.attemptId });
    const editor = trackedCreate({ language: u.language, value: u.code, onChange: (v) => (u.code = v), onRun: () => run() });
    const langEl = langSelect(u.language, (l) => { u.language = l; editor.setLanguage(l); u.attemptId = null; retryBtn.hidden = true; });
    const levelEl = h("select", { "aria-label": "Explanation level", onchange: () => (u.level = levelEl.value) },
      [["beginner", "Beginner wording"], ["intermediate", "More technical"]].map(([v, t]) => h("option", { value: v, selected: u.level === v, text: t })));
    const expected = h("textarea", { class: "plain", id: "expected", onchange: () => (u.expected = expected.value) }); expected.value = u.expected;
    const stdin = h("textarea", { class: "plain", id: "stdin", onchange: () => (u.stdin = stdin.value) }); stdin.value = u.stdin;

    const body = () => ({ language: u.language, code: editor.getValue(), expected_output: expected.value.trim() ? expected.value : undefined, stdin: stdin.value, skill_level: u.level });
    function show(data, banner) {
      u.data = data; clear(result); renderResult(result, data, editor, banner);
    }
    async function run() {
      Object.assign(u, { code: editor.getValue(), expected: expected.value, stdin: stdin.value, hints: [], hintCount: 0, retries: 0 });
      return busy(analyzeBtn, "Analysing", async () => {
        try { const data = await api("/api/explain", { method: "POST", body: body() }); u.attemptId = data.attempt_id; retryBtn.hidden = false; show(data); }
        catch (e) { clear(result).append(errBox(e)); }
      });
    }
    analyzeBtn.addEventListener("click", run);
    retryBtn.addEventListener("click", () => busy(retryBtn, "Checking", async () => {
      try {
        const data = await api(`/api/attempts/${u.attemptId}/retry`, { method: "POST", body: { code: editor.getValue(), expected_output: expected.value.trim() ? expected.value : undefined, stdin: stdin.value } });
        u.retries += 1; u.code = editor.getValue();
        const ok = data.analysis.status === "correct";
        show({ attempt_id: u.attemptId, analysis: data.analysis, explanation: data.explanation },
          ok ? { cls: "good", text: `Fixed on retry ${u.retries}. Your program now runs correctly.` } : { cls: "info", text: `Retry ${u.retries}: there is still something to fix.` });
      } catch (e) { clear(result).append(errBox(e)); }
    }));

    main.append(h("div", { class: "workspace" },
      h("div", {},
        h("div", { class: "panel-title" }, h("h1", { style: "font-size:30px;margin:0", text: "Understand an error" })),
        h("div", { class: "row", style: "margin-bottom:10px" },
          h("div", { class: "field" }, h("label", { text: "Language" }), langEl),
          h("div", { class: "field" }, h("label", { text: "Explanation" }), levelEl),
          analyzeBtn, retryBtn),
        editor.el,
        h("p", { class: "muted", style: "font-size:13px;margin:6px 0 0", text: "Press Ctrl+Enter to analyse. Tab inserts four spaces." }),
        h("details", { class: "extra", open: !!(u.expected || u.stdin) }, h("summary", { text: "Expected output and program input (optional)" }),
          h("div", { class: "extras" },
            h("div", { class: "field" }, h("label", { for: "expected", text: "Expected output" }), expected),
            h("div", { class: "field" }, h("label", { for: "stdin", text: "Program input, one value per line" }), stdin)))),
      h("div", {}, h("div", { class: "panel-title" }, h("h2", { style: "margin:0", text: "What the system found" })), result)));
    if (u.data) show(u.data); else result.append(h("p", { class: "empty", text: "Analyse a program to see which line failed, why it happened, and hints to fix it yourself." }));
  }

  function renderResult(box, data, editor, banner) {
    const a = data.analysis, ex = data.explanation || {};
    if (banner) box.append(h("div", { class: "banner " + banner.cls, text: banner.text }));
    editor.markLine(null);

    if (a.status === "unsupported" || a.status === "unavailable") {
      box.append(h("h2", { text: a.status === "unavailable" ? "This language is not ready" : "Language not supported" }), h("p", { text: a.message }));
      return;
    }
    if (a.status === "correct" || a.status === "logical_error") {
      box.classList.add("ok-state");
      box.append(h("h2", { text: a.status === "correct" ? "It runs correctly" : "It runs, but the output differs" }));
      if (a.status === "logical_error") {
        box.classList.remove("ok-state");
        if (ex.specific) box.append(h("p", { class: "specific", text: ex.specific }));
        box.append(h("section", {}, h("h3", { text: "Your output" }), h("div", { class: "outbox", text: a.actual_output || "(nothing printed)" }),
          h("h3", { style: "margin-top:10px", text: "Expected output" }), h("div", { class: "outbox", text: a.expected_output })));
        sections(box, ex);
        hintsAndFix(box, data, true);
      } else {
        box.append(h("p", { text: ex.summary }), h("section", {}, h("h3", { text: "Program output" }), h("div", { class: "outbox", text: a.actual_output || "(nothing printed)" })));
        warnings(box, ex);
        box.append(h("p", { class: "muted", text: ex.next_step }));
      }
      return;
    }

    const e = a.error;
    box.classList.remove("ok-state"); box.classList.add(catClass(e.category));
    if (e.line_number) editor.markLine(e.line_number);
    box.append(h("h2", { text: e.error_name }),
      h("p", { class: "where", text: `${e.category}${e.line_number ? `, line ${e.line_number}` : ""}` }));
    if (e.code) box.append(h("div", { class: "sourceline", text: e.code }));
    if (ex.specific) box.append(h("p", { class: "specific", text: ex.specific }));
    box.append(h("section", {}, h("h3", { text: "What happened" }), h("p", { text: ex.cause })));
    sections(box, ex);
    box.append(h("section", {}, h("h3", { text: "Original message" }), h("div", { class: "raw", text: e.raw_message || e.message })));
    if (a.output) box.append(h("section", {}, h("h3", { text: "Output before the error" }), h("div", { class: "outbox", text: a.output })));
    warnings(box, ex);
    hintsAndFix(box, data, false);
    if (ex.learning_outcome) box.append(h("p", { class: "outline", text: "What you learn: " + ex.learning_outcome }));
  }
  function sections(box, ex) {
    if (ex.why_it_happened) box.append(h("section", {}, h("h3", { text: "Why it happened" }), h("p", { text: ex.why_it_happened })));
    if (ex.approach) box.append(h("section", {}, h("h3", { text: "How to approach the correction" }), h("p", { text: ex.approach })));
    if (ex.learning_question) box.append(h("section", {}, h("h3", { text: "Think about it" }), h("p", { text: ex.learning_question })));
  }
  function warnings(box, ex) {
    if (ex.warnings && ex.warnings.length) box.append(h("section", {}, h("h3", { text: "Compiler warnings" }),
      h("ul", { class: "warns" }, ex.warnings.map((w) => h("li", { text: (w.line ? `Line ${w.line}: ` : "") + w.message })))));
  }
  function hintsAndFix(box, data, isLogic) {
    const u = state.u, id = data.attempt_id;
    const hintList = h("div", {});
    const hintBtn = h("button", { class: "btn small", type: "button" });
    const fixArea = h("div", {});
    const fixBtn = h("button", { class: "btn small", type: "button", text: "I'm stuck, show a possible fix", disabled: u.hintCount === 0, title: "Try at least one hint first" });
    const label = () => (hintBtn.textContent = u.hintCount ? `Show hint ${u.hintCount + 1}` : "Show a hint");
    u.hints.forEach((t, i) => hintList.append(h("div", { class: "hintbox", text: `Hint ${i + 1}: ${t}` })));
    label(); if (u.hintCount >= 3) hintBtn.hidden = true;
    hintBtn.addEventListener("click", () => busy(hintBtn, "Loading", async () => {
      try {
        const r = await api("/api/hints", { method: "POST", body: { attempt_id: id, level: u.hintCount + 1 } });
        u.hints.push(r.hint); u.hintCount += 1; hintList.append(h("div", { class: "hintbox", text: `Hint ${u.hintCount}: ${r.hint}` }));
        fixBtn.disabled = false; if (u.hintCount >= 3) hintBtn.hidden = true;
      } catch (e) { hintList.append(errBox(e)); }
    }).then(label));
    fixBtn.addEventListener("click", () => busy(fixBtn, "Checking fix", async () => {
      try {
        const { solution: s } = await api("/api/solution", { method: "POST", body: { attempt_id: id } });
        clear(fixArea);
        const card = h("div", { class: "fix" }, h("p", { style: "margin:0 0 4px;font-weight:600", text: s.description || s.solution }));
        if (s.description) card.append(h("p", { style: "margin:0 0 6px", text: s.solution }));
        (s.alternatives || []).forEach((t) => card.append(h("p", { class: "muted", style: "margin:0 0 4px", text: "Another option: " + t })));
        if (s.corrected_code) {
          card.append(h("div", { class: "diff" }, h("span", { class: "minus", text: `- line ${s.changed_line}: ${s.before}` }), h("span", { class: "plus", text: `+ line ${s.changed_line}: ${s.after}` })),
            h("p", { class: "muted", style: "font-size:13px;margin:4px 0 8px", text: s.note + (s.remaining_issue ? ` After this change the next problem is: ${s.remaining_issue}.` : "") }),
            h("button", { class: "btn small primary", type: "button", text: "Apply to editor", onclick: () => { currentEditor && currentEditor.setValue(s.corrected_code); u.code = s.corrected_code; } }));
        }
        fixArea.append(card);
      } catch (e) { fixArea.append(errBox(e)); }
    }));
    box.append(h("section", {}, h("h3", { text: "Need a nudge?" }), hintList,
      h("div", { class: "row", style: "margin-top:8px" }, hintBtn, fixBtn), fixArea));
  }
  // Remember the active editor so "Apply to editor" knows which one to update.
  let currentEditor = null;
  const trackedCreate = (opts) => (currentEditor = createEditor(opts));

  /* ---------- Practice ---------- */
  async function practice() {
    await loadLanguages();
    const panel = h("div", {});
    const tabBtn = (id, text) => h("button", { role: "tab", type: "button", "aria-selected": String(tab === id), text, onclick: () => { tab = id; draw(); } });
    let tab = "write";
    const tabs = h("div", { class: "tabs", role: "tablist" });
    function draw() {
      clear(tabs).append(tabBtn("write", "Write the code"), tabBtn("spot", "Spot the error"));
      clear(panel); (tab === "write" ? writeTab : spotTab)(panel);
    }
    main.append(h("h1", { style: "font-size:34px", text: "Practice" }), tabs, panel); draw();
  }
  async function writeTab(panel) {
    let concepts;
    try { concepts = (await api("/api/practice/concepts")).concepts; } catch (e) { panel.append(errBox(e)); return; }
    let problem = null, lang = "Python", conceptKey = concepts[0].key, hintShown = false;
    const out = h("div", { class: "notes", "aria-live": "polite" });
    const stage = h("div", {});
    const pick = h("select", { "aria-label": "Topic", onchange: () => { conceptKey = pick.value; lang = "Python"; load(); } },
      concepts.map((c) => h("option", { value: c.key, text: `${c.concept}: ${c.title}` })));
    async function load() {
      clear(out); clear(stage); hintShown = false;
      try { problem = await api("/api/practice/generate", { method: "POST", body: { concept: conceptKey } }); } catch (e) { stage.append(errBox(e)); return; }
      if (!problem.languages.includes(lang)) lang = problem.languages[0];
      const editor = trackedCreate({ language: lang, value: problem.starters[lang] });
      const sel = h("select", { "aria-label": "Language", onchange: () => { lang = sel.value; editor.setLanguage(lang); editor.setValue(problem.starters[lang]); } },
        problem.languages.map((l) => h("option", { value: l, selected: l === lang, text: l })));
      const submit = h("button", { class: "btn primary", type: "button", text: "Check my answer" });
      const hintBtn = h("button", { class: "btn", type: "button", text: "Show a hint" });
      hintBtn.addEventListener("click", () => { clear(out).append(h("div", { class: "hintbox", text: problem.hint })); });
      submit.addEventListener("click", () => busy(submit, "Running", async () => {
        try {
          const r = await api("/api/practice/submit", { method: "POST", body: { concept: conceptKey, code: editor.getValue(), language: lang } });
          clear(out); out.className = "notes"; editor.markLine(null);
          if (r.evaluation.passed) { out.classList.add("ok-state"); out.append(h("div", { class: "banner good", text: "Correct. Your output matches." }), h("div", { class: "outbox", text: r.evaluation.actual_output })); return; }
          out.append(h("h2", { text: r.analysis.status === "error" ? "Your program has an error" : "Not quite yet" }));
          if (r.analysis.status === "error") {
            out.classList.add(catClass(r.analysis.error.category)); editor.markLine(r.analysis.error.line_number);
            out.append(h("p", { class: "where", text: `${r.analysis.error.error_name}${r.analysis.error.line_number ? `, line ${r.analysis.error.line_number}` : ""}` }));
          } else out.append(h("section", {}, h("h3", { text: "Your output" }), h("div", { class: "outbox", text: r.evaluation.actual_output || "(nothing printed)" }), h("h3", { style: "margin-top:10px", text: "Expected" }), h("div", { class: "outbox", text: r.evaluation.expected_output })));
          const ex = r.explanation; if (ex.specific) out.append(h("p", { class: "specific", text: ex.specific }));
          out.append(h("p", { text: ex.cause }), h("p", { class: "muted", text: ex.approach || ex.next_step }));
        } catch (e) { clear(out).append(errBox(e)); }
      }));
      stage.append(h("h2", { text: problem.title }), h("p", { text: problem.description }),
        h("div", { class: "row", style: "margin-bottom:10px" }, h("div", { class: "field" }, h("label", { text: "Language" }), sel), submit, hintBtn),
        h("div", { class: "workspace" }, editor.el, out));
    }
    panel.append(h("div", { class: "field", style: "max-width:460px;margin-bottom:16px" }, h("label", { text: "Topic" }), pick), stage); load();
  }
  async function spotTab(panel) {
    let items;
    try { items = (await api("/api/practice/exercises")).exercises; } catch (e) { panel.append(errBox(e)); return; }
    let index = 0, filter = "All";
    const stage = h("div", {});
    const filt = h("select", { "aria-label": "Language filter", onchange: () => { filter = filt.value; index = 0; draw(); } },
      ["All", "Python", "Java", "C", "C++"].map((l) => h("option", { value: l, text: l })));
    const list = () => items.filter((e) => filter === "All" || e.language === filter);
    function draw() {
      clear(stage); const set = list(); if (!set.length) { stage.append(h("p", { text: "No exercises for this language." })); return; }
      const ex = set[index % set.length]; let chosen = null;
      const view = createEditor({ language: ex.language, value: ex.code, readOnly: true });
      const line = h("input", { type: "number", id: "ln", min: "1", style: "width:90px" });
      const fb = h("div", { class: "notes", "aria-live": "polite" });
      const submit = h("button", { class: "btn primary", type: "button", text: "Check answer" });
      const hintBtn = h("button", { class: "btn", type: "button", text: "Show a hint" });
      const next = h("button", { class: "btn", type: "button", text: "Next exercise", onclick: () => { index += 1; draw(); } });
      hintBtn.addEventListener("click", async () => { try { const r = await api(`/api/practice/exercises/${ex.key}/hint`); clear(fb).append(h("div", { class: "hintbox", text: r.hint })); } catch (e) { clear(fb).append(errBox(e)); } });
      submit.addEventListener("click", () => {
        if (!chosen) { clear(fb).append(errBox(new Error("Choose an answer first."))); return; }
        busy(submit, "Checking", async () => {
          try {
            const r = await api("/api/practice/identify", { method: "POST", body: { exercise_key: ex.key, answer: chosen, line: line.value ? Number(line.value) : undefined } });
            clear(fb); fb.className = "notes " + (r.passed ? "ok-state" : "cat-runtime"); view.markLine(r.correct_line);
            fb.append(h("div", { class: "banner " + (r.passed ? "good" : "info"), text: r.passed ? "Correct." : r.error_correct ? "The error is right, but check the line number." : "Not quite." }),
              h("p", { text: `The error is ${r.correct_answer} on line ${r.correct_line}.` }), h("p", { text: r.explanation }));
          } catch (e) { clear(fb).append(errBox(e)); }
        });
      });
      stage.append(h("h2", { text: ex.title }), h("p", { class: "muted", text: `${ex.language}. ${ex.question}` }),
        h("div", { class: "workspace" }, view.el, h("div", {},
          h("fieldset", { style: "border:0;padding:0;margin:0" }, h("legend", { style: "font-weight:600", text: "Which error is it?" }),
            h("div", { class: "options" }, ex.options.map((o) => h("label", {}, h("input", { type: "radio", name: "opt", value: o, onchange: () => (chosen = o) }), o)))),
          h("div", { class: "field", style: "margin-bottom:12px" }, h("label", { for: "ln", text: "On which line? (optional)" }), line),
          h("div", { class: "row" }, submit, hintBtn, next), fb)));
    }
    panel.append(h("div", { class: "field", style: "max-width:220px;margin-bottom:16px" }, h("label", { text: "Language" }), filt), stage); draw();
  }

  /* ---------- Progress ---------- */
  async function progress() {
    const root = h("div", {}, h("p", { class: "muted", text: "Loading..." }));
    main.append(h("h1", { style: "font-size:34px", text: "My progress" }), root);
    let p;
    try { p = await api("/api/progress"); } catch (e) { clear(root).append(errBox(e)); return; }
    const bars = (rows, label, value, max) => {
      const top = Math.max(1, ...rows.map(value));
      return h("div", { class: "bars" }, rows.length ? rows.map((r) => h("div", { class: "bar" }, h("span", { text: label(r) }),
        h("div", { class: "track" }, h("div", { class: "fill", style: `width:${(value(r) / top) * 100}%` })), h("span", { text: String(value(r)) }))) : h("p", { class: "muted", text: "No data yet." }));
    };
    const stat = (n, t) => h("div", { class: "stat" }, h("b", { text: n }), h("span", { text: t }));
    const byDay = Object.fromEntries(p.activity.map((d) => [d.day, d]));
    const act = Array.from({ length: 14 }, (_, i) => {
      const day = new Date(Date.now() - (13 - i) * 864e5).toISOString().slice(0, 10);
      return byDay[day] || { day, attempts: 0, solved: 0 };
    });
    const topAct = Math.max(1, ...act.map((d) => d.attempts));
    clear(root).append(
      h("div", { class: "stats" }, stat(p.total_attempts, "Total attempts"), stat(p.solved_attempts, "Solved correctly"),
        stat(p.overall_accuracy_percentage + "%", "Overall accuracy"), stat(p.practice.accuracy_percentage + "%", "Practice accuracy"),
        stat(p.retries.success_percentage + "%", "Retries that fixed the program")),
      h("div", { class: "grid2 section" },
        h("div", {}, h("h2", { text: "Common error categories" }), bars(p.category_frequency, (r) => r.category, (r) => r.count)),
        h("div", {}, h("h2", { text: "Errors you meet most" }), bars(p.error_frequency.slice(0, 8), (r) => r.error_name, (r) => r.count)),
        h("div", {}, h("h2", { text: "Languages" }), bars(p.language_frequency, (r) => r.language, (r) => r.attempts)),
        h("div", {}, h("h2", { text: "Concepts" }), bars(p.concept_frequency.slice(0, 8), (r) => `${r.concept} (${r.solved || 0} solved)`, (r) => r.attempts))),
      h("section", { class: "section" }, h("h2", { text: "Last 14 days" }),
        p.total_attempts ? h("div", { class: "activity", role: "img", "aria-label": "Attempts per day" }, act.map((d) => h("div", { class: "col", title: `${d.day}: ${d.attempts} attempts, ${d.solved} solved` },
          h("div", { class: "a", style: `height:${((d.attempts - (d.solved || 0)) / topAct) * 80}px` }), h("div", { class: "s", style: `height:${((d.solved || 0) / topAct) * 80}px` }), d.day.slice(8)))) : h("p", { class: "muted", text: "No recent activity." }),
        h("p", { class: "muted", style: "font-size:13px", text: "Dark bars are solved attempts; light bars are attempts that still need work." })),
      h("section", { class: "section" }, h("h2", { text: "Retry history" }),
        p.retry_history.length ? h("div", { class: "table-wrap" }, h("table", {}, h("thead", {}, h("tr", {}, ["Attempt", "Language", "Error", "Retries", "Result"].map((t) => h("th", { text: t })))),
          h("tbody", {}, p.retry_history.map((r) => h("tr", {}, h("td", { text: "#" + r.id }), h("td", { text: r.language }), h("td", { text: r.error_name || r.concept || "" }), h("td", { text: String(r.retry_count) }),
            h("td", {}, h("span", { class: "pill " + (r.solved ? "good" : "bad"), text: r.solved ? "Solved" : "Not solved yet" }))))))) : h("p", { class: "muted", text: "When you retry an attempt, it shows up here." })));
  }

  /* ---------- router ---------- */
  const routes = { home, understand, practice, progress };
  async function route() {
    const name = (location.hash.replace(/^#\/?/, "") || "home").split("/")[0];
    const key = routes[name] ? name : "home";
    document.querySelectorAll("nav a").forEach((a) => (a.dataset.route === key ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
    clear(main);
    await routes[key]();
  }
  window.addEventListener("hashchange", route);
  route();
})();
