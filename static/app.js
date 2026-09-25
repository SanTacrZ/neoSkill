const state = {
  data: null,
  sort: "recent",
  loading: false,
  answerDrafts: new Map(),
  toastTimer: null,
};

const elements = {
  questionForm: document.querySelector("#questionForm"),
  questionText: document.querySelector("#questionText"),
  characterCount: document.querySelector("#characterCount"),
  questionsList: document.querySelector("#questionsList"),
  feedCount: document.querySelector("#feedCount"),
  questionCount: document.querySelector("#questionCount"),
  responseCount: document.querySelector("#responseCount"),
  aiCount: document.querySelector("#aiCount"),
  keywordCount: document.querySelector("#keywordCount"),
  keywordCloud: document.querySelector("#keywordCloud"),
  summariesList: document.querySelector("#summariesList"),
  contextContent: document.querySelector("#contextContent"),
  connectionStatus: document.querySelector("#connectionStatus"),
  resetButton: document.querySelector("#resetButton"),
  toast: document.querySelector("#toast"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function initials(value) {
  const parts = String(value).trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

function formatTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "ahora";
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return "hace un momento";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `hace ${hours} h`;
  return date.toLocaleDateString("es", { day: "numeric", month: "short" });
}

function isEditing() {
  const active = document.activeElement;
  return Boolean(active && active.matches("#questionText, .answer-text, .panelist-select"));
}

function setConnection(label, connected = true) {
  elements.connectionStatus.textContent = label;
  elements.connectionStatus.style.color = connected ? "" : "#b8463c";
}

function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.classList.toggle("error", isError);
  elements.toast.classList.add("visible");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => {
    elements.toast.classList.remove("visible");
  }, 3600);
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw new Error(payload?.detail || "No se pudo completar la acción");
  }
  return payload;
}

function sortedQuestions() {
  const questions = [...(state.data?.questions || [])];
  if (state.sort === "popular") {
    return questions.sort((first, second) => second.votes - first.votes);
  }
  return questions.sort((first, second) => new Date(second.created_at) - new Date(first.created_at));
}

function renderAnswer(answer) {
  const isAi = answer.role === "ai";
  return `
    <div class="answer-bubble ${isAi ? "ai-answer" : ""}">
      <div class="answer-meta">
        <span class="answer-role">${isAi ? "Respuesta IA" : "Panelista"}</span>
        <span class="answer-author">${escapeHtml(answer.author)}</span>
        ${isAi ? '<span class="ai-label">simulada</span>' : ""}
        <span class="answer-time">${formatTime(answer.created_at)}</span>
      </div>
      <p class="answer-text">${escapeHtml(answer.text)}</p>
    </div>
  `;
}

function renderQuestion(question) {
  const draft = state.answerDrafts.get(question.id) || {};
  const selectedPanelist = draft.panelist || state.data?.panelists?.[0]?.name || "Panelista";
  const keywords = (question.keywords || []).slice(0, 3);
  const answers = question.answers || [];
  const hasPanelistAnswer = question.has_panelist_answer;
  const hasAiAnswer = question.has_ai_answer;
  const panelistOptions = (state.data?.panelists || [])
    .map(
      (panelist) =>
        `<option value="${escapeHtml(panelist.name)}" ${panelist.name === selectedPanelist ? "selected" : ""}>${escapeHtml(panelist.name)}</option>`,
    )
    .join("");
  const tags = keywords
    .map((keyword) => `<span class="question-tag">#${escapeHtml(keyword.word)}</span>`)
    .join("");
  const answerList = answers.length
    ? `<div class="answer-list">${answers.map(renderAnswer).join("")}</div>`
    : "";
  return `
    <article class="question-card" data-question-id="${escapeHtml(question.id)}">
      <div class="question-meta">
        <div class="question-author">
          <span class="avatar avatar-coral">${escapeHtml(initials(question.author))}</span>
          <span>${escapeHtml(question.author)}</span>
        </div>
        <span class="question-time">${formatTime(question.created_at)}</span>
      </div>
      <p class="question-text">${escapeHtml(question.text)}</p>
      ${tags ? `<div class="question-tags">${tags}</div>` : ""}
      ${answerList}
      <div class="answer-composer">
        <select class="panelist-select" data-field="panelist" aria-label="Elegir panelista">${panelistOptions}</select>
        <textarea class="answer-text" data-field="answer" maxlength="1200" placeholder="Escribe la respuesta de la mesa...">${escapeHtml(draft.text || "")}</textarea>
        <div class="answer-buttons">
          <button class="secondary-button" data-action="panelist-answer" type="button">Responder</button>
          <button class="ai-button" data-action="ai-answer" type="button" ${hasAiAnswer ? "disabled" : ""}>${hasAiAnswer ? "IA ya respondió" : "Responder con IA"}</button>
        </div>
      </div>
      <div class="question-actions">
        <button class="vote-button" data-action="vote" type="button"><span class="vote-arrow">↑</span> ${question.votes} votos</button>
        <span class="action-note">${hasPanelistAnswer ? "Panelista en la conversación" : "Esperando respuesta de la mesa"}</span>
      </div>
    </article>
  `;
}

