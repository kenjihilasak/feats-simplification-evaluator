import {
  api,
  ApiError,
  unwrapAnnotation,
  unwrapProgress,
  unwrapTask,
} from "./api.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const AUTOSAVE_DELAY_MS = 1200;
const LEASE_RENEWAL_INTERVAL_MS = 5 * 60 * 1000;
const RTL_LANGUAGES = new Set(["ar", "ur", "fa", "he"]);
const STRATEGY_CODES = ["SYN", "MOD", "COMP", "EXPL", "SYNT", "OMIT"];
const CORRECTED_STRATEGIES = new Set([
  ...STRATEGY_CODES,
  "NONE",
  "MULTIPLE",
  "OTHER",
]);

const STRATEGIES = {
  SYN: {
    label: "Synonymy",
    definition: "A more common and general word replaces a more complex or specific expression.",
    instructions: "Mark the complex source expression and its simpler equivalent.",
    roles: [
      ["replaced", "Complex expression", "source", "Select the complex or specific source expression."],
      ["replacement", "Simpler equivalent", "target", "Select the simpler or more general replacement."],
    ],
  },
  MOD: {
    label: "Modulation",
    definition: "Information is redistributed or expressed in a clearer linear organization.",
    instructions: "Mark the source information and its redistributed simplified expression.",
    roles: [
      ["modified_source", "Source information", "source", "Select the information whose organization changes."],
      ["modified_target", "Redistributed information", "target", "Select its clearer or more linear expression."],
    ],
  },
  COMP: {
    label: "Compression",
    definition: "A grammatical or semantic construction is compressed while its central content remains.",
    instructions: "Mark the expanded source content and the compressed expression.",
    roles: [
      ["compressed_source", "Expanded content", "source", "Select the expanded source content."],
      ["compressed_target", "Compressed content", "target", "Select the expression that preserves it compactly."],
    ],
  },
  EXPL: {
    label: "Explanation",
    definition: "An expression or implicit content is explained or made explicit with other words.",
    instructions: "Mark the source anchor being explained and the explanatory content.",
    roles: [
      ["explained", "Explained anchor", "source", "Select the source expression or implicit-content anchor."],
      ["explanation", "Explanation", "target", "Select the words that explain or make the content explicit."],
    ],
  },
  SYNT: {
    label: "Syntactic change",
    definition: "A unit changes into a different syntactic construction while preserving its words or content.",
    instructions: "Mark both sides of the changed construction.",
    roles: [
      ["syntactic_source", "Source construction", "source", "Select the original construction."],
      ["syntactic_target", "Changed construction", "target", "Select the corresponding changed construction."],
    ],
  },
  OMIT: {
    label: "Omission",
    definition: "Material considered unnecessary for understanding is removed.",
    instructions: "Mark the source material omitted from the simplification.",
    roles: [
      ["omitted", "Omitted content", "source", "Select the source material that was omitted."],
    ],
  },
};

const state = {
  user: null,
  task: null,
  annotation: null,
  mode: "evidence",
  activeRole: null,
  pendingEndpoint: null,
  zoom: 1,
  dirty: false,
  saving: false,
  submitting: false,
  conflict: null,
  changeSerial: 0,
  autosaveTimer: null,
  leaseTimer: null,
  loadController: null,
  filters: { sources: [], models: [] },
  filterOptions: { sources: [], models: [] },
};

const byId = (id) => document.getElementById(id);

const MODEL_LABELS = {
  gemma: "Gemma 3 12B pairwise QLoRA",
  qwen: "Qwen2.5 7B pairwise QLoRA",
  e5: "Multilingual-E5 Large BCE",
  xlmr: "XLM-R Large focal classifier",
};
const elements = {
  loginView: byId("login-view"),
  loginForm: byId("login-form"),
  loginUsername: byId("login-username"),
  loginPassword: byId("login-password"),
  loginButton: byId("login-button"),
  loginError: byId("login-error"),
  logoutButton: byId("logout-button"),
  s1ProjectLink: byId("s1-project-link"),
  appHeader: document.querySelector(".app-header"),
  workspace: byId("annotation-workspace"),
  globalAlert: byId("global-alert"),
  languageBadge: byId("language-badge"),
  saveStatus: byId("save-status"),
  reviewerName: byId("reviewer-name"),
  progressCount: byId("progress-count"),
  progressTrack: byId("progress-track"),
  progressFill: byId("progress-fill"),
  strategyCode: byId("strategy-code"),
  reviewHeading: byId("review-heading"),
  strategyDefinition: byId("strategy-definition"),
  sourceValue: byId("source-value"),
  modelsValue: byId("models-value"),
  strategyInstructions: byId("strategy-instructions"),
  strategyExample: byId("strategy-example"),
  verdictControl: byId("verdict-control"),
  correctionPanel: byId("correction-panel"),
  correctedStrategy: byId("corrected-strategy"),
  roleSelector: byId("role-selector"),
  roleHelp: byId("role-help"),
  clearEvidence: byId("clear-evidence"),
  notes: byId("annotation-notes"),
  notesCount: byId("notes-count"),
  evidenceMode: byId("evidence-mode"),
  alignmentMode: byId("alignment-mode"),
  modeInstructions: byId("mode-instructions"),
  zoomOut: byId("zoom-out"),
  zoomIn: byId("zoom-in"),
  zoomValue: byId("zoom-value"),
  parseAlerts: byId("parse-alerts"),
  loading: byId("loading-state"),
  empty: byId("empty-state"),
  refreshQueue: byId("refresh-queue"),
  viewport: byId("alignment-viewport"),
  canvas: byId("annotation-canvas"),
  sourceTree: byId("original-tree"),
  targetTree: byId("simplified-tree"),
  sourceTokens: byId("original-tokens"),
  targetTokens: byId("simplified-tokens"),
  sourceParseStatus: byId("original-parse-status"),
  targetParseStatus: byId("simplified-parse-status"),
  linkRegion: byId("link-region"),
  links: byId("alignment-links"),
  linksEmpty: byId("alignment-empty-hint"),
  linkStatus: byId("link-status"),
  taskIdentity: byId("task-identity"),
  skipButton: byId("skip-button"),
  saveButton: byId("save-button"),
  submitButton: byId("submit-button"),
  filtersButton: byId("filters-button"),
  filtersCount: byId("filters-count"),
  filtersDialog: byId("filters-dialog"),
  filtersForm: byId("filters-form"),
  sourceFilters: byId("source-filters"),
  modelFilters: byId("model-filters"),
  clearFilters: byId("clear-filters"),
  previousButton: byId("previous-button"),
  previousDialog: byId("previous-dialog"),
  previousClose: byId("previous-close"),
  previousLoading: byId("previous-loading"),
  previousEmpty: byId("previous-empty"),
  previousList: byId("previous-list"),
  resultDialog: byId("result-dialog"),
  resultSource: byId("result-source"),
  resultModels: byId("result-models"),
  resultNext: byId("result-next"),
  shortcutsButton: byId("shortcuts-button"),
  shortcutsDialog: byId("shortcuts-dialog"),
  toastRegion: byId("toast-region"),
};

function integerOr(value, fallback) {
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : fallback;
}

function nullableInteger(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : null;
}

function languageBase(language) {
  return String(language || "").toLowerCase().split("-")[0];
}

function directionFor(language) {
  return RTL_LANGUAGES.has(languageBase(language)) ? "rtl" : "ltr";
}

