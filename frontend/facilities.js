(async () => {
  if (!await shell("facilities")) return;
  const c = $("#content");
  const CATS = [["Hospital", "Hospitals"], ["Blood Bank", "Blood banks"], ["Ambulance Service", "Ambulances"],
                ["Emergency Medical Center", "Emergency centers"], ["Clinic", "Clinics"], ["Pharmacy", "Pharmacies"]];
  let coords = null, current = null;
  c.innerHTML = `<p class="notice">Facilities shown here are demo data and are not verified live availability. Call before travelling.</p>
  <section class="card"><h2>What do you need nearby?</h2>
   <div class="row" role="group" aria-label="Facility type" id="cats">${CATS.map(([v, l]) => `<button type="button" class="cat" data-t="${v}" aria-pressed="false">${l}</button>`).join("")}</div>
   <div class="row" style="margin-top:.8rem"><label for="rad" style="margin:0">Search within</label>
    <select id="rad" style="width:auto"><option value="10">10 km</option><option value="25" selected>25 km</option><option value="50">50 km</option><option value="100">100 km</option><option value="200">200 km</option></select>
    <label style="margin:0"><input id="eo" type="checkbox" style="width:auto;min-height:0"> Emergency care only</label>
    <button type="button" id="loc">Refresh my location</button></div>
   <p id="status" role="status" class="muted"></p>
   <details id="manual"><summary>Enter location manually</summary><form id="mf" class="row" style="margin-top:.5rem">
    <div><label for="lat">Latitude</label><input id="lat" type="number" step="any" min="-90" max="90" required></div>
    <div><label for="lon">Longitude</label><input id="lon" type="number" step="any" min="-180" max="180" required></div>
    <button class="primary" type="submit">Search here</button></form></details></section><div id="res"></div>`;

  const status = m => { $("#status").textContent = m; };
  const valid = (la, lo) => Number.isFinite(la) && Number.isFinite(lo) && Math.abs(la) <= 90 && Math.abs(lo) <= 180;

  async function getCoords(force) {
    if (coords && !force) return coords;
    status("Finding your location…");
    try { const p = await getPosition(); coords = {lat: p.latitude, lon: p.longitude}; $("#lat").value = coords.lat.toFixed(5); $("#lon").value = coords.lon.toFixed(5); return coords; }
    catch (e) {
      const la = parseFloat($("#lat").value), lo = parseFloat($("#lon").value);
      if (valid(la, lo)) { coords = {lat: la, lon: lo}; return coords; }
      $("#manual").open = true; status(e.message + " Enter your coordinates below.");
      throw e;
    }
  }

  const query = (type, radius) => {
    const q = new URLSearchParams({lat: coords.lat, lon: coords.lon, radius_km: radius, type, emergency_only: $("#eo").checked});
    return api("/api/facilities/nearby/search?" + q);
  };

  async function search(type) {
    current = type;
    document.querySelectorAll(".cat").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.t === type)));
    loading($("#res"));
    try { await getCoords(false); } catch { $("#res").innerHTML = ""; return; }
    const label = (CATS.find(x => x[0] === type) || [, type])[1].toLowerCase();
    let radius = +$("#rad").value, list;
    try {
      list = await query(type, radius);
      if (!list.length && radius < 200) { radius = 200; list = await query(type, radius); if (list.length) status(`None within ${$("#rad").value} km. Showing the nearest within 200 km.`); }
      else status(`Showing ${label} within ${radius} km of ${coords.lat.toFixed(3)}, ${coords.lon.toFixed(3)}. Accuracy depends on your device.`);
    } catch (er) { $("#res").innerHTML = ""; return toast(er.message, true); }
    $("#res").innerHTML = list.length ? list.map(f => `<div class="card"><b>${esc(f.name)}</b> ${f.is_demo ? '<span class="badge">DEMO</span>' : ""}<br>${f.distance_km} km away · ${esc(f.type)}<br>${esc(f.address || "")}<br>
      Emergency: ${f.emergency_available ? "yes" : "no"} · Ambulance: ${f.ambulance_available ? "yes" : "no"} · Blood: ${f.blood_available ? "yes" : "no"} <span class="muted">(unverified)</span>
      <div class="row" style="margin-top:.5rem"><a class="btn primary" href="tel:${esc(f.phone)}">Call ${esc(f.phone)}</a>
      <a class="btn" target="_blank" rel="noopener" href="https://www.google.com/maps/dir/?api=1&destination=${f.latitude},${f.longitude}">Directions</a></div></div>`).join("")
      : `<p class="card">No ${esc(label)} found within 200 km in the demo data. Try another category, or call your local emergency number.</p>`;
  }

  document.querySelectorAll(".cat").forEach(b => b.onclick = () => search(b.dataset.t));
  $("#loc").onclick = async () => { coords = null; try { await getCoords(true); status("Location updated."); if (current) search(current); } catch {} };
  $("#rad").onchange = $("#eo").onchange = () => current && search(current);
  $("#mf").onsubmit = e => { e.preventDefault(); const la = parseFloat($("#lat").value), lo = parseFloat($("#lon").value);
    if (!valid(la, lo)) return toast("Enter valid coordinates.", true); coords = {lat: la, lon: lo}; search(current || "Hospital"); };
})();