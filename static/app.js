const byId = id => document.getElementById(id);
const canvas = byId("graph");
const ctx = canvas.getContext("2d");
const colors = { Person: "#68e0cd", Organisation: "#d1a6ff", Location: "#f4cd86", Item: "#91bdff" };
const views = {
  demo: ["Fictional report network", "Explore 36 fictional reports with labeled identities and relationship examples."],
  benchmark: ["Hand-written report network", "Review report evidence and candidate identities without preassigned record IDs."],
  lead: ["Lead Finder", "Review custody evidence in the fictional missing-recorder case."],
  montagna: ["Montagna network", "Explore meetings and calls from the published investigation dataset."],
  custom: ["Uploaded report network", "Review extracted entities and the sentences that support each finding."],
  evaluation: ["Extraction evaluation", "Precision, recall, and F1 on held-out fictional reports."]
};
let data, nodes, view, panel = "entities", selected, requestNumber = 0;
let zoom = 1, pan = [0, 0], drag;
const cases = new Map();
let reviewing = false;
let revealedLeadAnswer = null;
let pathEnds = [];
function element(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
function button(text, action, subtitle) {
  const node = element("button", text, "item");
  node.type = "button";
  if (subtitle) node.append(element("small", subtitle));
  node.onclick = action;
  return node;
}
function toggleActive(selector, key, value) {
  document.querySelectorAll(selector).forEach(node => {
    const active = node.dataset[key] === value;
    node.classList.toggle("active", active);
    node.setAttribute("aria-pressed", active);
  });
}
async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || "The request failed.");
  return value;
}
function setHeading(next) {
  view = next;
  byId("save-case").disabled = next === "evaluation";
  byId("title").textContent = views[next][0];
  byId("description").textContent = views[next][1];
  toggleActive("[data-view]", "view", next);
  byId("workspace").hidden = next === "evaluation";
  document.querySelector('[data-panel="leads"]').hidden = next !== "lead";
  document.querySelector('[data-panel="timeline"]').hidden = next !== "lead";
  byId("weight-control").hidden = next !== "montagna";
  byId("item-key").hidden = next !== "lead";
  byId("evaluation").hidden = next !== "evaluation";
}
function showGraph(next, result) {
  cases.set(next, result);
  if (next === "custom") document.querySelector('[data-view="custom"]').hidden = false;
  data = result;
  pathEnds = [];
  byId("weighted").checked = false;
  nodes = new Map(result.nodes.map(node => [node.id, node]));
  selected = null;
  panel = next === "lead" ? "leads" : "entities";
  byId("search").value = "";
  const types = next === "lead" ? [...new Set(result.edges.map(edge => edge.type))] : ["Meeting", "Communication", "Association"];
  byId("filter").replaceChildren(...[["", "All types"], ...types.map(type => [type, type])].map(([value, label]) => {
    const option = element("option", label);
    option.value = value;
    return option;
  }));
  setHeading(next);
  byId("model").textContent = next === "montagna" ? "Source · Montagna Operation / Zenodo" : result.model;
  byId("status").textContent = result.nodes.length ? "" : "No entities were extracted from these reports.";
  stats([["Entities", result.nodes.length], ["Evidence rows", result.edges.length], ["Communities", result.communities]]);
  reset();
  inspect();
}
function stats(values) {
  byId("stats").replaceChildren(...values.map(([label, value]) => {
    const card = element("div", undefined, "stat");
    card.append(element("strong", value), element("span", label));
    return card;
  }));
}
async function load(next) {
  const token = ++requestNumber;
  if (cases.has(next)) return showGraph(next, cases.get(next));
  byId("status").textContent = "Loading…";
  try {
    const result = await fetchJSON("/api/" + next);
    if (token !== requestNumber) return;
    if (next !== "evaluation") return showGraph(next, result);
    setHeading(next);
    stats([["Field reports", result.release.field.current.reports], ["Custody cases", result.release.custody.length]]);
    byId("status").textContent = "";
    const active = result.training.selected === "pilot" ? result.training.pilot : result.training.pretrained;
    byId("model").textContent = "Active detector · " + active.model;
    const contextualBefore = scoreTable("Known contextual cases · Earlier rules", result.contextual.before);
    const contextualAfter = scoreTable("Known contextual cases · Current regression", result.contextual.after);
    const regression = metricsTable("Original test reused for regression checks", [
      ["Before contextual changes", result.contextual.regression_before],
      ["After contextual changes", result.contextual.regression_after]
    ]);
    const pretrained = scoreTable("Final NER test · Pretrained model", result.training.pretrained);
    const fineTuned = result.training.pilot
      ? scoreTable("Final NER test · Fine-tuned model", result.training.pilot)
      : element("p", "Train the pilot to see its comparison.", "muted");
    const previous = scoreTable("Earlier rules retest · Previous rules", result.baseline);
    const updated = scoreTable("Earlier rules retest · Expanded rules", result);
    const diagnostic = metricsTable("Diagnostic on " + result.diagnostic.reports + " earlier reports", [
      ["Previous rules with detected entities", result.diagnostic.previous.predicted],
      ["Previous rules with human-labeled entities", result.diagnostic.previous.reference],
      ["Expanded rules with detected entities", result.diagnostic.updated.predicted],
      ["Expanded rules with human-labeled entities", result.diagnostic.updated.reference]
    ]);
    const diagnosis = scoreTable("Development set · Hand-written reports", result.diagnosis);
    const templates = scoreTable("Development comparison · Templates with IDs", result.templates);
    const field = result.release.field;
    const custody = element("section", undefined, "score-section");
    custody.append(element("h2", "Custody validation · three fictional cases"));
    for (const row of result.release.custody) {
      custody.append(element("p", row.case + " · Expected " + (row.expected || "abstain")
        + " · Result " + (row.actual || "abstain") + " · " + row.reason
        + (row.citations ? " Citations matched." : " Check citations.")));
    }
    byId("evaluation").replaceChildren(metricsTable("Frozen field set · 16 fictional reports", [
      ["Previous relationships", field.previous.relationships], ["Current relationships", field.current.relationships],
      ...Object.entries(field.current.types)]), custody, contextualBefore, contextualAfter,
      element("p", "The contextual and original model tests now include examples used to develop rules. The field set was frozen before this update. All three sets use fictional reports.", "muted"),
      regression, pretrained, fineTuned,
      element("p", "Both models use the same relationship and identity rules on the final NER test. Entity scoring matches exact spans and types. Relationship scoring matches both mention offsets, type and status.", "muted"),
      previous, updated, diagnostic, diagnosis, templates);

  } catch (error) {
    if (token === requestNumber) byId("status").textContent = error.message;
  }
}
function scoreTable(title, result) {
  const scores = [["All entity types", result.ner], ["People", result.people], ["Relationship extraction", result.relationships]];
  if (result.identities) scores.push(["Automatic identity pairs", result.identities]);
  if (result.identity_coverage) scores.push(["Identity pairs found or suggested", result.identity_coverage]);
  return metricsTable(title, scores);
}

