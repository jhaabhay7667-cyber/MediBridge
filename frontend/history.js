(async () => {
  if (!await shell("history")) return;
  const c = $("#content");
  c.innerHTML = `<form class="card" id="ff"><div class="grid">
   <div><label for="q">Emergency ID</label><input id="q" placeholder="MB-2026-001"></div>
   <div><label for="st">Status</label><select id="st"><option value="">Any</option><option>ACTIVE</option><option>RESOLVED</option><option>CANCELLED</option></select></div>
   <div><label for="pr">Priority</label><select id="pr"><option value="">Any</option><option>CRITICAL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select></div>
   <div><label for="it">Incident</label><select id="it"><option value="">Any</option>${["Accident", "Medical Emergency", "Fire", "Injury", "Unconscious Person", "Cardiac Emergency", "Breathing Problem", "Other"].map(x => `<option>${x}</option>`).join("")}</select></div>
   <div><label for="df">From date</label><input id="df" type="date"></div></div>
   <button class="primary" style="margin-top:.8rem" type="submit">Apply filters</button></form><div id="res"></div>`;
  async function load() {
    loading($("#res"));
    const q = new URLSearchParams(); [["code", "q"], ["status", "st"], ["priority", "pr"], ["incident_type", "it"]].forEach(([k, i]) => $("#" + i).value && q.set(k, $("#" + i).value));
    try {
      let r = await api("/api/emergencies?" + q);
      if ($("#df").value) r = r.filter(e => new Date(e.created_at) >= new Date($("#df").value));
      $("#res").innerHTML = r.length ? `<table class="resp"><thead><tr><th>ID</th><th>Date</th><th>Incident</th><th>Condition</th><th>Priority</th><th>Status</th></tr></thead><tbody>${r.map(e =>
        `<tr><td><a href="emergency.html?id=${e.id}">${esc(e.code)}</a></td><td>${fmt(e.created_at)}</td><td>${esc(e.incident_type)}</td><td>${esc(e.condition || "–")}</td><td>${pBadge(e.priority)}</td><td>${sBadge(e.status)}</td></tr>`).join("")}</tbody></table>`
        : '<p class="card">No emergencies match these filters.</p>';
    } catch (er) { $("#res").innerHTML = ""; toast(er.message, true); }
  }
  $("#ff").onsubmit = e => { e.preventDefault(); load(); };
  load();
})();