function fallbackTokens(text, language) {
  const source = String(text || "");
  if (languageBase(language) === "ja") {
    let offset = 0;
    return Array.from(source).flatMap((character, index) => {
      const start = offset;
      offset += character.length;
      return /\s/u.test(character)
        ? []
        : [{ index, text: character, start, end: offset }];
    });
  }
  const tokens = [];
  for (const match of source.matchAll(/\S+/gu)) {
    tokens.push({
      index: tokens.length,
      text: match[0],
      start: match.index,
      end: match.index + match[0].length,
    });
  }
  return tokens;
}

function normalizeTokens(rawTokens, text, language) {
  const source = Array.isArray(rawTokens) && rawTokens.length
    ? rawTokens
    : fallbackTokens(text, language);
  return source.map((raw, position) => {
    const token = typeof raw === "string" ? { text: raw } : (raw || {});
    return {
      index: integerOr(
        token.index ?? token.global_index ?? token.token_index,
        position,
      ),
      text: String(token.text ?? token.form ?? token.surface ?? ""),
      start: integerOr(token.start ?? token.start_char, -1),
      end: integerOr(token.end ?? token.end_char, -1),
      orthographicParentIndex: nullableInteger(
        token.orthographic_parent_index ?? token.parent_index,
      ),
      sentenceId: integerOr(token.sentence_id ?? token.sentence_index, 0),
      sentenceTokenIndex: integerOr(
        token.sentence_token_index ?? token.id,
        position,
      ),
      lemma: token.lemma ?? null,
      upos: token.upos ?? token.pos ?? null,
      xpos: token.xpos ?? null,
      feats: token.feats ?? null,
      headIndex: nullableInteger(
        token.head_index ?? token.global_head_index ?? token.head,
      ),
      deprel: token.deprel ?? token.dependency_relation ?? null,
      parseStatus: token.parse_status ?? null,
    };
  });
}

function normalizeLink(raw) {
  if (Array.isArray(raw)) {
    return {
      source_index: nullableInteger(raw[0]),
      target_index: nullableInteger(raw[1]),
    };
  }
  const link = raw || {};
  return {
    source_index: nullableInteger(
      link.source_index ?? link.source ?? link.original_index ?? link[0],
    ),
    target_index: nullableInteger(
      link.target_index ?? link.target ?? link.simple_index ?? link[1],
    ),
  };
}

function normalizeLinks(rawLinks) {
  const seen = new Set();
  const result = [];
  for (const raw of Array.isArray(rawLinks) ? rawLinks : []) {
    const link = normalizeLink(raw);
    if (link.source_index === null || link.target_index === null) continue;
    const key = linkKey(link.source_index, link.target_index);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(link);
  }
  return result;
}

function linkKey(sourceIndex, targetIndex) {
  return String(sourceIndex) + ":" + String(targetIndex);
}

function normalizeTask(rawTask) {
  const task = rawTask || {};
  const language = String(task.language || "");
  const sourceText = String(task.source_text ?? task.original ?? "");
  const targetText = String(task.target_text ?? task.simplification ?? task.simple ?? "");
  return {
    ...task,
    task_id: String(task.task_id ?? task.review_task_id ?? ""),
    source_text: sourceText,
    target_text: targetText,
    candidate_strategy: String(task.candidate_strategy ?? task.candidate_strategy_code ?? ""),
    language,
    source_tokens: normalizeTokens(task.source_tokens, sourceText, language),
    target_tokens: normalizeTokens(task.target_tokens, targetText, language),
    simalign_links: normalizeLinks(task.simalign_links ?? task.alignment),
  };
}

function normalizeEvidence(raw) {
  return (Array.isArray(raw) ? raw : []).flatMap((item) => {
    const tokenIndex = nullableInteger(item?.token_index ?? item?.index);
    const role = String(item?.role || "");
    return tokenIndex === null || !role ? [] : [{ token_index: tokenIndex, role }];
  });
}

function normalizeAnnotation(raw) {
  const annotation = raw || {};
  const verdict = annotation.verdict === "unsure" ? "uncertain" : annotation.verdict;
  return {
    version: integerOr(annotation.version, 0),
    state: annotation.state || "draft",
    verdict: ["correct", "incorrect", "uncertain"].includes(verdict) ? verdict : null,
    corrected_strategy: CORRECTED_STRATEGIES.has(annotation.corrected_strategy)
      ? annotation.corrected_strategy
      : null,
    source_evidence: normalizeEvidence(annotation.source_evidence),
    target_evidence: normalizeEvidence(annotation.target_evidence),
    alignment_judgments: (Array.isArray(annotation.alignment_judgments)
      ? annotation.alignment_judgments
      : []).flatMap((item) => {
      const link = normalizeLink(item);
      const judgment = item?.judgment ?? item?.status;
      return link.source_index === null ||
        link.target_index === null ||
        !["valid", "invalid"].includes(judgment)
        ? []
        : [{ ...link, judgment }];
    }),
    human_added_links: normalizeLinks(annotation.human_added_links),
    notes: String(annotation.notes || "").slice(0, 4000),
  };
}

function annotationPayload() {
  const annotation = state.annotation;
  return {
    verdict: annotation.verdict,
    corrected_strategy: annotation.verdict === "incorrect"
      ? annotation.corrected_strategy
      : null,
    source_evidence: annotation.source_evidence
      .slice()
      .sort((a, b) => a.token_index - b.token_index || a.role.localeCompare(b.role)),
    target_evidence: annotation.target_evidence
      .slice()
      .sort((a, b) => a.token_index - b.token_index || a.role.localeCompare(b.role)),
    alignment_judgments: annotation.alignment_judgments
      .slice()
      .sort((a, b) => a.source_index - b.source_index || a.target_index - b.target_index),
    human_added_links: annotation.human_added_links
      .slice()
      .sort((a, b) => a.source_index - b.source_index || a.target_index - b.target_index),
    notes: annotation.notes,
  };
}

function localDraftKey(taskId) {
  return "phase4a:draft:" + taskId;
}

function storeLocalDraft() {
  if (!state.task || !state.annotation) return;
  try {
    localStorage.setItem(localDraftKey(state.task.task_id), JSON.stringify({
      version: state.annotation.version,
      annotation: annotationPayload(),
      saved_at: new Date().toISOString(),
    }));
  } catch {
    // Server persistence still works when local storage is unavailable.
  }
}

function clearLocalDraft(taskId) {
  try {
    localStorage.removeItem(localDraftKey(taskId));
  } catch {
    // Ignore browser storage restrictions.
  }
}

function restoreLocalDraft(task) {
  try {
    const raw = localStorage.getItem(localDraftKey(task.task_id));
    if (!raw) return null;
    const saved = JSON.parse(raw);
    if (!saved?.annotation) return null;
    return normalizeAnnotation({
      ...saved.annotation,
      version: integerOr(saved.version, task.annotation?.version ?? 0),
    });
  } catch {
    return null;
  }
}

function errorText(error) {
  return error instanceof Error ? error.message : String(error || "Unexpected error.");
}

function setSaveStatus(label, status) {
  elements.saveStatus.textContent = label;
  if (status) elements.saveStatus.dataset.state = status;
  else delete elements.saveStatus.dataset.state;
}

function toast(message, error = false) {
  const node = document.createElement("div");
  node.className = "toast" + (error ? " is-error" : "");
  node.textContent = message;
  elements.toastRegion.append(node);
  window.setTimeout(() => node.remove(), 4200);
}

function markDirty() {
  if (!state.task || !state.annotation || state.submitting) return;
  state.dirty = true;
  state.changeSerial += 1;
  setSaveStatus("Unsaved changes", "saving");
  storeLocalDraft();
  scheduleAutosave();
}