function metricsTable(title, scores) {
  const section = element("section", undefined, "score-section");
  const table = element("table");
  const header = table.createTHead().insertRow();
  for (const heading of ["Task", "Precision", "Recall", "F1", "TP", "FP", "FN"]) header.append(element("th", heading));
  for (const [label, row] of scores) {
    const tr = table.insertRow();
    const values = [label, ...[row.precision, row.recall, row.f1].map(value => (100 * value).toFixed(1) + "%"), row.tp, row.fp, row.fn];
    for (const value of values) tr.insertCell().textContent = value;
  }
  section.append(element("h2", title), table);
  return section;
}

function exportReview() {
  const reviewedTargets = new Set(data.decisions.map(item => item.target));
  const record = { dataset: view, decisions: data.decisions, edges: data.edges.filter(edge => reviewedTargets.has(edge.id)),
    identityProposals: data.review.filter(item => reviewedTargets.has(item.id)) };
  downloadJSON(record, "casegraph-" + view + "-review.json");
}

function downloadJSON(record, filename) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(record)], { type: "application/json" }));
  const link = element("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function decide(target, decision, note) {
  if (reviewing) return;
  reviewing = true;
  const caseView = view, original = data;
  byId("status").textContent = "Saving review…";
  inspect();
  try {
    const result = await fetchJSON("/api/review", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset: caseView, reports: caseView === "custom" ? original.reports : undefined,
        decisions: [...original.decisions, { target, decision, at: new Date().toISOString(), note }] })
    });
    if (cases.get(caseView) !== original) return;
    cases.set(caseView, result);
    if (view !== caseView) return;
    data = result;
    nodes = new Map(result.nodes.map(node => [node.id, node]));
    if (selected?.type === "edge") selected.value = result.edges.find(edge => edge.id === selected.value.id);
    if (selected?.type === "node") selected = null;
    stats([["Entities", result.nodes.length], ["Evidence rows", result.edges.length], ["Communities", result.communities]]);
    byId("status").textContent = "Review decision recorded.";
  } catch (error) {
    if (view === caseView) byId("status").textContent = error.message;
  } finally {
    reviewing = false;
    if (view !== "evaluation") { inspect(); draw(); }
  }
}
function reviewActions(target, current, noun) {
  const actions = element("div", undefined, "review-actions");
  const note = element("input");
  note.placeholder = "Optional review note";
  note.setAttribute("aria-label", note.placeholder);
  note.maxLength = 300;
  actions.append(note);
  const candidateActions = [["accepted", "Accept " + noun], ["rejected", "Reject " + noun], ["cleared", "Clear decision"]];
  for (const [decision, label] of candidateActions) {
    if (decision === current) continue;
    const action = element("button", label);
    action.disabled = reviewing;
    action.onclick = () => decide(target, decision, note.value);
    actions.append(action);
  }
  return actions;
}
function decisionLabel(decision) {
  return decision === "accepted" ? "Accepted" : decision === "rejected" ? "Rejected" : "Awaiting review";
}

