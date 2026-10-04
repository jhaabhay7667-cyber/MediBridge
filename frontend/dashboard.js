(async () => {
  if (!await shell("dashboard")) return;
  const c = $("#content"); loading(c);
  let list = [], contacts = [], facs = [];
  try { [list, contacts, facs] = await Promise.all([api("/api/emergencies"), api("/api/contacts"), api("/api/facilities")]); }
  catch (e) { c.innerHTML = ""; return toast(e.message, true); }
  const active = list.filter(e => e.status === "ACTIVE"), resolved = list.filter(e => e.status === "RESOLVED");
  const stat = (n, l) => `<div class="card stat"><b>${n}</b>${l}</div>`;
  const act = active[0];
  c.innerHTML = `
    <div class="grid">${stat(active.length, "Active emergencies")}${stat(resolved.length, "Resolved")}${stat(contacts.length, "Trusted contacts")}${stat(facs.length, "Facilities (demo data)")}</div>
    ${act ? `<section class="card" aria-labelledby="ae"><h2 id="ae">Active emergency</h2>
      <p><b>${esc(act.code)}</b> ${pBadge(act.priority)} ${sBadge(act.status)}</p>
      <p>Patient: ${esc(act.patient_name)}<br>Incident: ${esc(act.incident_type)}<br>Location: ${esc(act.location_text || (act.latitude != null ? act.latitude + ", " + act.longitude : "not captured"))}</p>
      <p>Ambulance: ${esc(act.ambulance?.status)} · Hospital: ${esc(act.hospital?.status)}</p>
      <a class="btn primary" href="emergency.html?id=${act.id}">Open emergency</a></section>` : `<p class="card">No active emergency. Press and hold SOS if you need to start one.</p>`}
    <section class="card sos-wrap" id="sos-sec" aria-labelledby="st"><h2 id="st">Start an emergency</h2>
      <button id="sos" type="button" aria-describedby="sh">SOS<small>hold 3 s</small></button>
      <p id="sh" class="muted">Press and hold for 3 seconds (or hold Space/Enter). This creates a record and lets you alert your trusted contacts. It does not call emergency services.</p></section>
    <dialog id="dlg"><form method="dialog" id="cf"><h2>Confirm emergency</h2>
      <label for="inc">Incident type</label><select id="inc">${["Medical Emergency", "Accident", "Cardiac Emergency", "Breathing Problem", "Unconscious Person", "Injury", "Fire", "Other"].map(i => `<option>${i}</option>`).join("")}</select>
      <label for="pri">Priority</label><select id="pri"><option>CRITICAL</option><option selected>HIGH</option><option>MEDIUM</option><option>LOW</option></select>
      <label for="loc">Location (used if device location is unavailable)</label><input id="loc" placeholder="Area, city">
      <div class="row" style="margin-top:1rem"><button class="primary" id="go" value="go">Confirm emergency</button><button value="cancel">Cancel</button></div></form></dialog>`;
  const btn = $("#sos"), dlg = $("#dlg"); let start = 0, raf = 0;
  const stop = () => { cancelAnimationFrame(raf); start = 0; btn.style.setProperty("--p", 0); };
  const tick = () => { const p = Math.min((performance.now() - start) / 3000, 1); btn.style.setProperty("--p", p);
    if (p >= 1) { stop(); dlg.showModal(); } else raf = requestAnimationFrame(tick); };
  const down = () => { if (!start) { start = performance.now(); tick(); } };
  btn.addEventListener("pointerdown", down);
  ["pointerup", "pointerleave", "pointercancel"].forEach(ev => btn.addEventListener(ev, stop));
  btn.addEventListener("keydown", e => { if ((e.key === " " || e.key === "Enter") && !e.repeat) { e.preventDefault(); down(); } });
  btn.addEventListener("keyup", stop);
  btn.addEventListener("contextmenu", e => e.preventDefault());
  $("#cf").onsubmit = async e => {
    if (e.submitter.value !== "go") return;
    e.preventDefault(); $("#go").disabled = true;
    const body = {incident_type: $("#inc").value, priority: $("#pri").value, location_text: $("#loc").value || null};
    try { const p = await getPosition(); body.latitude = p.latitude; body.longitude = p.longitude; }
    catch (er) { toast(er.message + " Emergency will be created without coordinates.", true); }
    try { const em = await api("/api/emergencies", {method: "POST", body}); location.href = "emergency.html?id=" + em.id; }
    catch (er) { toast(er.message, true); $("#go").disabled = false; }
  };
  if (location.hash === "#sos") btn.focus();
})();
