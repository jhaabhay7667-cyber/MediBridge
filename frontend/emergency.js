
(async () => {
  if (!await shell("")) return;

  const id = new URLSearchParams(location.search).get("id");
  const c = $("#content");

  if (!id) {
    c.innerHTML = '<p class="card">No emergency selected. <a href="history.html">View history</a></p>';
    return;
  }

  const AMB = ["SEARCHING", "REQUESTED", "ASSIGNED", "EN_ROUTE", "ARRIVED", "COMPLETED", "UNAVAILABLE"];
  const HOS = ["SEARCHING", "REQUESTED", "PENDING", "ACCEPTED", "REJECTED", "READY", "ARRIVED", "COMPLETED"];

  let facMap = {};
  let nearby = null;

  const opts = (a, v) =>
    a.map(x => `<option ${x === v ? "selected" : ""}>${x}</option>`).join("");

  function safePhone(value) {
    const phone = String(value || "").replace(/[^\d+]/g, "");
    const digits = phone.replace(/\D/g, "");
    return digits.length >= 7 && digits.length <= 15 ? phone : "";
  }

  function locationMessage(latitude, longitude) {
    if (latitude == null || longitude == null) {
      return "Location is not available. Please share your current location manually.";
    }

    const mapUrl = `https://www.google.com/maps?q=${latitude},${longitude}`;

    return `Emergency! I may need help. My location: ${mapUrl}`;
  }

  async function shareLocation(em) {
    let latitude = em.latitude;
    let longitude = em.longitude;

    if (latitude == null || longitude == null) {
      try {
        const position = await getPosition();
        latitude = position.latitude;
        longitude = position.longitude;
      } catch (error) {
        toast("Location permission was not granted or location is unavailable.", true);
        return;
      }
    }

    const message = locationMessage(latitude, longitude);

    try {
      if (navigator.share) {
        await navigator.share({
          title: "MediBridge Emergency Location",
          text: message
        });
        toast("Location sharing opened. Confirm sharing in your device.");
        return;
      }

      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(message);
        toast("Location message copied. You can paste it into a message.");
        return;
      }

      window.prompt("Copy this emergency location message:", message);
    } catch (error) {
      if (error.name !== "AbortError") {
        toast("Could not open location sharing. Please share your location manually.", true);
      }
    }
  }

  async function run(fn, ok) {
    try {
      await fn();
      if (ok) toast(ok);
    } catch (error) {
      toast(error.message, true);
    }
    await load();
  }

  async function load() {
    loading(c);

    let em, tl, nt, cts;

    try {
      [em, tl, nt, cts] = await Promise.all([
        api(`/api/emergencies/${id}`),
        api(`/api/emergencies/${id}/timeline`),
        api(`/api/emergencies/${id}/notifications`),
        api("/api/contacts")
      ]);

      if (!Object.keys(facMap).length) {
        const facilities = await api("/api/facilities");
        facilities.forEach(f => facMap[f.id] = f);
      }
    } catch (error) {
      c.innerHTML = `<p class="card">${esc(error.message)} <a href="history.html">Back to history</a></p>`;
      return;
    }

    const hasLoc = em.latitude != null && em.longitude != null;
    const active = em.status === "ACTIVE";
    const fac = facMap[em.hospital?.facility_id];

    const contactMessage = locationMessage(
      hasLoc ? em.latitude : null,
      hasLoc ? em.longitude : null
    );

    const contactCards = cts.length
      ? cts.map(k => {
          const phone = safePhone(k.phone);
          const callLink = phone
            ? `<a class="btn" href="tel:${esc(phone)}">Call</a>`
            : "";

          const smsLink = phone
            ? `<a class="btn" href="sms:${esc(phone)}?body=${encodeURIComponent(contactMessage)}">SMS</a>`
            : "";

          return `
            <li>
              <b>${esc(k.name)}</b>
              (${esc(k.relationship || "contact")})
              ${k.is_primary ? "★ primary" : ""}
              <br>
              ${k.phone ? `Phone: ${esc(k.phone)}` : ""}
              ${k.email ? `<br>Email: ${esc(k.email)}` : ""}
              <div class="row noprint">
                ${callLink}
                ${smsLink}
              </div>
            </li>
          `;
        }).join("")
      : '<p>No trusted contacts yet. <a href="contacts.html">Add a contact</a></p>';

    const nearbyHtml = nearby
      ? nearby.map(f => {
          const phone = safePhone(f.phone);

          return `
            <div class="card">
              <b>${esc(f.name)}</b>
              ${f.is_demo ? '<span class="badge">DEMO DATA</span>' : ""}
              <br>
              ${esc(String(f.distance_km))} km · ${esc(f.type)} · ${esc(f.address || "")}
              <br>
              ${phone ? `<a class="btn" href="tel:${esc(phone)}">Call facility</a>` : ""}
              <a class="btn" target="_blank" rel="noopener"
                 href="https://www.google.com/maps/dir/?api=1&destination=${f.latitude},${f.longitude}">
                Directions
              </a>
              <button data-f="${f.id}" class="pick noprint">Select facility</button>
              ${f.is_demo
                ? '<p class="muted">Demo facility: details and availability are not verified.</p>'
                : '<p class="muted">Listing information is not a confirmation of emergency capacity or availability.</p>'}
            </div>
          `;
        }).join("")
      : "";

    c.innerHTML = `
      <section class="card" role="alert">
        <h2>Emergency assistance</h2>
        <p><b>If someone is in immediate danger, call India's emergency number now.</b></p>
        <p>Do not wait for this app, an AI response, or location processing.</p>
        <a class="btn danger" href="tel:112">Call Emergency 112</a>
        <p class="muted">
          This opens your phone's calling app. You must place the call.
          MediBridge does not automatically contact 112.
        </p>
      </section>

      <section class="card">
        <h2>${esc(em.code)} ${pBadge(em.priority)} ${sBadge(em.status)}</h2>

        <p>
          Patient: <b>${esc(em.patient_name)}</b>
          ${em.patient_age != null ? ", " + em.patient_age : ""}
          · Blood group: ${esc(em.blood_group || "–")}<br>

          Incident: ${esc(em.incident_type)}
          · Condition: ${esc(em.condition || "–")}<br>

          Symptoms: ${esc(em.symptoms || "–")}<br>
          Notes: ${esc(em.notes || "–")}<br>
          Time: ${fmt(em.created_at)}<br>

          Location: ${esc(em.location_text || "–")}
          (${hasLoc
            ? `${em.latitude.toFixed(5)}, ${em.longitude.toFixed(5)}`
            : "coordinates not captured"})
          ${hasLoc
            ? `· <a href="https://www.google.com/maps?q=${em.latitude},${em.longitude}" target="_blank" rel="noopener">Open map</a>`
            : ""}
        </p>

        <div class="row noprint">
          <button id="print">Print / save as PDF</button>
          ${active ? '<button class="danger" id="resolve">Mark resolved</button>' : ""}
        </div>
      </section>

      <section class="card">
        <h2>Share emergency location</h2>
        <p>
          Location is shared only after you press the button and approve
          the browser/device permission or sharing action.
        </p>
        <p>
          ${hasLoc
            ? "Coordinates are available for this emergency."
            : "Coordinates are not saved yet. You can request your current device location."}
        </p>
        <button class="primary noprint" id="share-location">
          Share my location
        </button>
      </section>

      <section class="card">
        <h2>Trusted contacts</h2>
        <ul>${contactCards}</ul>

        <button class="primary noprint" id="notify"
          ${cts.some(k => k.email) ? "" : "disabled"}>
          Email trusted contacts
        </button>

        <p class="muted">
          Call and SMS links open your device apps. Review the recipient
          and message before sending. Email notifications depend on the
          configured backend email service.
        </p>
      </section>

      <section class="card">
        <h2>Ambulance coordination</h2>

        <p>
          Status: ${sBadge(em.ambulance.status)}
          ${em.ambulance.provider ? esc(em.ambulance.provider) : ""}
          ${em.ambulance.eta_minutes != null
            ? "ETA " + em.ambulance.eta_minutes + " min"
            : ""}
        </p>

        <p class="muted">
          ${esc(em.ambulance.notes ||
            "No ambulance provider is connected. Requests are recorded here only. Call emergency services directly.")}
        </p>

        <div class="row noprint">
          <button id="amb">Record ambulance request</button>
          <label class="muted" for="as" style="margin:0">Status</label>
          <select id="as" style="width:auto">${opts(AMB, em.ambulance.status)}</select>
          <button id="asu">Update</button>
        </div>

        <p class="muted">
          Recording a request does not dispatch an ambulance.
        </p>
      </section>

      <section class="card">
        <h2>Hospital coordination</h2>

        <p>
          Status: ${sBadge(em.hospital.status)}
          · Facility:
          ${fac
            ? esc(fac.name) + (fac.is_demo ? " (demo data)" : "")
            : "not selected"}
        </p>

        <div class="row noprint">
          <label class="muted" for="hs" style="margin:0">Status</label>
          <select id="hs" style="width:auto">${opts(HOS, em.hospital.status)}</select>
          <button id="hsu">Update</button>
          <button id="near" ${hasLoc ? "" : "disabled"}>
            Find nearby facilities
          </button>
        </div>

        ${hasLoc
          ? ""
          : '<p class="muted">Coordinates are required to search nearby facilities.</p>'}

        <div id="nearby">
          ${nearbyHtml || (nearby === null ? "" : "<p>No facilities within 25 km.</p>")}
        </div>

        <p class="muted">
          Nearby listings may be incomplete or outdated. MediBridge does not
          verify live hospital capacity, emergency services, or bed availability.
          Call 112 for urgent help.
        </p>
      </section>

      <section class="card">
        <h2>Basic first-aid information</h2>
        <p class="notice">
          First aid is not a substitute for professional care.
          Call 112 for serious or life-threatening emergencies.
          Follow the emergency operator's instructions.
        </p>

        <details>
          <summary>Severe bleeding</summary>
          <ul>
            <li>Make sure the area is safe before approaching.</li>
            <li>Call 112 for severe or uncontrolled bleeding.</li>
            <li>Apply firm, continuous direct pressure using clean cloth or gauze.</li>
            <li>If blood soaks through, place more material on top and keep applying pressure.</li>
            <li>Do not remove an embedded object. Apply pressure around it.</li>
          </ul>
        </details>

        <details>
          <summary>Unconscious person or abnormal breathing</summary>
          <ul>
            <li>Call 112 immediately.</li>
            <li>Check responsiveness and normal breathing.</li>
            <li>If the person is not breathing normally or is only gasping, follow the emergency operator's CPR instructions.</li>
            <li>Use an AED if available and follow its voice instructions.</li>
            <li>Do not give food, drink, or medicine to an unconscious person.</li>
            <li>Avoid moving someone with a possible neck or spinal injury unless there is immediate danger.</li>
          </ul>
        </details>

        <details>
          <summary>Seizure</summary>
          <ul>
            <li>Move nearby dangerous objects away and protect the person's head.</li>
            <li>Do not restrain the person.</li>
            <li>Do not put anything in their mouth.</li>
            <li>Time the seizure. When movements stop, check breathing.</li>
            <li>Call 112 for a first seizure, a seizure lasting 5 minutes or longer, repeated seizures, injury, breathing difficulty, or failure to recover.</li>
          </ul>
        </details>

        <details>
          <summary>Burns</summary>
          <ul>
            <li>Stop the burning process and move away from the heat source if safe.</li>
            <li>Cool the burn under cool running water for 20 minutes if possible.</li>
            <li>Remove jewellery or loose clothing near the burn, but do not pull away anything stuck to the skin.</li>
            <li>Do not apply ice, toothpaste, butter, oils, or creams.</li>
            <li>Seek urgent medical care for serious, large, deep, chemical, or electrical burns.</li>
          </ul>
        </details>

        <details>
          <summary>Suspected poisoning</summary>
          <ul>
            <li>Move away from the source only if it is safe to do so.</li>
            <li>Seek emergency medical advice immediately. Call 112 if the person is seriously unwell.</li>
            <li>Do not induce vomiting.</li>
            <li>Do not give food, drink, or home remedies unless a medical professional instructs you.</li>
            <li>Keep the product container or label for medical professionals.</li>
          </ul>
        </details>
      </section>

      <section class="card">
        <h2>Notifications</h2>
        ${nt.length
          ? `<table class="resp"><tbody>
              ${nt.map(n => `
                <tr>
                  <td>${fmt(n.created_at)}</td>
                  <td>${esc(n.type)}</td>
                  <td>${esc(n.channel)} ${esc(n.recipient || "")}</td>
                  <td>${sBadge(n.status)} ${esc(n.error || "")}</td>
                </tr>
              `).join("")}
            </tbody></table>`
          : "<p>None yet.</p>"}
      </section>

      <section class="card">
        <h2>Timeline</h2>
        <ul class="tl">
          ${tl.map(e => `
            <li>
              <b>${fmt(e.created_at)}</b>
              ${esc(e.event)}
              <span class="muted">
                — ${esc(e.actor || "system")}
                ${e.status ? ", " + esc(e.status) : ""}
              </span>
            </li>
          `).join("")}
        </ul>
      </section>
    `;

    $("#print").onclick = () => print();

    $("#share-location").onclick = () => shareLocation(em);

    const resolveButton = $("#resolve");
    if (resolveButton) {
      resolveButton.onclick = () =>
        confirm("Mark this emergency as resolved?") &&
        run(
          () => api(`/api/emergencies/${id}`, {
            method: "PATCH",
            body: { status: "RESOLVED" }
          }),
          "Emergency resolved"
        );
    }

    $("#notify").onclick = () => run(async () => {
      const result = await api(`/api/emergencies/${id}/notify`, {
        method: "POST"
      });

      const failed = result.results.filter(x => x.status === "FAILED");

      if (failed.length) {
        toast(
          `${failed.length} email(s) failed: ${failed.map(x => x.contact).join(", ")}`,
          true
        );
      }
    }, "Contacts emailed");

    $("#amb").onclick = () =>
      run(
        () => api(`/api/emergencies/${id}/ambulance`, { method: "POST" }),
        "Ambulance request recorded. This is not a dispatch."
      );

    $("#asu").onclick = () =>
      run(
        () => api(`/api/emergencies/${id}/coordination`, {
          method: "PATCH",
          body: { ambulance_status: $("#as").value }
        }),
        "Ambulance status updated"
      );

    $("#hsu").onclick = () =>
      run(
        () => api(`/api/emergencies/${id}/coordination`, {
          method: "PATCH",
          body: { hospital_status: $("#hs").value }
        }),
        "Hospital status updated"
      );

    $("#near").onclick = async () => {
      try {
        nearby = await api(
          `/api/facilities/nearby?lat=${em.latitude}&lon=${em.longitude}&radius_km=25`
        );
        await load();
      } catch (error) {
        toast(error.message, true);
      }
    };

    document.querySelectorAll(".pick").forEach(button => {
      button.onclick = () =>
        run(
          () => api(
            `/api/emergencies/${id}/hospital?facility_id=${button.dataset.f}`,
            { method: "POST" }
          ),
          "Facility selected"
        );
    });
  }

  load();
})();