function matches(node) {
  const term = byId("search").value.trim().toLowerCase();
  return [node.id, ...node.names].some(value => value.toLowerCase().includes(term));
}
function visibleEdges() {
  const kind = byId("filter").value;
  return data.edges.filter(edge => (!kind || edge.type === kind)
    && (matches(nodes.get(edge.source)) || matches(nodes.get(edge.target))));
}
function related(edge, id) {
  return edge.source === id || edge.target === id;
}
function select(type, value) {
  selected = { type, value };
  inspect();
  draw();
}
function edgeButton(edge) {
  return button(nodes.get(edge.source).label + " · " + nodes.get(edge.target).label,
    () => select("edge", edge), edge.type + " · " + edge.status + (edge.decision !== "cleared" ? " · " + decisionLabel(edge.decision) : ""));
}
function openPanel(next) {
  panel = next;
  selected = null;
  inspect();
  draw();
}

async function revealLeadAnswer(control) {
  control.disabled = true;
  try {
    revealedLeadAnswer = await fetchJSON("/api/lead/answer");
    if (view === "lead" && panel === "leads" && !selected) inspect();
  } catch (error) {
    if (view === "lead") byId("status").textContent = error.message;
    control.disabled = false;
  }
}

function leadEvidence(card, heading, edgeIds) {
  if (!edgeIds.length) return;
  card.append(element("h4", heading));
  for (const id of edgeIds) {
    const edge = data.edges.find(item => item.id === id);
    const report = data.reports.find(item => item.id === edge.report);
    card.append(button(report.name, () => select("edge", edge),
      edge.origin + " · " + edge.status + (edge.time ? " · " + edge.time : "")));
  }
}

