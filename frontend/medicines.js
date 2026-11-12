function setMedicineStatus(message) {
  document.getElementById("medicineStatus").textContent = message;
}

function medicineSection(title, content) {
  if (!content) return "";

  return `
    <section class="medicine-section">
      <h3>${esc(title)}</h3>
      <p>${esc(content)}</p>
    </section>
  `;
}

function renderMedicines(medicines) {
  const container = document.getElementById("medicineResults");

  if (!medicines.length) {
    container.innerHTML = `
      <p>No matching public FDA label records were found.
      This does not mean the medicine is unavailable or unsafe.
      Try its generic name or another spelling.</p>
    `;
    return;
  }

  container.innerHTML = medicines.map((medicine, index) => {
    const brands = (medicine.brand_names || []).join(", ");
    const generics = (medicine.generic_names || []).join(", ");
    const manufacturers = (medicine.manufacturers || []).join(", ");

    return `
      <article class="medicine-card">

        <h2>Medicine record ${index + 1}</h2>

        <p><strong>Brand name:</strong>
          ${esc(brands || "Not listed")}
        </p>

        <p><strong>Generic name:</strong>
          ${esc(generics || "Not listed")}
        </p>

        <p><strong>Manufacturer:</strong>
          ${esc(manufacturers || "Not listed")}
        </p>

        ${medicineSection(
          "Purpose",
          medicine.purpose
        )}

        ${medicineSection(
          "Indications and usage",
          medicine.indications_and_usage
        )}

        ${medicineSection(
          "Warnings",
          medicine.warnings
        )}

        ${medicineSection(
          "Contraindications",
          medicine.contraindications
        )}

        ${medicineSection(
          "Adverse reactions",
          medicine.adverse_reactions
        )}

        ${medicineSection(
          "Drug interactions — label information",
          medicine.drug_interactions
        )}

        <p class="medicine-muted">
          Label effective date: ${esc(medicine.effective_time || "Not provided")}
        </p>

        <p class="medicine-muted">
          Source: ${esc(medicine.source)}
        </p>

        <a
          class="medicine-source"
          href="https://open.fda.gov/apis/drug/label/"
          target="_blank"
          rel="noopener noreferrer"
        >
          Read official source documentation
        </a>

      </article>
    `;
  }).join("");
}

async function searchMedicines(event) {
  event.preventDefault();

  const input = document.getElementById("medicineInput");
  const query = input.value.trim();

  if (query.length < 2) {
    toast("Enter at least 2 characters.", true);
    return;
  }

  const button = document.getElementById("medicineSearchButton");

  button.disabled = true;
  button.textContent = "Searching…";

  setMedicineStatus("Searching public medicine information…");

  document.getElementById("medicineResults").innerHTML = "";

  try {
    const params = new URLSearchParams({ q: query });

    const data = await api(
      `/api/medicines/search?${params.toString()}`
    );

    renderMedicines(data.medicines || []);

    setMedicineStatus(
      `${data.count} medicine record(s) found.`
    );

  } catch (error) {
    setMedicineStatus(error.message);
    toast(error.message, true);

  } finally {
    button.disabled = false;
    button.textContent = "Search medicine";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await shell("medicines")) return;

  document.getElementById("medicineSearchForm")
    .addEventListener("submit", searchMedicines);
});