function svgElement(name, attributes = {}) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) {
    node.setAttribute(key, String(value));
  }
  return node;
}
function strategyFor(task = state.task) {
  const code = task?.candidate_strategy;
  return STRATEGIES[code] || {
    label: code || "Unknown strategy",
    definition: "Review the candidate strategy against the sentence pair.",
    instructions: "Select the tokens that provide the clearest linguistic evidence.",
    roles: [["other", "Other evidence", "both", "Select relevant evidence on either side."]],
  };
}

function activeRoleConfig() {
  return strategyFor().roles.find(([role]) => role === state.activeRole) || null;
}

function showAuthenticated(authenticated) {
  elements.loginView.hidden = authenticated;
  elements.appHeader.hidden = !authenticated;
  elements.workspace.hidden = !authenticated;
  if (!authenticated) {
    elements.globalAlert.hidden = true;
    elements.loginUsername.focus();
  }
}

function renderProgress(rawProgress) {
  const progress = unwrapProgress(rawProgress);
  const language = state.task?.language || state.user?.allowed_languages?.[0] || "";
  const languageProgress = progress.by_language?.[language] || null;
  const values = languageProgress || progress;
  const total = Math.max(0, Number(values.total ?? progress.total ?? 0));
  const completed = Math.max(
    0,
    Number(values.submitted ?? values.completed ?? 0),
  );
  const percentage = total ? Math.min(100, Math.round((completed / total) * 100)) : 0;
  elements.progressCount.textContent = String(completed) + " / " + String(total);
  elements.progressTrack.setAttribute("aria-valuenow", String(percentage));
  elements.progressTrack.setAttribute(
    "aria-label",
    "Review progress: " + completed + " of " + total + " complete",
  );
  elements.progressFill.style.width = percentage + "%";
}

function renderStrategy() {
  const strategy = strategyFor();
  elements.strategyCode.textContent = state.task.candidate_strategy || "—";
  elements.reviewHeading.textContent = strategy.label;
  elements.strategyDefinition.textContent = strategy.definition;
  elements.sourceValue.textContent = (state.task.sources || []).join(", ") || "—";
  const agreeingModels = Object.entries(state.task.model_votes || {})
    .filter(([, vote]) => vote === "yes")
    .map(([model]) => MODEL_LABELS[model] || model);
  elements.modelsValue.textContent = agreeingModels.join(", ") || "—";
  elements.strategyInstructions.textContent = strategy.instructions;
  const example = state.task.metadata?.strategy_example ??
    state.task.public_metadata?.strategy_example;
  elements.strategyExample.hidden = !example;
  elements.strategyExample.textContent = example ? String(example) : "";
}

function renderVerdict() {
  const value = state.annotation.verdict;
  for (const button of elements.verdictControl.querySelectorAll("[data-verdict]")) {
    const selected = button.dataset.verdict === value;
    button.setAttribute("aria-checked", String(selected));
    button.tabIndex = selected || !value ? 0 : -1;
  }
  elements.correctionPanel.hidden = value !== "incorrect";
  elements.correctedStrategy.value = state.annotation.corrected_strategy || "";
}

function renderRoles() {
  const roles = strategyFor().roles;
  if (!roles.some(([role]) => role === state.activeRole)) {
    state.activeRole = roles[0]?.[0] || null;
  }
  elements.roleSelector.replaceChildren();
  roles.forEach(([role, label, side, prompt], position) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "role-button";
    button.setAttribute("role", "radio");
    button.setAttribute("aria-checked", String(role === state.activeRole));
    button.dataset.role = role;
    button.dataset.side = side;
    button.style.setProperty("--role-color", "var(--role-" + (position + 1) + ")");
    const swatch = document.createElement("span");
    swatch.className = "role-swatch";
    swatch.setAttribute("aria-hidden", "true");
    const name = document.createElement("span");
    name.className = "role-name";
    name.textContent = label;
    const sideNode = document.createElement("span");
    sideNode.className = "role-side";
    sideNode.textContent = side === "target" ? "simplified" : side;
    const help = document.createElement("small");
    help.textContent = prompt;
    const key = document.createElement("kbd");
    key.textContent = String(position + 1);
    button.append(swatch, name, sideNode, help, key);
    button.addEventListener("click", () => selectRole(role));
    elements.roleSelector.append(button);
  });
  updateRoleHelp();
}

function selectRole(role) {
  const config = strategyFor().roles.find(([candidate]) => candidate === role);
  if (!config) return;
  state.activeRole = role;
  for (const button of elements.roleSelector.querySelectorAll("[data-role]")) {
    button.setAttribute("aria-checked", String(button.dataset.role === role));
  }
  updateRoleHelp();
}

function updateRoleHelp(message) {
  if (message) {
    elements.roleHelp.textContent = message;
    return;
  }
  const config = activeRoleConfig();
  elements.roleHelp.textContent = config
    ? config[3] + " Click again to remove a selection."
    : "Choose a role, then select one or more tokens.";
}

function evidenceFor(side) {
  return side === "source"
    ? state.annotation.source_evidence
    : state.annotation.target_evidence;
}

function roleNumber(role) {
  const index = strategyFor().roles.findIndex(([candidate]) => candidate === role);
  return index >= 0 ? index + 1 : 1;
}

function renderTokenRow(side) {
  const row = side === "source" ? elements.sourceTokens : elements.targetTokens;
  const tokens = side === "source" ? state.task.source_tokens : state.task.target_tokens;
  const language = state.task.language;
  row.replaceChildren();
  row.dir = directionFor(language);
  row.lang = language;
  row.dataset.language = languageBase(language);

  const selectedByIndex = new Map(
    evidenceFor(side).map((selection) => [selection.token_index, selection.role]),
  );
  for (const token of tokens) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "token-button";
    button.dataset.side = side;
    button.dataset.tokenIndex = String(token.index);
    button.dataset.sentenceId = String(token.sentenceId);
    button.setAttribute(
      "aria-label",
      (side === "source" ? "Original" : "Simplified") +
        " token " + token.index + ": " + token.text +
        (token.upos ? ", " + token.upos : ""),
    );
    const tokenText = document.createElement("span");
    tokenText.className = "token-text";
    tokenText.textContent = token.text;
    const pos = document.createElement("span");
    pos.className = "token-pos";
    pos.textContent = token.upos || "";
    const index = document.createElement("span");
    index.className = "token-index";
    index.setAttribute("aria-hidden", "true");
    index.textContent = String(token.index);
    button.append(tokenText, pos, index);
    const role = selectedByIndex.get(token.index);
    if (role) {
      button.dataset.role = role;
      button.dataset.roleNumber = String(roleNumber(role));
      button.setAttribute("aria-pressed", "true");
    } else {
      button.setAttribute("aria-pressed", "false");
    }
    button.addEventListener("click", () => handleTokenActivation(side, token.index));
    button.addEventListener("mouseenter", () => hoverToken(side, token.index, true));
    button.addEventListener("mouseleave", () => hoverToken(side, token.index, false));
    row.append(button);
  }
}

function updateEvidenceHighlights() {
  for (const side of ["source", "target"]) {
    const selectedByIndex = new Map(
      evidenceFor(side).map((selection) => [selection.token_index, selection.role]),
    );
    const row = side === "source" ? elements.sourceTokens : elements.targetTokens;
    for (const button of row.querySelectorAll(".token-button")) {
      const role = selectedByIndex.get(Number(button.dataset.tokenIndex));
      if (role) {
        button.dataset.role = role;
        button.dataset.roleNumber = String(roleNumber(role));
        button.setAttribute("aria-pressed", "true");
      } else {
        delete button.dataset.role;
        delete button.dataset.roleNumber;
        button.setAttribute("aria-pressed", "false");
      }
    }
  }
}