function inspectLeads(box) {
  const incident = data.case;
  const brief = element("details", undefined, "lead-brief");
  brief.append(element("summary", "Read incident report"), element("pre", data.reports[0].text));
  box.append(element("h3", incident.title),
    element("p", incident.question, "lead-question"),
    element("p", incident.date + " · " + incident.window.start + "–" + incident.window.end, "caption"), brief);
  box.append(element("p", data.lead.strongest ? "Strongest lead to follow up" : data.lead.reason, "lead-result"));
  const coverage = element("details");
  const parsed = data.passages.filter(row => row.outcome === "parsed").length;
  coverage.append(element("summary", "Source coverage · " + parsed + " of " + data.passages.length + " passages parsed"));
  for (const row of data.passages) {
    coverage.append(element("p", row.report + " · line " + row.line + " · " + row.outcome, "caption"),
      element("blockquote", row.text));
  }
  box.append(coverage);
  for (const lead of data.lead.cards) {
    const strongest = lead.id === data.lead.strongest;
    const card = element("article", undefined, strongest ? "review-card lead-highlight" : "review-card");
    card.append(element("h3", lead.name),
      element("p", lead.count + (lead.count === 1 ? " independent custody record" : " independent custody records"), "caption"));
    if (strongest) card.append(element("p", data.lead.reason, "caption"));
    if (lead.names.length > 1) card.append(element("p", "Names in reviewed records · " + lead.names.join(", "), "caption"));
    if (lead.latest) card.append(element("p", "Latest direct handling record · " + lead.latest, "caption"));
    if (lead.pending_matches.length) {
      card.append(button("Review identity match", () => openPanel("review"),
        "An initial and surname match needs confirmation."));
    }
    leadEvidence(card, "Independent support", lead.support);
    leadEvidence(card, "Other custody evidence", lead.other);
    leadEvidence(card, "Conflicting record", lead.conflicts);
    box.append(card);
  }
  if (!revealedLeadAnswer) {
    const reveal = element("button", "Reveal fictional answer", "item");
    reveal.onclick = () => revealLeadAnswer(reveal);
    box.append(reveal);
  } else {
    const answer = element("article", undefined, "review-card lead-answer");
    answer.append(element("h3", "Fictional answer"), element("strong", revealedLeadAnswer.person),
      element("p", revealedLeadAnswer.explanation));
    box.append(answer);
  }
}

function inspectTimeline(box) {
  box.append(element("h3", data.case.date + " · " + data.case.item));
  const entries = [...data.edges].sort((a, b) =>
    (a.time || a.start).localeCompare(b.time || b.start) || a.id.localeCompare(b.id));
  const conflicts = new Set(data.lead.cards.flatMap(card => card.conflicts));
  for (const edge of entries) {
    const time = edge.time || edge.start + "–" + edge.end;
    const title = time + " · " + nodes.get(edge.source).label + " · " + edge.type;
    const context = [edge.role, edge.location, edge.origin, edge.status];
    if (conflicts.has(edge.id)) context.push("Conflicting evidence");
    if (edge.decision === "rejected") context.push("Rejected in review");
    box.append(button(title, () => select("edge", edge), context.join(" · ")));
  }
}

function inspectPath(box) {
  box.append(element("h3", "Trace a connection"),
    element("p", "Paths use directly reported, unrejected links in either direction. Open each row to inspect the original endpoints.", "caption"));
  const choices = [...nodes.values()].sort((a, b) => a.label.localeCompare(b.label));
  for (const [i, label] of ["From", "To"].entries()) {
    const selectNode = element("select");
    selectNode.id = "path-end-" + i;
    const caption = element("label", label);
    caption.htmlFor = selectNode.id;
    selectNode.append(new Option("Choose entity", ""));
    for (const node of choices) selectNode.append(new Option(node.label + " · " + node.id, node.id));
    selectNode.value = pathEnds[i] || "";
    selectNode.onchange = () => { pathEnds[i] = selectNode.value; inspect(); };
    box.append(caption, selectNode);
  }
  const [start, end] = pathEnds;
  if (!nodes.has(start) || !nodes.has(end)) return;
  if (start === end) { box.append(element("p", "Choose two different entities.")); return; }
  const adjacency = new Map(choices.map(node => [node.id, new Map()]));
  for (const edge of data.edges) {
    if (edge.status !== "Directly reported" || edge.decision === "rejected" || edge.source === edge.target) continue;
    for (const [a, b] of [[edge.source, edge.target], [edge.target, edge.source]]) {
      const neighbors = adjacency.get(a);
      if (!neighbors.has(b)) neighbors.set(b, []);
      neighbors.get(b).push(edge);
    }
  }
  const previous = new Map([[start, null]]);
  const queue = [start];
  for (let i = 0; i < queue.length && !previous.has(end); i++) {
    for (const neighbor of adjacency.get(queue[i]).keys()) {
      if (previous.has(neighbor)) continue;
      previous.set(neighbor, queue[i]);
      queue.push(neighbor);
    }
  }
  if (!previous.has(end)) { box.append(element("p", "No qualifying path in this case.")); return; }
  const hops = [];
  for (let b = end; b !== start; b = previous.get(b)) hops.unshift([previous.get(b), b]);
  for (const [a, b] of hops) {
    const edges = adjacency.get(a).get(b);
    box.append(element("h4", nodes.get(a).label + " ↔ " + nodes.get(b).label + " · " + edges.length + " source rows"));
    for (const edge of edges) box.append(button(edge.report + " · " + edge.type, () => select("edge", edge), edge.sentence));
  }
}