function renderQuestions() {
  const questions = sortedQuestions();
  elements.feedCount.textContent = `${questions.length} ${questions.length === 1 ? "pregunta" : "preguntas"} en la conversación`;
  if (questions.length === 0) {
    elements.questionsList.innerHTML = '<div class="empty-state">Sé la primera persona en abrir una conversación. Escribe una pregunta arriba y la mesa podrá responderla.</div>';
    return;
  }
  elements.questionsList.innerHTML = questions.map(renderQuestion).join("");
}

function keywordSize(count, maximum) {
  if (!maximum) return 1;
  const ratio = count / maximum;
  if (ratio >= 0.8) return 4;
  if (ratio >= 0.55) return 3;
  if (ratio >= 0.3) return 2;
  return 1;
}

function renderKeywords(keywords) {
  if (!keywords || keywords.length === 0) {
    elements.keywordCloud.innerHTML = '<span class="context-empty">Las palabras más repetidas aparecerán aquí.</span>';
    return;
  }
  const maximum = keywords[0].count;
  elements.keywordCloud.innerHTML = keywords
    .slice(0, 14)
    .map(
      (keyword) =>
        `<span class="keyword-bubble keyword-size-${keywordSize(keyword.count, maximum)}">${escapeHtml(keyword.word)}<span>${keyword.count}</span></span>`,
    )
    .join("");
}

function renderSummaries(summaries) {
  elements.summariesList.innerHTML = (summaries || [])
    .map(
      (summary, index) => `
        <article class="summary-item ${summary.available ? "" : "pending"}">
          <div class="summary-title"><span class="summary-index">0${index + 1}</span>${escapeHtml(summary.title)}</div>
          <p class="summary-text">${escapeHtml(summary.summary)}</p>
          <div class="summary-source">${escapeHtml(summary.role)} · ${summary.response_count} ${summary.response_count === 1 ? "respuesta" : "respuestas"}</div>
        </article>
      `,
    )
    .join("");
}

function renderContext(context) {
  if (!context) {
    elements.contextContent.innerHTML = '<div class="context-empty">Cuando un panelista responda, la IA podrá abrir una segunda pregunta del mismo contexto.</div>';
    return;
  }
  const followup = context.ai_answer
    ? `<div class="context-arrow"></div><div class="context-node ai-node"><span class="context-node-label">Respuesta IA</span>${escapeHtml(context.ai_answer)}</div>`
    : "";
  elements.contextContent.innerHTML = `
    <div class="context-flow">
      <div class="context-node"><span class="context-node-label">Contexto de ${escapeHtml(context.panelist)}</span>${escapeHtml(context.panelist_answer)}</div>
      ${followup}
    </div>
    <p class="context-note">${context.ai_answer ? "La IA encontró una pregunta relacionada y la respondió desde este mismo hilo." : "La respuesta IA aparecerá aquí cuando se detecte otra pregunta relacionada."}</p>
  `;
}

function renderAnalytics(analytics) {
  const stats = analytics?.stats || {};
  elements.questionCount.textContent = stats.questions ?? 0;
  elements.responseCount.textContent = stats.responses ?? 0;
  elements.aiCount.textContent = stats.ai_responses ?? 0;
  elements.keywordCount.textContent = stats.keywords ?? 0;
  renderKeywords(analytics?.keywords);
  renderSummaries(analytics?.summaries);
  renderContext(analytics?.context);
}

function render() {
  if (!state.data) return;
  renderQuestions();
  renderAnalytics(state.data.analytics);
}

async function refresh(force = false) {
  if (state.loading || (!force && isEditing())) return;
  state.loading = true;
  try {
    state.data = await apiRequest("/api/state");
    render();
    setConnection("En vivo");
  } catch (error) {
    setConnection("Sin conexión", false);
    if (force) showToast(error.message, true);
  } finally {
    state.loading = false;
  }
}