function parseSummary(side) {
  const tokens = side === "source" ? state.task.source_tokens : state.task.target_tokens;
  const metadata = state.task.metadata || state.task.public_metadata || {};
  const sideMetadata = metadata[side] || metadata.syntax?.[side] || {};
  const explicit = state.task[side + "_parse_status"] ??
    metadata[side + "_parse_status"] ??
    sideMetadata.parse_status ??
    sideMetadata.status;
  const tokenStatuses = new Set(tokens.map((token) => token.parseStatus).filter(Boolean));
  let status = explicit || (tokenStatuses.has("fallback") ? "fallback" : null);
  if (!status) status = tokens.some((token) => token.deprel || token.headIndex !== null)
    ? "parsed"
    : "fallback";

  const warnings = [];
  const suppliedWarnings = state.task[side + "_parse_warnings"] ??
    metadata[side + "_parse_warnings"] ??
    sideMetadata.warnings ??
    [];
  for (const warning of Array.isArray(suppliedWarnings) ? suppliedWarnings : [suppliedWarnings]) {
    if (warning) warnings.push(String(warning));
  }
  if (status !== "parsed") {
    warnings.push(
      (side === "source" ? "Original" : "Simplified") +
        " dependency parse is unavailable; fallback tokens remain reviewable.",
    );
  }

  const indices = new Set(tokens.map((token) => token.index));
  for (const token of tokens) {
    if (token.headIndex !== null && !indices.has(token.headIndex)) {
      warnings.push(
        (side === "source" ? "Original" : "Simplified") +
          " token " + token.index + " references missing global head " + token.headIndex + ".",
      );
    }
  }
  return { status, warnings: Array.from(new Set(warnings)) };
}

function renderParseAlerts() {
  elements.parseAlerts.replaceChildren();
  for (const side of ["source", "target"]) {
    const summary = parseSummary(side);
    const status = side === "source"
      ? elements.sourceParseStatus
      : elements.targetParseStatus;
    status.textContent = summary.status === "parsed" ? "Dependency parse" : "Fallback tokens";
    status.classList.toggle("is-error", summary.status !== "parsed");
    for (const warning of summary.warnings) {
      const node = document.createElement("div");
      node.className = "parse-warning";
      node.textContent = warning;
      elements.parseAlerts.append(node);
    }
  }
}

function drawDependencyTree(side) {
  const svg = side === "source" ? elements.sourceTree : elements.targetTree;
  const row = side === "source" ? elements.sourceTokens : elements.targetTokens;
  const tokens = side === "source" ? state.task.source_tokens : state.task.target_tokens;
  svg.replaceChildren();
  const scale = state.zoom || 1;
  const width = Math.max(
    row.scrollWidth,
    row.getBoundingClientRect().width / scale,
    820,
  );
  const height = 132;
  svg.setAttribute("viewBox", "0 0 " + width + " " + height);
  svg.setAttribute("width", String(width));
  svg.setAttribute("height", String(height));

  const markerId = "dependency-arrow-" + side;
  const defs = svgElement("defs");
  const marker = svgElement("marker", {
    id: markerId,
    viewBox: "0 0 8 8",
    refX: 7,
    refY: 4,
    markerWidth: 5,
    markerHeight: 5,
    orient: "auto-start-reverse",
  });
  marker.append(svgElement("path", {
    d: "M 0 0 L 8 4 L 0 8 z",
    class: "dependency-arrow",
  }));
  defs.append(marker);
  svg.append(defs);

  const svgRect = svg.getBoundingClientRect();
  const tokenByIndex = new Map(tokens.map((token) => [token.index, token]));
  const buttonByIndex = new Map(
    Array.from(row.querySelectorAll(".token-button")).map((button) => [
      Number(button.dataset.tokenIndex),
      button,
    ]),
  );
  const xFor = (index) => {
    const rect = buttonByIndex.get(index)?.getBoundingClientRect();
    return rect
      ? (rect.left - svgRect.left + rect.width / 2) / scale
      : null;
  };
  const base = side === "source" ? height - 5 : 5;
  const sign = side === "source" ? -1 : 1;

  for (const token of tokens) {
    const dependentX = xFor(token.index);
    if (dependentX === null) continue;
    if (token.headIndex === null) {
      const root = svgElement("text", {
        x: dependentX,
        y: base + sign * 16,
        class: "root-marker",
      });
      root.textContent = "ROOT";
      svg.append(root);
      continue;
    }
    const head = tokenByIndex.get(token.headIndex);
    const headX = xFor(token.headIndex);
    if (!head || headX === null || head.index === token.index) continue;
    const distance = Math.abs(
      tokens.findIndex((item) => item.index === token.index) -
      tokens.findIndex((item) => item.index === head.index),
    );
    const arcHeight = Math.min(112, 24 + distance * 8);
    const middleX = (headX + dependentX) / 2;
    const elevated = base + sign * arcHeight;
    const pathData = "M " + headX + " " + base +
      " C " + headX + " " + elevated + ", " +
      dependentX + " " + elevated + ", " +
      dependentX + " " + base;
    const group = svgElement("g", {
      class: "dependency-group",
      tabindex: "0",
      "data-dependent-index": token.index,
      "data-head-index": head.index,
      "aria-label": (token.deprel || "dependency") +
        " from " + head.text + " to " + token.text,
    });
    const hitbox = svgElement("path", { d: pathData, class: "dependency-hitbox" });
    const path = svgElement("path", {
      d: pathData,
      class: "dependency-arc",
      "marker-end": "url(#" + markerId + ")",
    });
    const label = svgElement("text", {
      x: middleX,
      y: elevated - sign * 3,
      class: "dependency-label",
    });
    label.textContent = token.deprel || "dep";
    group.append(hitbox, path, label);
    group.addEventListener("mouseenter", () => {
      buttonByIndex.get(token.index)?.classList.add("is-hovered");
      buttonByIndex.get(head.index)?.classList.add("is-hovered");
    });
    group.addEventListener("mouseleave", () => {
      buttonByIndex.get(token.index)?.classList.remove("is-hovered");
      buttonByIndex.get(head.index)?.classList.remove("is-hovered");
    });
    svg.append(group);
  }
}

function judgmentMap() {
  return new Map(
    state.annotation.alignment_judgments.map((item) => [
      linkKey(item.source_index, item.target_index),
      item.judgment,
    ]),
  );
}

function allDisplayLinks() {
  const proposed = new Map(
    state.task.simalign_links.map((link) => [
      linkKey(link.source_index, link.target_index),
      { ...link, origin: "simalign" },
    ]),
  );
  for (const link of state.annotation.human_added_links) {
    proposed.set(linkKey(link.source_index, link.target_index), {
      ...link,
      origin: "human",
    });
  }
  return Array.from(proposed.values()).sort(
    (a, b) => a.source_index - b.source_index || a.target_index - b.target_index,
  );
}

