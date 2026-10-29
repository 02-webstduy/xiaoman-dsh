// 小满 · 第 1 步的前端：流式对话 + 人格弹窗 + 一点状态显示。
// 没有框架、没有构建。改完刷新。

import { mountPet, setMood } from "./pet.js";

const $ = (id) => document.getElementById(id);

const log = $("log");
const form = $("form");
const input = $("input");
const sendBtn = $("send");
const dot = $("dot");
const statusText = $("status");
const note = $("note");
const pet = $("pet");

mountPet(pet);

let streaming = false;
let controller = null;

/* ------------------------------------------------------------------ 基础 */

function nearBottom() {
  return log.scrollHeight - log.scrollTop - log.clientHeight < 96;
}

function scrollToEnd(force) {
  if (force || nearBottom()) {
    log.scrollTop = log.scrollHeight;
  }
}

function addBubble(role, text = "") {
  const row = document.createElement("div");
  row.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);
  log.appendChild(row);
  scrollToEnd(true);
  return bubble;
}

function showSystem(text) {
  addBubble("system", text);
}

function setBusy(busy) {
  streaming = busy;
  input.disabled = busy;
  sendBtn.classList.toggle("stop", busy);
  sendBtn.textContent = busy ? "■" : "↑";
  sendBtn.type = busy ? "button" : "submit";
  sendBtn.setAttribute("aria-label", busy ? "停止" : "发送");
  if (!busy) {
    setMood(pet, "calm");
    input.focus();
  }
}

function setHealth(ok, label, detail) {
  dot.classList.toggle("ok", ok === true);
  dot.classList.toggle("bad", ok === false);
  statusText.textContent = label;
  if (detail) statusText.title = detail;
}

/* ------------------------------------------------------------------ 状态 */

async function loadState() {
  try {
    const res = await fetch("/api/state");
    const s = await res.json();
    $("name").textContent = s.name;
    $("day").textContent = `第 ${s.day} 天`;
    if (s.ok) {
      const ms = s.latency_ms == null ? "" : ` · ${s.latency_ms}ms`;
      setHealth(true, `本地模型在线${ms}`, s.model);
    } else {
      setHealth(false, "模型没连上", s.detail);
    }
  } catch {
    setHealth(false, "服务没响应", "");
  }
}

/* ------------------------------------------------------------------ SSE */

function parseEvent(block) {
  let event = "message";
  const data = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data.push(line.slice(5).trim());
  }
  if (!data.length) return null;
  try {
    return { event, data: JSON.parse(data.join("\n")) };
  } catch {
    return null;
  }
}

async function send(text) {
  streaming = true;
  setBusy(true);
  note?.remove();

  addBubble("user", text);
  const bubble = addBubble("bot");
  bubble.classList.add("thinking");
  setMood(pet, "calm");

  controller = new AbortController();
  let got = false;
  let failed = false;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal: controller.signal,
    });
    if (!res.ok || !res.body) throw new Error(`请求失败（${res.status}）`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let cut;
      while ((cut = buffer.indexOf("\n\n")) !== -1) {
        const evt = parseEvent(buffer.slice(0, cut));
        buffer = buffer.slice(cut + 2);
        if (!evt) continue;

        if (evt.event === "delta") {
          if (!got) {
            bubble.classList.remove("thinking");
            got = true;
          }
          const stick = nearBottom();
          bubble.textContent += evt.data.text ?? "";
          if (stick) log.scrollTop = log.scrollHeight;
        } else if (evt.event === "error") {
          bubble.classList.remove("thinking");
          bubble.textContent = "";
          bubble.parentElement.remove();
          failed = true;
          showSystem(evt.data.message || "模型那边出了点问题，再说一次试试。");
        }
      }
    }
  } catch (err) {
    bubble.classList.remove("thinking");
    if (err.name !== "AbortError") {
      failed = true;
      bubble.parentElement?.remove();
      showSystem(err.message || "连不上本地服务。");
    }
  } finally {
    controller = null;
    setBusy(false);
    if (bubble.isConnected && !bubble.textContent) bubble.parentElement?.remove();
    loadState();
  }
}

/* ------------------------------------------------------------------ 交互 */

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (streaming) return;
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  input.style.height = "auto";
  send(text);
});

sendBtn.addEventListener("click", (event) => {
  if (streaming && controller) {
    event.preventDefault();
    controller.abort();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});

/* ------------------------------------------------------------------ 弹窗 */

const dialog = $("persona-dialog");

$("persona-btn").addEventListener("click", async () => {
  try {
    const res = await fetch("/api/persona");
    $("persona-text").textContent = await res.text();
  } catch {
    $("persona-text").textContent = "读不到人格文件。";
  }
  dialog.showModal();
});

$("persona-close").addEventListener("click", () => dialog.close());

dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

/* ------------------------------------------------------------------ 求助 */

const helpDialog = $("help-dialog");

function addHelpSection(body, title, items) {
  if (!items || !items.length) return;
  const heading = document.createElement("p");
  heading.className = "help-title";
  heading.textContent = title;
  body.appendChild(heading);

  const list = document.createElement("ul");
  list.className = "help-list";
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  }
  body.appendChild(list);
}

$("help-btn").addEventListener("click", async () => {
  const body = $("help-body");
  body.replaceChildren();
  try {
    const res = await fetch("/api/safety");
    const info = await res.json();
    addHelpSection(body, "能马上联系的人", info.contacts);
    addHelpSection(body, "可以打的电话", info.hotlines);
    if (!info.contacts?.length && !info.hotlines?.length) {
      body.textContent = "还没有配置联系人和热线，请直接拨 120。";
    }
  } catch {
    body.textContent = "读取失败，请直接拨 120 或 12356。";
  }
  helpDialog.showModal();
});

$("help-close").addEventListener("click", () => helpDialog.close());

helpDialog.addEventListener("click", (event) => {
  if (event.target === helpDialog) helpDialog.close();
});

/* ------------------------------------------------------------------ 新对话 */
$("reset-btn").addEventListener("click", async () => {
  if (streaming) controller?.abort();
  if (!confirm("清掉这段对话，重新开始？")) return;
  try {
    await fetch("/api/reset", { method: "POST" });
  } catch {
    /* 服务没起来也照样清屏 */
  }
  log.querySelectorAll(".msg").forEach((el) => el.remove());
  showSystem("重新开始了。它只记得从这一句起的事。");
  loadState();
});

/* ------------------------------------------------------------------ 启动 */

loadState();
setInterval(loadState, 60_000);
input.focus();
