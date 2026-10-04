(async () => {
  if (!await shell("")) return;
  const id = new URLSearchParams(location.search).get("id"), c = $("#content");
  if (!id) { c.innerHTML = '<p class="card">No emergency selected. <a href="history.html">View history</a></p>'; return; }
  const AMB = ["SEARCHING", "REQUESTED", "ASSIGNED", "EN_ROUTE", "ARRIVED", "COMPLETED", "UNAVAILABLE"];
  const HOS = ["SEARCHING", "REQUESTED", "PENDING", "ACCEPTED", "REJECTED", "READY", "ARRIVED", "COMPLETED"];
  let facMap = {}, nearby = null;
  const opts = (a, v) => a.map(x => `<option ${x === v ? "selected" : ""}>${x}</option>`).join("");
  async function run(fn, ok) { try { await fn(); if (ok) toast(ok); } catch (e) { toast(e.message, true); } await load(); }

  async function load() {
    loading(c);
    let em, tl, nt, cts;
    try {
      [em, tl, nt, cts] = await Promise.all([api(`/api/emergencies/${id}`), api(`/api/emergencies/${id}/timeline`), api(`/api/emergencies/${id}/notifications`), api("/api/contacts")]);
      if (!Object.keys(facMap).length) (await api("/api/facilities")).forEach(f => facMap[f.id] = f);
    } catch (e) { c.innerHTML = `<p class="card">${esc(e.message)} <a href="history.html">Back to history</a></p>`; return; }
    const hasLoc = em.latitude != null, active = em.status === "ACTIVE", fac = facMap[em.hospital?.facility_id];
    c.innerHTML = `
    <section class="card"><h2>${esc(em.code)} ${pBadge(em.priority)} ${sBadge(em.status)}</h2>
      <p>Patient: <b>${esc(em.patient_name)}</b>${em.patient_age != null ? ", " + em.patient_age : ""} · Blood group: ${esc(em.blood_group || "–")}<br>
      Incident: ${esc(em.incident_type)} · Condition: ${esc(em.condition || "–")}<br>Symptoms: ${esc(em.symptoms || "–")}<br>Notes: ${esc(em.notes || "–")}<br>
      Time: ${fmt(em.created_at)}<br>Location: ${esc(em.location_text || "–")} (${hasLoc ? em.latitude.toFixed(5) + ", " + em.longitude.toFixed(5) : "coordinates not captured"})
      ${hasLoc ? `· <a href="https://www.google.com/maps?q=${em.latitude},${em.longitude}" target="_blank" rel="noopener">Open map</a>` : ""}</p>
      <div class="row noprint"><button id="print">Print / save as PDF</button>
      ${active ? `<button class="danger" id="resolve">Mark resolved</button>` : ""}</div></section>
    <section class="card"><h2>Trusted contacts</h2>${cts.length ? "<ul>" + cts.map(k => `<li>${esc(k.name)} (${esc(k.relationship || "contact")}) ${esc(k.phone || "")} ${esc(k.email || "")} ${k.is_primary ? "★ primary" : ""}</li>`).join("") + "</ul>" : '<p>No contacts yet. <a href="contacts.html">Add a contact</a></p>'}
      <button class="primary noprint" id="notify" ${cts.some(k => k.email) ? "" : "disabled"}>Email trusted contacts</button></section>
    <section class="card"><h2>Ambulance</h2><p>Status: ${sBadge(em.ambulance.status)} ${em.ambulance.provider ? esc(em.ambulance.provider) : ""} ${em.ambulance.eta_minutes != null ? "ETA " + em.ambulance.eta_minutes + " min" : ""}</p>
      <p class="muted">${esc(em.ambulance.notes || "No ambulance provider is connected. Requests are recorded here only; call an ambulance service directly.")}</p>
      <div class="row noprint"><button id="amb">Record ambulance request</button><label class="muted" for="as" style="margin:0">Status</label><select id="as" style="width:auto">${opts(AMB, em.ambulance.status)}</select><button id="asu">Update</button></div></section>
    <section class="card"><h2>Hospital</h2><p>Status: ${sBadge(em.hospital.status)} · Facility: ${fac ? esc(fac.name) + (fac.is_demo ? " (demo data)" : "") : "not selected"}</p>
      <div class="row noprint"><label class="muted" for="hs" style="margin:0">Status</label><select id="hs" style="width:auto">${opts(HOS, em.hospital.status)}</select><button id="hsu">Update</button>
      <button id="near" ${hasLoc ? "" : "disabled"}>Find nearby facilities</button></div>
      ${hasLoc ? "" : '<p class="muted">Add coordinates to search nearby.</p>'}
      <div id="nearby">${nearby ? nearby.map(f => `<div class="card"><b>${esc(f.name)}</b> ${f.is_demo ? '<span class="badge">DEMO</span>' : ""}<br>${f.distance_km} km · ${esc(f.type)} · ${esc(f.address || "")}<br>
        <a class="btn" href="tel:${esc(f.phone)}">Call</a> <a class="btn" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${f.latitude},${f.longitude}">Directions</a>
        <button data-f="${f.id}" class="pick noprint">Select facility</button></div>`).join("") || "<p>No facilities within 25 km.</p>" : ""}</div></section>
    <section class="card"><h2>Notifications</h2>${nt.length ? `<table class="resp"><tbody>${nt.map(n => `<tr><td>${fmt(n.created_at)}</td><td>${esc(n.type)}</td><td>${esc(n.channel)} ${esc(n.recipient || "")}</td><td>${sBadge(n.status)} ${esc(n.error || "")}</td></tr>`).join("")}</tbody></table>` : "<p>None yet.</p>"}</section>
    <section class="card"><h2>Timeline</h2><ul class="tl">${tl.map(e => `<li><b>${fmt(e.created_at)}</b> ${esc(e.event)} <span class="muted">— ${esc(e.actor || "system")}${e.status ? ", " + esc(e.status) : ""}</span></li>`).join("")}</ul></section>`;
    $("#print").onclick = () => print();
    $("#resolve") && ($("#resolve").onclick = () => confirm("Mark this emergency as resolved?") && run(() => api(`/api/emergencies/${id}`, {method: "PATCH", body: {status: "RESOLVED"}}), "Emergency resolved"));
    $("#notify").onclick = () => run(async () => { const r = await api(`/api/emergencies/${id}/notify`, {method: "POST"}); const bad = r.results.filter(x => x.status === "FAILED"); if (bad.length) toast(`${bad.length} email(s) failed: ${bad.map(b => b.contact).join(", ")}`, true); }, "Contacts emailed");
    $("#amb").onclick = () => run(() => api(`/api/emergencies/${id}/ambulance`, {method: "POST"}), "Request recorded (not dispatched)");
    $("#asu").onclick = () => run(() => api(`/api/emergencies/${id}/coordination`, {method: "PATCH", body: {ambulance_status: $("#as").value}}), "Ambulance status updated");
    $("#hsu").onclick = () => run(() => api(`/api/emergencies/${id}/coordination`, {method: "PATCH", body: {hospital_status: $("#hs").value}}), "Hospital status updated");
    $("#near").onclick = async () => { try { nearby = await api(`/api/facilities/nearby?lat=${em.latitude}&lon=${em.longitude}&radius_km=25`); } catch (e) { return toast(e.message, true); } load(); };
    document.querySelectorAll(".pick").forEach(b => b.onclick = () => run(() => api(`/api/emergencies/${id}/hospital?facility_id=${b.dataset.f}`, {method: "POST"}), "Facility selected"));
  }
  load();
})();
