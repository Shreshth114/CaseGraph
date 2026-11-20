const caseChats = new WeakMap();

function chatSuggestions(graph, dataset) {
  if (dataset === "lead") {
    return ["Who last handled KIT-17?", "Who should I follow up with?", "Are Dev Rao and D. Rao the same person?"];
  }
  const edge = graph.edges.find(row => row.decision !== "rejected");
  const endpoints = edge && [edge.source, edge.target].map(id => graph.nodes.find(node => node.id === id));
  const prompts = endpoints ? ["What connects " + endpoints.map(node => node.label).join(" and ") + "?"] : [];
  if (graph.edges.some(row => row.status === "Unverified claim" && row.decision !== "rejected")) {
    prompts.push("Which claims are unverified?");
  }
  return prompts;
}

function caseChat(graph) {
  if (caseChats.has(graph)) return caseChats.get(graph);
  const root = element("section", undefined, "case-chat");
  const messages = element("div", undefined, "chat-messages");
  messages.setAttribute("role", "log");
  messages.setAttribute("aria-label", "Case chat messages");
  messages.tabIndex = 0;
  const intro = element("div", undefined, "chat-intro");
  intro.append(element("h3", "Ask this case"),
    element("p", "Ask about the people, connections, or evidence in the open case.", "muted"));
  const prompts = element("div", undefined, "chat-prompts");
  const dataset = view;
  for (const prompt of chatSuggestions(graph, dataset)) {
    const suggestion = element("button", prompt);
    suggestion.type = "button";
    suggestion.onclick = () => submit(prompt);
    prompts.append(suggestion);
  }
  intro.append(prompts);
  messages.append(intro);

  const form = element("form", undefined, "chat-composer");
  const input = element("input");
  input.type = "text";
  input.placeholder = "Ask a question…";
  input.autocomplete = "off";
  input.maxLength = 500;
  input.setAttribute("aria-label", "Question about the open case");
  const send = element("button", "Send", "primary");
  send.type = "submit";
  const status = element("p", "", "caption chat-status");
  status.setAttribute("role", "status");
  form.append(status, input, send);
  form.onsubmit = event => {
    event.preventDefault();
    submit(input.value);
  };
  root.append(messages, form);
  const state = { root, edge: null };
  caseChats.set(graph, state);
  return state;

  async function submit(question) {
    question = question.trim();
    if (!question || send.disabled) return;
    send.disabled = true;
    input.value = "";
    input.focus();
    intro.hidden = true;
    messages.append(element("p", question, "chat-user"));
    messages.scrollTop = messages.scrollHeight;
    status.textContent = "Looking up case evidence…";
    try {
      const reply = await fetchJSON("/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset, version: graph.source_version, decisions: graph.decisions,
          reports: dataset === "custom" ? graph.reports : undefined, question, edge: state.edge })
      });
      if (reply.citations.length === 1 && reply.citations[0].edge) state.edge = reply.citations[0].edge;
      const response = chatReply(graph, reply);
      messages.append(response);
      const top = response.getBoundingClientRect().top - messages.getBoundingClientRect().top;
      if (top > 0) messages.scrollTop += top;
    } catch (error) {
      messages.append(element("p", "Could not answer. " + error.message, "chat-response"));
      messages.scrollTop = messages.scrollHeight;
    } finally {
      status.textContent = "";
      send.disabled = false;
    }
  }
}

function chatReply(graph, reply) {
  const response = element("article", undefined, "chat-response");
  response.append(element("p", reply.message));
  for (const citation of reply.citations) {
    const edge = graph.edges.find(item => item.id === citation.edge);
    const report = graph.reports.find(item => item.id === citation.report);
    const label = report?.name || citation.report;
    const source = element("div", undefined, "chat-source");
    source.append(element("blockquote", citation.quote));
    if (edge || report) {
      source.append(button(label,
        () => edge ? select("edge", edge) : select("report", report),
        [citation.report, citation.status].filter(Boolean).join(" · ")));
    }
    response.append(source);
  }
  if (reply.action === "review") response.append(button("Open Review", () => openPanel("review")));
  if (reply.action === "leads") response.append(button("Open Leads", () => openPanel("leads")));
  return response;
}
