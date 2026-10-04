const API = ((window.MB_CONFIG || {}).API_BASE || "").replace(/\/$/, "");
const T = {
  en: {dashboard: "Dashboard", history: "History", contacts: "Contacts", facilities: "Facilities", logout: "Log out", sos: "SOS",
       disclaimer: "MediBridge is for coordination and information. It does not call emergency services or replace medical advice. In a genuine emergency, call your local emergency number (112 in India)."},
  hi: {dashboard: "डैशबोर्ड", history: "इतिहास", contacts: "संपर्क", facilities: "सुविधाएँ", logout: "लॉग आउट", sos: "SOS",
       disclaimer: "MediBridge समन्वय और जानकारी के लिए है। यह आपातकालीन सेवाओं को कॉल नहीं करता और चिकित्सकीय सलाह का विकल्प नहीं है। वास्तविक आपात स्थिति में अपने स्थानीय आपातकालीन नंबर (भारत में 112) पर कॉल करें।"},
  bn: {dashboard: "ড্যাশবোর্ড", history: "ইতিহাস", contacts: "যোগাযোগ", facilities: "সুবিধা", logout: "লগ আউট", sos: "SOS",
       disclaimer: "MediBridge সমন্বয় ও তথ্যের জন্য। এটি জরুরি পরিষেবাকে কল করে না এবং চিকিৎসা পরামর্শের বিকল্প নয়। প্রকৃত জরুরি অবস্থায় আপনার স্থানীয় জরুরি নম্বরে (ভারতে 112) কল করুন।"}
};
let lang = localStorage.getItem("mb_lang") || "en";
const t = k => (T[lang] && T[lang][k]) || T.en[k] || k;
const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const fmt = d => d ? new Date(d).toLocaleString() : "–";
const token = () => localStorage.getItem("mb_token");
let currentUser = null;

function logout() { localStorage.removeItem("mb_token"); location.href = "login.html"; }

function errMsg(d, status) {
  const det = d && d.detail;
  if (typeof det === "string") return det;
  if (Array.isArray(det)) return det.map(e => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ");
  if (det && det.message) return det.message + (det.results ? " — " + det.results.map(r => `${r.contact}: ${r.error}`).join("; ") : "");
  return `Request failed (${status})`;
}

async function api(path, {method = "GET", body} = {}) {
  let r;
  try {
    r = await fetch(API + path, {method, body: body ? JSON.stringify(body) : undefined,
      headers: {"Content-Type": "application/json", ...(token() ? {Authorization: "Bearer " + token()} : {})}});
  } catch { throw new Error("Cannot reach the MediBridge server. Check your connection and API_BASE in config.js."); }
  if (r.status === 401 && token()) { logout(); }
  if (r.status === 204) return null;
  const data = await r.json().catch(() => null);
  if (!r.ok) { const e = new Error(errMsg(data, r.status)); e.status = r.status; throw e; }
  return data;
}

function toast(msg, err = false) {
  let box = $(".toasts");
  if (!box) { box = document.createElement("div"); box.className = "toasts"; box.setAttribute("role", "status"); box.setAttribute("aria-live", "polite"); document.body.append(box); }
  const el = document.createElement("div"); el.className = "toast" + (err ? " err" : ""); el.textContent = msg;
  box.append(el); setTimeout(() => el.remove(), err ? 8000 : 4000);
}

const PRI = {CRITICAL: "▲▲▲ CRITICAL", HIGH: "▲▲ HIGH", MEDIUM: "▲ MEDIUM", LOW: "▽ LOW"};
const pBadge = p => `<span class="badge p-${esc(p)}">${esc(PRI[p] || p)}</span>`;
const sBadge = s => `<span class="badge s-${esc(s)}">${esc(s)}</span>`;
const loading = el => { el.innerHTML = '<p class="muted" aria-busy="true">Loading…</p>'; };

function applyTheme(th) { document.documentElement.dataset.theme = th; localStorage.setItem("mb_theme", th); }
applyTheme(localStorage.getItem("mb_theme") || "light");

async function shell(page) {
  if (!token()) { location.href = "login.html"; return false; }
  try { currentUser = await api("/api/auth/me"); } catch (e) { toast(e.message, true); return false; }
  const items = [["dashboard", "dashboard.html"], ["history", "history.html"], ["contacts", "contacts.html"], ["facilities", "facilities.html"]];
  document.body.insertAdjacentHTML("afterbegin", `
    <header><a class="brand" href="dashboard.html">MediBridge</a>
      <label class="muted" for="lang" style="margin:0">Language</label>
      <select id="lang" style="width:auto">${["en", "hi", "bn"].map(l => `<option value="${l}" ${l === lang ? "selected" : ""}>${{en: "English", hi: "हिन्दी", bn: "বাংলা"}[l]}</option>`).join("")}</select>
      <button id="theme" type="button" aria-label="Toggle light or dark theme">Theme</button>
      <span>${esc(currentUser.full_name)}</span><button id="out" type="button">${t("logout")}</button></header>
    <nav aria-label="Main">${items.map(([k, h]) => `<a href="${h}" ${k === page ? 'aria-current="page"' : ""}>${t(k)}</a>`).join("")}
      <a class="sos-link" href="dashboard.html#sos">${t("sos")}</a></nav>`);
  $("#out").onclick = logout;
  $("#theme").onclick = () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  $("#lang").onchange = e => { localStorage.setItem("mb_lang", e.target.value); location.reload(); };
  const m = $("main"); if (m) m.insertAdjacentHTML("beforeend", `<p class="notice">${t("disclaimer")}</p>`);
  return true;
}

function getPosition() {
  return new Promise((res, rej) => {
    if (!navigator.geolocation) return rej(new Error("This browser does not support location."));
    navigator.geolocation.getCurrentPosition(p => res(p.coords), e => rej(new Error(
      e.code === 1 ? "Location permission was denied." : e.code === 3 ? "Location timed out." : "Location is unavailable.")), {timeout: 8000, enableHighAccuracy: true});
  });
}
