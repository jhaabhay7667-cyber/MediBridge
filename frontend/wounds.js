
let woundPreviewUrl = null;

function setWoundStatus(message) {
  document.getElementById("woundStatus").textContent = message;
}

function setWoundResult(message) {
  document.getElementById("woundResult").textContent = message;
}

function updateWoundSubmitState() {
  const file = document.getElementById("woundImage").files[0];
  const consent = document.getElementById("woundConsent").checked;

  document.getElementById("woundSubmit").disabled =
    !(file && consent);
}

function previewWoundImage() {
  const input = document.getElementById("woundImage");
  const preview = document.getElementById("woundPreview");
  const file = input.files[0];

  if (woundPreviewUrl) {
    URL.revokeObjectURL(woundPreviewUrl);
    woundPreviewUrl = null;
  }

  preview.style.display = "none";
  preview.removeAttribute("src");

  if (!file) {
    updateWoundSubmitState();
    return;
  }

  const allowedTypes = ["image/jpeg", "image/png"];

  if (!allowedTypes.includes(file.type)) {
    input.value = "";
    toast("Please select a JPG or PNG image.", true);
    updateWoundSubmitState();
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    input.value = "";
    toast("Image must be 5 MB or smaller.", true);
    updateWoundSubmitState();
    return;
  }

  woundPreviewUrl = URL.createObjectURL(file);
  preview.src = woundPreviewUrl;
  preview.style.display = "block";

  updateWoundSubmitState();
}

async function submitWoundImage(event) {
  event.preventDefault();

  const input = document.getElementById("woundImage");
  const file = input.files[0];
  const consent = document.getElementById("woundConsent").checked;

  if (!file || !consent) {
    toast("Select an image and provide consent first.", true);
    return;
  }

  const button = document.getElementById("woundSubmit");

  button.disabled = true;
  button.textContent = "Analyzing…";

  setWoundStatus("Uploading image securely to the MediBridge backend…");
  setWoundResult("Waiting for AI observations…");

  const formData = new FormData();
  formData.append("file", file);
  formData.append("consent", "true");

  try {
    const response = await fetch(`${API}/api/wounds/analyze`, {
      method: "POST",
      headers: {
        ...(token() ? {
          Authorization: "Bearer " + token()
        } : {})
      },
      body: formData
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        typeof data.detail === "string"
          ? data.detail
          : "Image analysis failed."
      );
    }

    setWoundResult(data.result || "No observation was returned.");

    setWoundStatus(
      `Assessment #${data.id} saved successfully.`
    );

    await loadWoundHistory();

  } catch (error) {
    setWoundStatus(error.message);
    setWoundResult("No assessment was saved.");
    toast(error.message, true);

  } finally {
    button.textContent = "Analyze image";
    updateWoundSubmitState();
  }
}

async function loadWoundHistory() {
  const container = document.getElementById("woundHistory");

  try {
    const data = await api("/api/wounds/");

    const records = data.assessments || [];

    if (!records.length) {
      container.textContent = "No previous assessments found.";
      return;
    }

    container.innerHTML = records.map(record => `
      <div class="wound-history-item">
        <div>
          <strong>${esc(record.filename)}</strong>
          <p class="hospital-muted">
            ${esc(fmt(record.created_at))}
          </p>
          <small>Assessment #${Number(record.id)}</small>
        </div>

        <div>
          <button
            type="button"
            data-wound-action="view"
            data-wound-id="${Number(record.id)}"
          >
            View
          </button>

          <button
            type="button"
            data-wound-action="delete"
            data-wound-id="${Number(record.id)}"
          >
            Delete
          </button>
        </div>
      </div>
    `).join("");

  } catch (error) {
    container.textContent = error.message;
  }
}

async function viewWoundAssessment(id) {
  try {
    const data = await api(`/api/wounds/${id}`);

    setWoundResult(data.result || "No saved observation.");
    setWoundStatus(`Viewing saved assessment #${id}.`);

  } catch (error) {
    toast(error.message, true);
  }
}

async function deleteWoundAssessment(id) {
  if (!confirm("Delete this wound assessment permanently?")) {
    return;
  }

  try {
    await api(`/api/wounds/${id}`, {
      method: "DELETE"
    });

    toast("Assessment deleted.");
    setWoundResult("Select an assessment to view its observation.");

    await loadWoundHistory();

  } catch (error) {
    toast(error.message, true);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await shell("wounds")) return;

  document.getElementById("woundImage")
    .addEventListener("change", previewWoundImage);

  document.getElementById("woundConsent")
    .addEventListener("change", updateWoundSubmitState);

  document.getElementById("woundForm")
    .addEventListener("submit", submitWoundImage);

  document.getElementById("woundHistory")
    .addEventListener("click", event => {
      const button = event.target.closest("button[data-wound-action]");

      if (!button) return;

      const id = Number(button.dataset.woundId);

      if (!Number.isInteger(id) || id <= 0) return;

      if (button.dataset.woundAction === "view") {
        viewWoundAssessment(id);
      }

      if (button.dataset.woundAction === "delete") {
        deleteWoundAssessment(id);
      }
    });

  await loadWoundHistory();
});