function renderAlignments() {
  elements.links.replaceChildren();
  const links = allDisplayLinks();
  elements.linksEmpty.hidden = links.length > 0;
  const width = Math.max(elements.linkRegion.clientWidth, 820);
  const height = Math.max(elements.linkRegion.clientHeight, 192);
  elements.links.setAttribute("viewBox", "0 0 " + width + " " + height);
  const regionRect = elements.linkRegion.getBoundingClientRect();
  const scale = state.zoom || 1;
  const statuses = judgmentMap();

  for (const link of links) {
    const sourceButton = elements.sourceTokens.querySelector(
      '[data-token-index="' + link.source_index + '"]',
    );
    const targetButton = elements.targetTokens.querySelector(
      '[data-token-index="' + link.target_index + '"]',
    );
    if (!sourceButton || !targetButton) continue;
    const sourceRect = sourceButton.getBoundingClientRect();
    const targetRect = targetButton.getBoundingClientRect();
    const sourceX = (
      sourceRect.left - regionRect.left + sourceRect.width / 2
    ) / scale;
    const targetX = (
      targetRect.left - regionRect.left + targetRect.width / 2
    ) / scale;
    const middleY = height / 2;
    const pathData = "M " + sourceX + " 1 C " + sourceX + " " + middleY +
      ", " + targetX + " " + middleY + ", " + targetX + " " + (height - 1);
    const key = linkKey(link.source_index, link.target_index);
    const status = link.origin === "human" ? "valid" : (statuses.get(key) || "unreviewed");
    const sourceToken = state.task.source_tokens.find(
      (token) => token.index === link.source_index,
    );
    const targetToken = state.task.target_tokens.find(
      (token) => token.index === link.target_index,
    );
    const group = svgElement("g", {
      class: "alignment-link",
      tabindex: "0",
      role: "button",
      "data-source-index": link.source_index,
      "data-target-index": link.target_index,
      "data-status": status,
      "data-origin": link.origin,
      "aria-label": (link.origin === "human" ? "Human-added" : "SimAlign") +
        " link, " + (sourceToken?.text || link.source_index) + " to " +
        (targetToken?.text || link.target_index) + ", " + status +
        ". Activate to " + (link.origin === "human" ? "remove" : "change judgment") + ".",
    });
    group.append(
      svgElement("path", { d: pathData, class: "alignment-hitbox" }),
      svgElement("path", { d: pathData, class: "alignment-path" }),
    );
    group.addEventListener("click", () => activateAlignment(link));
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activateAlignment(link);
      }
    });
    group.addEventListener("mouseenter", () => hoverAlignment(link, true));
    group.addEventListener("mouseleave", () => hoverAlignment(link, false));
    elements.links.append(group);
  }
}

function redrawCanvas() {
  if (!state.task || elements.viewport.hidden) return;
  drawDependencyTree("source");
  drawDependencyTree("target");
  renderAlignments();
}

function renderTask() {
  const task = state.task;
  elements.loading.hidden = true;
  elements.empty.hidden = true;
  elements.viewport.hidden = false;
  elements.taskIdentity.textContent = task.task_id;
  elements.languageBadge.textContent = task.language || "—";
  elements.reviewerName.textContent = state.user?.display_name ||
    state.user?.username ||
    "Reviewer";
  renderStrategy();
  renderVerdict();
  renderRoles();
  renderTokenRow("source");
  renderTokenRow("target");
  renderParseAlerts();
  elements.notes.value = state.annotation.notes;
  elements.notesCount.textContent = String(state.annotation.notes.length);
  setMode(state.mode, false);
  requestAnimationFrame(redrawCanvas);
}
function hoverToken(side, tokenIndex, active) {
  const tree = side === "source" ? elements.sourceTree : elements.targetTree;
  for (const group of tree.querySelectorAll(".dependency-group")) {
    const related = Number(group.dataset.dependentIndex) === tokenIndex ||
      Number(group.dataset.headIndex) === tokenIndex;
    if (related) group.classList.toggle("is-hovered", active);
  }
  const attribute = side === "source" ? "sourceIndex" : "targetIndex";
  for (const group of elements.links.querySelectorAll(".alignment-link")) {
    if (Number(group.dataset[attribute]) === tokenIndex) {
      group.classList.toggle("is-hovered", active);
    }
  }
}

function hoverAlignment(link, active) {
  const source = elements.sourceTokens.querySelector(
    '[data-token-index="' + link.source_index + '"]',
  );
  const target = elements.targetTokens.querySelector(
    '[data-token-index="' + link.target_index + '"]',
  );
  source?.classList.toggle("is-link-endpoint", active);
  target?.classList.toggle("is-link-endpoint", active);
}

function handleTokenActivation(side, tokenIndex) {
  if (state.mode === "alignment") {
    chooseAlignmentEndpoint(side, tokenIndex);
    return;
  }
  const role = activeRoleConfig();
  if (!role) return;
  const allowedSide = role[2];
  if (allowedSide !== "both" && allowedSide !== side) {
    updateRoleHelp(
      role[1] + " applies to the " +
        (allowedSide === "source" ? "original" : "simplified") + " sentence.",
    );
    return;
  }
  const selections = evidenceFor(side);
  const existing = selections.find(
    (selection) => selection.token_index === tokenIndex && selection.role === role[0],
  );
  const withoutToken = selections.filter((selection) => selection.token_index !== tokenIndex);
  if (!existing) withoutToken.push({ token_index: tokenIndex, role: role[0] });
  if (side === "source") state.annotation.source_evidence = withoutToken;
  else state.annotation.target_evidence = withoutToken;
  updateEvidenceHighlights();
  updateRoleHelp(
    (existing ? "Removed" : "Selected") + " token " + tokenIndex +
      " as " + role[1].toLowerCase() + ".",
  );
  markDirty();
}

function updatePendingEndpoint() {
  for (const button of document.querySelectorAll(".token-button")) {
    const selected = state.pendingEndpoint &&
      button.dataset.side === state.pendingEndpoint.side &&
      Number(button.dataset.tokenIndex) === state.pendingEndpoint.index;
    button.classList.toggle("is-alignment-pending", Boolean(selected));
  }
}

function clearPendingEndpoint(message = "") {
  state.pendingEndpoint = null;
  updatePendingEndpoint();
  if (message) {
    elements.modeInstructions.textContent = message;
    elements.linkStatus.textContent = message;
  } else if (state.mode === "alignment") {
    elements.modeInstructions.textContent =
      "Choose one original token and one simplified token to add a missing link; activate a line to judge it.";
  }
}

function chooseAlignmentEndpoint(side, tokenIndex) {
  if (!state.pendingEndpoint || state.pendingEndpoint.side === side) {
    state.pendingEndpoint = { side, index: tokenIndex };
    updatePendingEndpoint();
    const other = side === "source" ? "simplified" : "original";
    const message = "Token " + tokenIndex + " selected. Choose a " + other + " token.";
    elements.modeInstructions.textContent = message;
    elements.linkStatus.textContent = message;
    return;
  }

  const sourceIndex = side === "source" ? tokenIndex : state.pendingEndpoint.index;
  const targetIndex = side === "target" ? tokenIndex : state.pendingEndpoint.index;
  const key = linkKey(sourceIndex, targetIndex);
  if (allDisplayLinks().some((link) =>
    linkKey(link.source_index, link.target_index) === key)) {
    clearPendingEndpoint("That link already exists. Activate its line to change its state.");
    return;
  }

  state.annotation.human_added_links.push({
    source_index: sourceIndex,
    target_index: targetIndex,
  });
  clearPendingEndpoint(
    "Added link from original token " + sourceIndex +
      " to simplified token " + targetIndex + ".",
  );
  markDirty();
  renderAlignments();
}

