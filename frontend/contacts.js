(async () => {
  if (!await shell("contacts")) return;
  const c = $("#content");
  c.innerHTML = `<div class="row"><button class="primary" id="add">Add contact</button></div><div id="list"></div>
  <dialog id="dlg"><form method="dialog" id="cf"><h2 id="dt">Contact</h2>
   <label for="n">Name</label><input id="n" required><label for="r">Relationship</label><input id="r">
   <label for="p">Phone</label><input id="p" type="tel"><label for="e">Email (needed for email alerts)</label><input id="e" type="email">
   <label for="pr">Priority (1 = first)</label><input id="pr" type="number" min="1" max="10" value="1">
   <label><input id="pm" type="checkbox" style="width:auto;min-height:0"> Primary contact</label>
   <div class="row" style="margin-top:1rem"><button class="primary" value="save">Save</button><button value="cancel">Cancel</button></div></form></dialog>`;
  let editing = null, data = [];
  async function load() {
    loading($("#list"));
    try { data = await api("/api/contacts"); } catch (e) { $("#list").innerHTML = ""; return toast(e.message, true); }
    $("#list").innerHTML = data.length ? data.map(k => `<div class="card"><b>${esc(k.name)}</b> ${k.is_primary ? '<span class="badge">★ Primary</span>' : ""}<br>${esc(k.relationship || "")}<br>${esc(k.phone || "")} ${esc(k.email || "")}
      <div class="row" style="margin-top:.5rem"><button data-e="${k.id}">Edit</button><button class="danger" data-d="${k.id}">Delete</button></div></div>`).join("")
      : '<p class="card">No trusted contacts yet. Add someone who should be told in an emergency.</p>';
    document.querySelectorAll("[data-e]").forEach(b => b.onclick = () => open(data.find(x => x.id == b.dataset.e)));
    document.querySelectorAll("[data-d]").forEach(b => b.onclick = async () => { if (!confirm("Delete this contact?")) return; try { await api("/api/contacts/" + b.dataset.d, {method: "DELETE"}); toast("Contact deleted"); } catch (e) { toast(e.message, true); } load(); });
  }
  function open(k) { editing = k; $("#dt").textContent = k ? "Edit contact" : "Add contact";
    $("#n").value = k?.name || ""; $("#r").value = k?.relationship || ""; $("#p").value = k?.phone || ""; $("#e").value = k?.email || ""; $("#pr").value = k?.priority || 1; $("#pm").checked = !!k?.is_primary; $("#dlg").showModal(); }
  $("#add").onclick = () => open(null);
  $("#cf").onsubmit = async e => {
    if (e.submitter.value !== "save") return; e.preventDefault();
    const body = {name: $("#n").value.trim(), relationship: $("#r").value || null, phone: $("#p").value || null, email: $("#e").value || null, priority: +$("#pr").value, is_primary: $("#pm").checked};
    try { await api(editing ? "/api/contacts/" + editing.id : "/api/contacts", {method: editing ? "PUT" : "POST", body}); $("#dlg").close(); toast("Contact saved"); load(); }
    catch (er) { toast(er.message, true); }
  };
  load();
})();