function inspect() {
  const box = byId("details");
  box.replaceChildren();
  byId("clear").hidden = !selected;
  toggleActive("[data-panel]", "panel", panel);
  if (!data) return;
  if (selected?.type === "edge") {
    const edge = selected.value;
    const badge = element("p", edge.status, "badge " + (edge.status === "Denied" ? "deny" : edge.status === "Unverified claim" ? "warn" : ""));
    const report = data.reports.find(item => item.id === edge.report);
    box.append(element("h3", edge.type), badge,
      element("p", nodes.get(edge.source).label + " · " + nodes.get(edge.target).label),
      element("p", edge.report + (report?.name ? " · " + report.name : ""), "caption"), element("blockquote", edge.sentence));
    if (edge.origin) {
      box.append(element("p", edge.origin + (edge.time ? " · " + edge.time : "") + " · " + edge.location, "caption"));
    }
    if (report) {
      const details = element("details");
      details.append(element("summary", "Read original report"), element("pre", report.text));
      box.append(details);
    }
    box.append(element("p", "Review · " + decisionLabel(edge.decision), "caption"), reviewActions(edge.id, edge.decision, "link"));
    return;
  }
  if (selected?.type === "node") {
    const node = selected.value;
    box.append(element("h3", node.label), element("p", node.type + " · " + node.id, "caption"),
      element("p", "Degree " + node.degree + " · Centrality " + node.centrality
        + (node.community ? " · Community " + node.community : "")));
    if (view === "montagna") box.append(element("p", "Total source weight · " + node.activity_weight,
      "caption"), element("p", "Sums incident meeting and call row weights in both directions.", "caption"));
    if (node.names.length > 1) box.append(element("p", "Names · " + node.names.join(", "), "caption"));
    if (node.reports?.length) box.append(element("p", "Reports · " + node.reports.join(", "), "caption"));
    for (const alias of node.aliases || []) {
      const evidence = element("details");
      evidence.append(element("summary", "Alias evidence · " + alias.report), element("blockquote", alias.sentence));
      box.append(evidence);
    }
    for (const [label, value] of Object.entries(node.metadata || {})) box.append(element("p", label + " · " + value, "caption"));
    const claims = visibleEdges().filter(edge => related(edge, node.id));
    box.append(...claims.map(edgeButton));
    if (!claims.length) box.append(element("p", "No matching relationship evidence.", "muted"));
    return;
  }
  if (panel === "leads") {
    inspectLeads(box);
  } else if (panel === "timeline") {
    inspectTimeline(box);
  } else if (panel === "paths") {
    inspectPath(box);
  } else if (panel === "evidence") {
    const edges = visibleEdges();
    box.append(...edges.map(edgeButton));
    if (!edges.length) box.append(element("p", "No matching relationship evidence.", "muted"));
  } else if (panel === "review") {
    if (data.decisions.length) {
      const history = element("details");
      history.append(element("summary", "Review actions · " + data.decisions.length));
      for (const action of data.decisions) {
        history.append(element("p", [action.at, action.target, action.decision, action.note].filter(Boolean).join(" · ")));
      }
      box.append(history);
      box.append(button("Download review history", exportReview,
        data.decisions.length + " recorded actions · available during this browser session"));
    }
    for (const item of data.review) {
      const card = element("article", undefined, "review-card");
      card.append(element("h3", item.id ? "Possible identity match" : "Identity notice"),
        element("p", item.reason, "caption"));
      if (item.report) card.append(element("p", item.report, "caption"));
      if (item.sentence) card.append(element("blockquote", item.sentence));
      if (item.records) {
        for (const record of item.records) {
          card.append(element("p", record.label + " · " + record.id, "caption"));
          for (const item of record.evidence) card.append(element("blockquote", item.report + " · " + item.sentence));
        }
        if (item.shared_contacts?.length) {
          const context = element("details");
          context.append(element("summary", "Reported contact names in common"),
            element("p", item.shared_contacts.join(", "), "caption"));
          for (const claim of item.supporting_claims) {
            context.append(element("blockquote", claim.report + " · " + claim.sentence));
          }
          card.append(context);
        }
        card.append(element("p", decisionLabel(item.decision), "badge"));
        if (item.resolved[0] === item.resolved[1] && item.decision === "cleared") {
          card.append(element("p", "Linked through another reviewed merge.", "caption"));
        } else {
          card.append(reviewActions(item.id, item.decision, "merge"));
        }
      }
      box.append(card);
    }
    if (!data.review.length) box.append(element("p", "No identity conflicts were flagged.", "muted"));
  } else {
    const items = data.nodes.filter(matches).sort((a, b) => b.degree - a.degree || a.label.localeCompare(b.label));
    box.append(...items.map(node => button(node.label, () => select("node", node), node.type + " · Degree " + node.degree)));
    if (!items.length) box.append(element("p", "No matching entities.", "muted"));
  }
}
function point(node) {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  return [w / 2 + node.x * w * .43 * zoom + pan[0], h / 2 + node.y * h * .43 * zoom + pan[1]];
}
function edgePoints(edge) {
  return [point(nodes.get(edge.source)), point(nodes.get(edge.target))];
}
function draw() {
  if (!data || canvas.offsetParent === null) return;
  const w = canvas.clientWidth, h = canvas.clientHeight, scale = window.devicePixelRatio || 1;
  canvas.width = w * scale;
  canvas.height = h * scale;
  ctx.scale(scale, scale);
  ctx.fillStyle = "#203247";
  for (let x = 12; x < w; x += 24) for (let y = 12; y < h; y += 24) ctx.fillRect(x, y, 1.4, 1.4);
  for (const edge of visibleEdges()) {
    if (edge.decision === "rejected") continue;
    const [[x, y], [tx, ty]] = edgePoints(edge);
    const focused = selected?.type === "edge" ? selected.value.id === edge.id :
      selected?.type === "node" && related(edge, selected.value.id);
    ctx.strokeStyle = edge.status === "Denied" ? "#f495a4" : edge.status === "Unverified claim" ? "#f4cd86" : "#819eb9";
    ctx.globalAlpha = focused ? 1 : selected ? .22 : .57;
    ctx.lineWidth = focused ? 2.7 : 1;
    ctx.setLineDash(edge.status === "Denied" ? [1, 4] : edge.status === "Unverified claim" ? [5, 4] : []);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(tx, ty);
    ctx.stroke();
  }
  for (const node of data.nodes) {
    const [x, y] = point(node);
    const focused = selected?.type === "node" && selected.value.id === node.id;
    ctx.globalAlpha = matches(node) ? 1 : .18;
    ctx.fillStyle = colors[node.type];
    ctx.beginPath();
    const size = view === "montagna" && byId("weighted").checked
      ? Math.min(Math.sqrt(node.activity_weight), 18) : Math.min(node.degree, 10) / 3;
    ctx.arc(x, y, (focused ? 7 : 4) + size, 0, Math.PI * 2);
    ctx.fill();
    if (focused || zoom > 1.45 || (data.nodes.length <= 45) || (byId("search").value && matches(node))) {
      ctx.font = "12px system-ui";
      ctx.fillStyle = "#edf3fa";
      ctx.fillText(node.label, x + 9, y - 5);
    }
  }
  ctx.globalAlpha = 1;
}
function reset() {
  zoom = 1;
  pan = [0, 0];
  draw();
}
function edgeDistance(px, py, [[x, y], [tx, ty]]) {
  const dx = tx - x, dy = ty - y;
  const t = Math.max(0, Math.min(1, ((px - x) * dx + (py - y) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(px - x - t * dx, py - y - t * dy);
}
canvas.onpointerdown = event => {
  canvas.setPointerCapture(event.pointerId);
  drag = { x: event.clientX, y: event.clientY, pan: [...pan] };
};
canvas.onpointermove = event => {
  if (!drag) return;
  pan = [drag.pan[0] + event.clientX - drag.x, drag.pan[1] + event.clientY - drag.y];
  draw();
};
canvas.onpointercancel = () => { drag = null; };
canvas.onpointerup = event => {
  if (data && drag && Math.hypot(event.clientX - drag.x, event.clientY - drag.y) < 5) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left, y = event.clientY - rect.top;
    const hit = data.nodes.find(node => {
      const [nx, ny] = point(node);
      return Math.hypot(nx - x, ny - y) < 9;
    });
    if (hit) select("node", hit);
    else {
      const edge = visibleEdges().find(item => item.decision !== "rejected" && edgeDistance(x, y, edgePoints(item)) < 5);
      if (edge) select("edge", edge);
    }
  }
  drag = null;
};
canvas.addEventListener("wheel", event => {
  event.preventDefault();
  zoom = Math.max(.5, Math.min(6, zoom * Math.exp(-event.deltaY * .0015)));
  draw();
}, { passive: false });
new ResizeObserver(draw).observe(canvas);
document.querySelectorAll("[data-view]").forEach(node => { node.onclick = () => load(node.dataset.view); });
document.querySelectorAll("[data-panel]").forEach(node => {
  node.onclick = () => openPanel(node.dataset.panel);
});
byId("clear").onclick = () => { selected = null; inspect(); draw(); };
byId("reset").onclick = reset;
byId("weighted").onchange = draw;
for (const id of ["search", "filter"]) byId(id).oninput = () => { selected = null; inspect(); draw(); };
byId("open-input").onclick = () => byId("input-dialog").showModal();
byId("close-input").onclick = () => byId("input-dialog").close();
byId("report-form").onsubmit = async event => {
  event.preventDefault();
  const submit = event.submitter;
  submit.disabled = true;
  byId("input-status").textContent = "Analyzing reports…";
  try {
    const files = Array.from(byId("files").files);
    if (files.length > 50 || files.some(file => file.size > 80_000)) throw new Error("Choose up to 50 short UTF-8 text files.");
    const batch = await Promise.all(files.map(async file => ({
      name: file.name, text: new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer())
    })));
    const pasted = byId("report-text").value.trim();
    if (pasted) batch.push({ name: "Pasted report", text: pasted });
    const result = await fetchJSON("/api/analyze", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reports: batch })
    });
    ++requestNumber;
    showGraph("custom", result);
    byId("input-dialog").close();
    byId("input-status").textContent = "";
  } catch (error) {
    byId("input-status").textContent = error.message;
  } finally {
    submit.disabled = false;
  }
};
byId("save-case").onclick = () => {
  if (!data || reviewing || view === "evaluation") return;
  downloadJSON({ format: "casegraph-1", version: data.source_version, dataset: view,
    reports: data.reports, decisions: data.decisions }, "casegraph-" + view + ".json");
};
byId("open-case").onclick = () => byId("case-file").click();
byId("case-file").onchange = async event => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  const token = ++requestNumber;
  try {
    if (file.size > 1500000) throw new Error("Case file exceeds the size limit.");
    const opened = await fetchJSON("/api/cases/open", { method: "POST", headers: { "Content-Type": "application/json" },
      body: await file.text() });
    if (token !== requestNumber) return;
    revealedLeadAnswer = null;
    showGraph(opened.dataset, opened.graph);
    byId("status").textContent = "Saved case restored.";
  } catch (error) {
    if (token === requestNumber) byId("status").textContent = error.message;
  }
};
load("demo");