function activateAlignment(link) {
  const key = linkKey(link.source_index, link.target_index);
  if (link.origin === "human") {
    state.annotation.human_added_links = state.annotation.human_added_links.filter(
      (item) => linkKey(item.source_index, item.target_index) !== key,
    );
    elements.linkStatus.textContent =
      "Removed human-added link " + link.source_index + " to " + link.target_index + ".";
    markDirty();
    renderAlignments();
    return;
  }

  const statuses = ["unreviewed", "valid", "invalid"];
  const judgments = judgmentMap();
  const current = judgments.get(key) || "unreviewed";
  const next = statuses[(statuses.indexOf(current) + 1) % statuses.length];
  state.annotation.alignment_judgments = state.annotation.alignment_judgments.filter(
    (item) => linkKey(item.source_index, item.target_index) !== key,
  );
  if (next !== "unreviewed") {
    state.annotation.alignment_judgments.push({
      source_index: link.source_index,
      target_index: link.target_index,
      judgment: next,
    });
  }
  elements.linkStatus.textContent =
    "Alignment " + link.source_index + " to " + link.target_index +
      " marked " + next + ".";
  markDirty();
  renderAlignments();
}

function setMode(mode, focus = true) {
  state.mode = mode === "alignment" ? "alignment" : "evidence";
  const alignment = state.mode === "alignment";
  elements.canvas.classList.toggle("mode-alignment", alignment);
  elements.evidenceMode.classList.toggle("is-active", !alignment);
  elements.alignmentMode.classList.toggle("is-active", alignment);
  elements.evidenceMode.setAttribute("aria-pressed", String(!alignment));
  elements.alignmentMode.setAttribute("aria-pressed", String(alignment));
  elements.modeInstructions.textContent = alignment
    ? "Choose one original token and one simplified token to add a missing link; activate a line to cycle unreviewed, valid, and invalid."
    : "Select tokens that provide evidence for the active strategy role.";
  if (!alignment) clearPendingEndpoint();
  if (focus) {
    (alignment ? elements.alignmentMode : elements.evidenceMode).focus();
  }
}

function setZoom(value) {
  state.zoom = Math.min(1.5, Math.max(0.7, Math.round(value * 10) / 10));
  elements.canvas.style.setProperty("--canvas-scale", String(state.zoom));
  elements.zoomValue.value = Math.round(state.zoom * 100) + "%";
  requestAnimationFrame(redrawCanvas);
}

function clearGlobalAlert() {
  state.conflict = null;
  elements.globalAlert.replaceChildren();
  elements.globalAlert.hidden = true;
}

function showGlobalError(message) {
  elements.globalAlert.replaceChildren();
  const text = document.createElement("span");
  text.textContent = message;
  elements.globalAlert.append(text);
  elements.globalAlert.hidden = false;
}

async function showVersionConflict(error) {
  window.clearTimeout(state.autosaveTimer);
  state.autosaveTimer = null;
  let serverTask = null;
  try {
    serverTask = normalizeTask(unwrapTask(await api.task(state.task.task_id)));
  } catch {
    // The explicit conflict still remains actionable if refresh fails.
  }
  state.conflict = {
    serverTask,
    currentVersion: integerOr(
      error?.details?.current_version ??
        error?.details?.details?.current_version ??
        serverTask?.annotation?.version,
      state.annotation.version,
    ),
  };
  elements.globalAlert.replaceChildren();
  const message = document.createElement("span");
  message.textContent =
    "This draft changed in another tab. Your local edits have not been overwritten.";
  const actions = document.createElement("span");
  actions.className = "alert-actions";
  const reload = document.createElement("button");
  reload.type = "button";
  reload.className = "text-button";
  reload.textContent = "Load server draft";
  reload.addEventListener("click", () => {
    if (state.conflict?.serverTask?.annotation) {
      state.task = state.conflict.serverTask;
      state.annotation = normalizeAnnotation(state.conflict.serverTask.annotation);
      state.dirty = false;
      clearLocalDraft(state.task.task_id);
      clearGlobalAlert();
      renderTask();
      setSaveStatus("Server draft loaded", "saved");
    } else {
      loadNextTask();
    }
  });
  const keep = document.createElement("button");
  keep.type = "button";
  keep.className = "text-button";
  keep.textContent = "Keep local edits";
  keep.addEventListener("click", () => {
    state.annotation.version = state.conflict.currentVersion;
    state.dirty = true;
    clearGlobalAlert();
    storeLocalDraft();
    setSaveStatus("Local edits retained", "saving");
  });
  actions.append(reload, keep);
  elements.globalAlert.append(message, actions);
  elements.globalAlert.hidden = false;
  setSaveStatus("Version conflict", "error");
}

function scheduleAutosave() {
  window.clearTimeout(state.autosaveTimer);
  if (!state.dirty || state.conflict || state.submitting) return;
  state.autosaveTimer = window.setTimeout(() => {
    saveDraft({ quiet: true });
  }, AUTOSAVE_DELAY_MS);
}

async function saveDraft({ quiet = false } = {}) {
  if (!state.task || !state.annotation || !state.dirty || state.saving || state.conflict) {
    if (!quiet && !state.dirty) toast("Draft is already saved.");
    return false;
  }
  window.clearTimeout(state.autosaveTimer);
  state.autosaveTimer = null;
  state.saving = true;
  elements.saveButton.disabled = true;
  setSaveStatus("Saving…", "saving");
  const serial = state.changeSerial;
  const expectedVersion = state.annotation.version;
  try {
    const response = await api.saveDraft(
      state.task.task_id,
      annotationPayload(),
      expectedVersion,
    );
    const updated = unwrapAnnotation(response);
    state.annotation.version = integerOr(updated?.version, expectedVersion + 1);
    if (serial === state.changeSerial) {
      state.dirty = false;
      clearLocalDraft(state.task.task_id);
      setSaveStatus("Draft saved", "saved");
      if (!quiet) toast("Draft saved.");
    } else {
      state.dirty = true;
      storeLocalDraft();
      setSaveStatus("New changes pending", "saving");
      scheduleAutosave();
    }
    return true;
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      await showVersionConflict(error);
    } else if (error instanceof ApiError && error.status === 401) {
      await returnToLogin("Your session expired. Sign in again; the local draft is safe.");
    } else {
      setSaveStatus("Save failed", "error");
      if (!quiet) toast(errorText(error), true);
      storeLocalDraft();
    }
    return false;
  } finally {
    state.saving = false;
    elements.saveButton.disabled = false;
  }
}

function validateForSubmit() {
  if (!state.annotation.verdict) return "Choose correct, incorrect, or uncertain.";
  if (
    state.annotation.verdict === "incorrect" &&
    !CORRECTED_STRATEGIES.has(state.annotation.corrected_strategy)
  ) {
    return "Select the corrected strategy, NONE, MULTIPLE, or OTHER.";
  }
  if (state.annotation.verdict === "correct") {
    for (const [role, label, side] of strategyFor().roles) {
      const found = side === "both"
        ? state.annotation.source_evidence.some((item) => item.role === role) ||
          state.annotation.target_evidence.some((item) => item.role === role)
        : evidenceFor(side).some((item) => item.role === role);
      if (!found) return "Select at least one token for " + label.toLowerCase() + ".";
    }
  }
  return null;
}

function setActionsDisabled(disabled) {
  elements.submitButton.disabled = disabled;
  elements.skipButton.disabled = disabled;
  elements.saveButton.disabled = disabled;
}

async function submitAndNext() {
  if (state.saving) {
    toast("Wait for the current save to finish.", true);
    return;
  }
  const validation = validateForSubmit();
  if (validation) {
    toast(validation, true);
    return;
  }
  state.submitting = true;
  setActionsDisabled(true);
  window.clearTimeout(state.autosaveTimer);
  setSaveStatus("Submitting…", "saving");
  try {
    const response = await api.submit(
      state.task.task_id,
      annotationPayload(),
      state.annotation.version,
    );
    const updated = unwrapAnnotation(response);
    state.annotation.version = integerOr(updated?.version, state.annotation.version + 1);
    clearLocalDraft(state.task.task_id);
    state.dirty = false;
    toast("Annotation submitted.");
    stopLeaseRenewal();
    showSubmissionResult(response.result || {});
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      await showVersionConflict(error);
    } else if (error instanceof ApiError && error.status === 401) {
      await returnToLogin("Your session expired. Sign in again.");
    } else {
      toast(errorText(error), true);
      setSaveStatus("Submit failed", "error");
    }
  } finally {
    state.submitting = false;
    setActionsDisabled(false);
  }
}