function rememberDraft(questionId, field, value) {
  const draft = state.answerDrafts.get(questionId) || {};
  draft[field] = value;
  state.answerDrafts.set(questionId, draft);
}

function getQuestionElement(target) {
  return target.closest(".question-card");
}

async function handleQuestionAction(event) {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const card = getQuestionElement(button);
  if (!card) return;
  const questionId = card.dataset.questionId;
  const action = button.dataset.action;
  if (action === "vote") {
    button.disabled = true;
    try {
      await apiRequest(`/api/questions/${encodeURIComponent(questionId)}/vote`, { method: "POST" });
      await refresh(true);
    } catch (error) {
      showToast(error.message, true);
      button.disabled = false;
    }
    return;
  }
  const answerText = card.querySelector(".answer-text")?.value.trim() || "";
  const panelist = card.querySelector(".panelist-select")?.value || "";
  if (action === "panelist-answer") {
    if (answerText.length < 3) {
      showToast("Escribe una respuesta antes de publicarla.", true);
      card.querySelector(".answer-text")?.focus();
      return;
    }
    button.disabled = true;
    try {
      const result = await apiRequest(
        `/api/questions/${encodeURIComponent(questionId)}/panelist-answer`,
        { method: "POST", body: JSON.stringify({ panelist, text: answerText }) },
      );
      state.answerDrafts.delete(questionId);
      await refresh(true);
      if (result.ai_followup) {
        showToast("Respuesta publicada. La IA conectó otra pregunta del mismo contexto.");
      } else {
        showToast("Respuesta del panelista publicada.");
      }
    } catch (error) {
      showToast(error.message, true);
      button.disabled = false;
    }
    return;
  }
  if (action === "ai-answer") {
    button.disabled = true;
    try {
      await apiRequest(`/api/questions/${encodeURIComponent(questionId)}/ai-answer`, { method: "POST" });
      state.answerDrafts.delete(questionId);
      await refresh(true);
      showToast("La IA simulada respondió usando el contexto disponible.");
    } catch (error) {
      showToast(error.message, true);
      button.disabled = false;
    }
  }
}

function updateCharacterCount() {
  elements.characterCount.textContent = elements.questionText.value.length;
}

function bindEvents() {
  elements.questionText.addEventListener("input", updateCharacterCount);
  elements.questionForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = elements.questionText.value.trim();
    if (text.length < 3) {
      showToast("Escribe una pregunta de al menos 3 caracteres.", true);
      elements.questionText.focus();
      return;
    }
    const submitButton = elements.questionForm.querySelector("button[type='submit']");
    submitButton.disabled = true;
    try {
      await apiRequest("/api/questions", {
        method: "POST",
        body: JSON.stringify({ text, author: "Asistente anónimo" }),
      });
      elements.questionText.value = "";
      updateCharacterCount();
      await refresh(true);
      showToast("Pregunta publicada. Ahora forma parte de la conversación.");
    } catch (error) {
      showToast(error.message, true);
    } finally {
      submitButton.disabled = false;
    }
  });
  elements.questionsList.addEventListener("click", handleQuestionAction);
  elements.questionsList.addEventListener("input", (event) => {
    const card = event.target.closest(".question-card");
    if (!card || !event.target.matches("[data-field]")) return;
    rememberDraft(card.dataset.questionId, event.target.dataset.field, event.target.value);
  });
  elements.questionsList.addEventListener("change", (event) => {
    const card = event.target.closest(".question-card");
    if (!card || !event.target.matches("[data-field]")) return;
    rememberDraft(card.dataset.questionId, event.target.dataset.field, event.target.value);
  });
  document.querySelectorAll(".sort-button").forEach((button) => {
    button.addEventListener("click", () => {
      state.sort = button.dataset.sort;
      document.querySelectorAll(".sort-button").forEach((item) => item.classList.toggle("active", item === button));
      renderQuestions();
    });
  });
  elements.resetButton.addEventListener("click", async () => {
    if (!window.confirm("¿Reiniciar la sesión y borrar las preguntas de la demo?")) return;
    try {
      state.data = await apiRequest("/api/reset", { method: "POST" });
      state.answerDrafts.clear();
      render();
      showToast("La conversación se reinició.");
    } catch (error) {
      showToast(error.message, true);
    }
  });
}

async function init() {
  bindEvents();
  await refresh(true);
  window.setInterval(() => refresh(), 5000);
}

init();