async function deferAndNext() {
  if (!state.task || !state.annotation || state.submitting) return;
  if (state.saving) {
    toast("Wait for the current save to finish.", true);
    return;
  }
  if (state.dirty) {
    const saved = await saveDraft({ quiet: true });
    if (!saved) return;
  }
  state.submitting = true;
  setActionsDisabled(true);
  try {
    await api.skip(
      state.task.task_id,
      "review_later",
      state.annotation.notes,
      state.annotation.version,
    );
    clearLocalDraft(state.task.task_id);
    state.dirty = false;
    toast("Pair kept in the queue for later.");
    await loadNextTask();
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      await showVersionConflict(error);
    } else {
      toast(errorText(error), true);
    }
  } finally {
    state.submitting = false;
    setActionsDisabled(false);
  }
}

function showLoading() {
  elements.loading.hidden = false;
  elements.empty.hidden = true;
  elements.viewport.hidden = true;
  elements.taskIdentity.textContent = "—";
}

function showEmptyQueue() {
  stopLeaseRenewal();
  state.task = null;
  state.annotation = null;
  elements.loading.hidden = true;
  elements.viewport.hidden = true;
  elements.empty.hidden = false;
  elements.languageBadge.textContent = state.user?.allowed_languages?.[0] || "—";
  setSaveStatus("Queue complete", "saved");
}

function stopLeaseRenewal() {
  if (state.leaseTimer !== null) window.clearInterval(state.leaseTimer);
  state.leaseTimer = null;
}

function startLeaseRenewal() {
  stopLeaseRenewal();
  const taskId = state.task?.task_id;
  if (!taskId) return;
  state.leaseTimer = window.setInterval(async () => {
    if (!state.user || state.task?.task_id !== taskId) {
      stopLeaseRenewal();
      return;
    }
    try {
      await api.renewLease(taskId);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        await returnToLogin("Your session expired. Sign in again.");
        return;
      }
      setSaveStatus("Lease renewal failed", "error");
    }
  }, LEASE_RENEWAL_INTERVAL_MS);
}


async function refreshProgress() {
  try {
    renderProgress(await api.progress(state.filters));
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) {
      toast("Progress could not be refreshed.", true);
    }
  }
}

async function loadNextTask() {
  stopLeaseRenewal();
  if (state.loadController) state.loadController.abort();
  state.loadController = new AbortController();
  clearGlobalAlert();
  clearPendingEndpoint();
  showLoading();
  try {
    const [taskPayload, progressPayload] = await Promise.all([
      api.nextTask(state.filters, state.loadController.signal),
      api.progress(state.filters, state.loadController.signal),
    ]);
    renderProgress(progressPayload);
    const rawTask = unwrapTask(taskPayload);
    if (!rawTask) {
      showEmptyQueue();
      return;
    }
    state.task = normalizeTask(rawTask);
    const serverAnnotation = normalizeAnnotation(rawTask.annotation);
    const localAnnotation = restoreLocalDraft(state.task);
    if (localAnnotation) {
      localAnnotation.version = serverAnnotation.version;
      state.annotation = localAnnotation;
      state.dirty = true;
      state.changeSerial += 1;
      setSaveStatus("Local draft restored", "saving");
      toast("Restored unsaved changes from this browser.");
      scheduleAutosave();
    } else {
      state.annotation = serverAnnotation;
      state.dirty = false;
      setSaveStatus("Draft loaded", "saved");
    }
    state.activeRole = strategyFor().roles[0]?.[0] || null;
    state.pendingEndpoint = null;
    state.zoom = 1;
    elements.canvas.style.setProperty("--canvas-scale", "1");
    elements.zoomValue.value = "100%";
    renderTask();
    startLeaseRenewal();
  } catch (error) {
    if (error.name === "AbortError") return;
    if (error instanceof ApiError && error.status === 401) {
      await returnToLogin("Your session expired. Sign in again.");
      return;
    }
    elements.loading.hidden = true;
    showGlobalError(errorText(error));
    setSaveStatus("Load failed", "error");
  }
}

function setFilterCount() {
  const count = state.filters.sources.length + state.filters.models.length;
  elements.filtersCount.textContent = String(count);
  elements.filtersCount.hidden = count === 0;
}

function renderFilterChoices(container, values, selected, kind) {
  container.replaceChildren();
  values.forEach((value) => {
    const label = document.createElement("label");
    label.className = "filter-option";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = kind;
    input.value = value;
    input.checked = selected.includes(value);
    const textNode = document.createElement("span");
    textNode.textContent = kind === "models" ? (MODEL_LABELS[value] || value) : value;
    label.append(input, textNode);
    container.append(label);
  });
}

async function openFilters() {
  try {
    state.filterOptions = await api.queueFilters();
    renderFilterChoices(
      elements.sourceFilters,
      state.filterOptions.sources || [],
      state.filters.sources,
      "sources",
    );
    renderFilterChoices(
      elements.modelFilters,
      state.filterOptions.models || [],
      state.filters.models,
      "models",
    );
    elements.filtersDialog.showModal();
  } catch (error) {
    toast(errorText(error), true);
  }
}

function selectedFilterValues(name) {
  return Array.from(elements.filtersForm.querySelectorAll(`input[name="${name}"]:checked`))
    .map((input) => input.value);
}

function showSubmissionResult(result) {
  elements.resultSource.textContent = (result.sources || []).join(", ") || "—";
  elements.resultModels.replaceChildren();
  const votes = result.model_votes || {};
  ["gemma", "qwen", "e5", "xlmr"].forEach((model) => {
    const vote = String(votes[model] || "unknown").toLowerCase();
    const card = document.createElement("div");
    card.className = `model-vote is-${vote}`;
    const name = document.createElement("strong");
    name.textContent = model.toUpperCase();
    const value = document.createElement("div");
    value.textContent = vote === "yes" ? "Agrees" : vote === "no" ? "Does not agree" : "No vote";
    card.append(name, value);
    elements.resultModels.append(card);
  });
  elements.resultDialog.showModal();
}

async function openPrevious() {
  elements.previousList.replaceChildren();
  elements.previousLoading.hidden = false;
  elements.previousEmpty.hidden = true;
  elements.previousDialog.showModal();
  try {
    const payload = await api.mine(["submitted"]);
    const rows = payload.annotations || [];
    elements.previousLoading.hidden = true;
    elements.previousEmpty.hidden = rows.length > 0;
    rows.forEach((row) => {
      const item = document.createElement("article");
      item.className = "previous-item";
      const strategy = document.createElement("strong");
      strategy.textContent = row.candidate_strategy;
      const copy = document.createElement("div");
      copy.className = "previous-copy";
      const source = document.createElement("small");
      let sources = [];
      try { sources = JSON.parse(row.sources_json || "[]"); } catch { sources = []; }
      source.textContent = sources.join(", ") || "Unknown source";
      const pair = document.createElement("p");
      pair.textContent = `${row.source_text} → ${row.target_text}`;
      copy.append(source, pair);
      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "button button-secondary";
      edit.textContent = "Edit";
      edit.addEventListener("click", async () => {
        edit.disabled = true;
        try {
          if (state.dirty) await saveDraft({ quiet: true });
          const response = await api.resume(row.task_id, row.version);
          elements.previousDialog.close();
          activateTask(unwrapTask(response), "Previous submission reopened");
        } catch (error) {
          toast(errorText(error), true);
          edit.disabled = false;
        }
      });
      item.append(strategy, copy, edit);
      elements.previousList.append(item);
    });
  } catch (error) {
    elements.previousLoading.hidden = true;
    toast(errorText(error), true);
  }
}

function activateTask(rawTask, status = "Draft loaded") {
  state.task = normalizeTask(rawTask);
  state.annotation = normalizeAnnotation(rawTask.annotation);
  state.dirty = false;
  state.activeRole = strategyFor().roles[0]?.[0] || null;
  state.pendingEndpoint = null;
  state.zoom = 1;
  elements.canvas.style.setProperty("--canvas-scale", "1");
  elements.zoomValue.value = "100%";
  setSaveStatus(status, "saved");
  renderTask();
  startLeaseRenewal();
}

async function completeLogin(payload) {
  state.user = payload?.user ?? payload?.data?.user ?? payload;
  elements.s1ProjectLink.hidden = !(state.user?.role === "admin" || ["en", "es", "fr"].some((code) => state.user?.allowed_languages?.includes(code)));
  showAuthenticated(true);
  elements.reviewerName.textContent =
    state.user?.display_name || state.user?.username || "Reviewer";
  await loadNextTask();
}

async function returnToLogin(message = "") {
  stopLeaseRenewal();
  window.clearTimeout(state.autosaveTimer);
  if (state.dirty) storeLocalDraft();
  state.user = null;
  state.task = null;
  state.annotation = null;
  showAuthenticated(false);
  elements.loginError.textContent = message;
  elements.loginError.hidden = !message;
  elements.loginPassword.value = "";
}

async function bootstrap() {
  bindEvents();
  showAuthenticated(false);
  try {
    await completeLogin(await api.me());
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) {
      elements.loginError.textContent = errorText(error);
      elements.loginError.hidden = false;
    }
  }
}

function bindEvents() {
  elements.loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    elements.loginButton.disabled = true;
    elements.loginError.hidden = true;
    try {
      await completeLogin(
        await api.login(elements.loginUsername.value, elements.loginPassword.value),
      );
      elements.loginPassword.value = "";
    } catch (error) {
      elements.loginError.textContent = errorText(error);
      elements.loginError.hidden = false;
      elements.loginPassword.select();
    } finally {
      elements.loginButton.disabled = false;
    }
  });

  elements.filtersButton.addEventListener("click", openFilters);
  elements.filtersForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (state.saving) {
      toast("Wait for the current save to finish.", true);
      return;
    }
    if (state.dirty) {
      const saved = await saveDraft({ quiet: true });
      if (!saved) return;
    }
    state.filters = {
      sources: selectedFilterValues("sources"),
      models: selectedFilterValues("models"),
    };
    setFilterCount();
    elements.filtersDialog.close();
    await loadNextTask();
    toast("Filters applied.");
  });
  elements.clearFilters.addEventListener("click", () => {
    elements.filtersForm.querySelectorAll('input[type="checkbox"]:not(:disabled)').forEach((input) => {
      input.checked = false;
    });
  });
  elements.previousButton.addEventListener("click", openPrevious);
  elements.previousClose.addEventListener("click", () => elements.previousDialog.close());
  elements.resultNext.addEventListener("click", () => {
    elements.resultDialog.close();
    loadNextTask();
  });
  elements.resultDialog.addEventListener("cancel", (event) => event.preventDefault());

  elements.logoutButton.addEventListener("click", async () => {
    if (state.dirty) await saveDraft({ quiet: true });
    try {
      await api.logout();
    } catch {
      // Returning to login is safe even if the server already ended the session.
    }
    await returnToLogin();
  });

  elements.verdictControl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-verdict]");
    if (!button || !state.annotation) return;
    state.annotation.verdict = button.dataset.verdict;
    if (state.annotation.verdict !== "incorrect") {
      state.annotation.corrected_strategy = null;
    }
    renderVerdict();
    markDirty();
  });

  elements.verdictControl.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
    const buttons = Array.from(elements.verdictControl.querySelectorAll("[data-verdict]"));
    const current = Math.max(0, buttons.indexOf(document.activeElement));
    const delta = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1;
    const next = buttons[(current + delta + buttons.length) % buttons.length];
    event.preventDefault();
    next.focus();
    next.click();
  });

  elements.correctedStrategy.addEventListener("change", () => {
    state.annotation.corrected_strategy = elements.correctedStrategy.value || null;
    markDirty();
  });

  elements.clearEvidence.addEventListener("click", () => {
    state.annotation.source_evidence = [];
    state.annotation.target_evidence = [];
    updateEvidenceHighlights();
    updateRoleHelp("All evidence selections cleared.");
    markDirty();
  });

  elements.notes.addEventListener("input", () => {
    state.annotation.notes = elements.notes.value.slice(0, 4000);
    elements.notesCount.textContent = String(state.annotation.notes.length);
    markDirty();
  });

  elements.evidenceMode.addEventListener("click", () => setMode("evidence"));
  elements.alignmentMode.addEventListener("click", () => setMode("alignment"));
  elements.zoomOut.addEventListener("click", () => setZoom(state.zoom - 0.1));
  elements.zoomIn.addEventListener("click", () => setZoom(state.zoom + 0.1));
  elements.saveButton.addEventListener("click", () => saveDraft());
  elements.submitButton.addEventListener("click", submitAndNext);
  elements.skipButton.addEventListener("click", deferAndNext);
  elements.refreshQueue.addEventListener("click", loadNextTask);
  elements.shortcutsButton.addEventListener("click", () => {
    elements.shortcutsDialog.showModal();
  });

  document.addEventListener("keydown", (event) => {
    if (!state.task || event.defaultPrevented) return;
    const editing = ["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName) ||
      event.target.isContentEditable;
    if (event.key === "Escape" && state.pendingEndpoint) {
      event.preventDefault();
      clearPendingEndpoint("Pending link endpoints cleared.");
      return;
    }
    if (editing || elements.shortcutsDialog.open || elements.filtersDialog.open ||
        elements.previousDialog.open || elements.resultDialog.open) return;
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      submitAndNext();
      return;
    }
    const key = event.key.toLowerCase();
    const verdicts = { c: "correct", x: "incorrect", u: "uncertain" };
    if (verdicts[key]) {
      event.preventDefault();
      elements.verdictControl.querySelector(
        '[data-verdict="' + verdicts[key] + '"]',
      )?.click();
    } else if (key === "e") {
      event.preventDefault();
      setMode("evidence");
    } else if (key === "a") {
      event.preventDefault();
      setMode("alignment");
    } else if (key === "s") {
      event.preventDefault();
      saveDraft();
    } else if (key === "k") {
      event.preventDefault();
      elements.skipButton.click();
    } else if (/^[1-9]$/.test(key)) {
      const role = strategyFor().roles[Number(key) - 1]?.[0];
      if (role) {
        event.preventDefault();
        selectRole(role);
      }
    } else if (key === "?") {
      event.preventDefault();
      elements.shortcutsDialog.showModal();
    }
  });

  let resizeFrame = null;
  window.addEventListener("resize", () => {
    window.cancelAnimationFrame(resizeFrame);
    resizeFrame = window.requestAnimationFrame(redrawCanvas);
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && state.dirty) saveDraft({ quiet: true });
  });
  window.addEventListener("beforeunload", () => {
    if (state.dirty) storeLocalDraft();
  });
}

bootstrap();
