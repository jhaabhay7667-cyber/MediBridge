(async function () {

    if (!await shell("reports")) return;

    const fileInput = document.getElementById("reportFile");
    const fileLabel = document.getElementById("selectedFile");
    const form = document.getElementById("reportForm");
    const uploadStatus = document.getElementById("uploadStatus");
    const analyzeButton = document.getElementById("analyzeButton");
    const analysisResult = document.getElementById("analysisResult");
    const reportHistory = document.getElementById("reportHistory");

    const MAX_SIZE = 12 * 1024 * 1024;

    const allowedTypes = {
        "application/pdf": [".pdf"],
        "image/jpeg": [".jpg", ".jpeg"],
        "image/png": [".png"]
    };

    fileInput.addEventListener("change", function () {

        const file = fileInput.files[0];

        if (!file) {
            fileLabel.textContent = "No file selected";
            return;
        }

        fileLabel.textContent = file.name;

        if (file.size > MAX_SIZE) {
            toast("File must be smaller than 12 MB.", true);
            fileInput.value = "";
            fileLabel.textContent = "No file selected";
            return;
        }

        const extension = "." + file.name.split(".").pop().toLowerCase();

        const validExtension = Object.values(allowedTypes)
            .flat()
            .includes(extension);

        if (!validExtension) {
            toast("Only PDF, JPG, JPEG and PNG are supported.", true);
            fileInput.value = "";
            fileLabel.textContent = "No file selected";
        }

    });


    function safe(value) {
        return esc(value ?? "");
    }


    function listItems(items) {

        if (!Array.isArray(items) || items.length === 0) {
            return "<p class='muted'>No information provided.</p>";
        }

        return `
            <ul>
                ${items.map(item => `<li>${safe(item)}</li>`).join("")}
            </ul>
        `;
    }


    function renderAnalysis(data) {

        const findings = Array.isArray(data.findings)
            ? data.findings
            : [];

        const findingHTML = findings.map(item => {

            const status = String(item.status || "inconclusive")
                .toLowerCase()
                .replace(/[^a-z-]/g, "");

            return `
                <div class="finding">

                    <h3>${safe(item.test_name || "Test")}</h3>

                    <p>
                        <strong>Value:</strong>
                        ${safe(item.value || "Not provided")}
                        ${safe(item.unit || "")}
                    </p>

                    <p>
                        <strong>Reference range:</strong>
                        ${safe(item.reference_range || "Not provided")}
                    </p>

                    <p>
                        <strong>Status:</strong>
                        <span class="status-${status}">
                            ${safe(item.status || "Inconclusive")}
                        </span>
                    </p>

                    <p>
                        <strong>Explanation:</strong>
                        ${safe(item.explanation || "No explanation provided.")}
                    </p>

                </div>
            `;

        }).join("");


        analysisResult.innerHTML = `

            <div class="result-section">
                <h3>Report Overview</h3>
                <p>${safe(data.summary || "No summary provided.")}</p>
            </div>

            <div class="result-section">
                <h3>Test Findings</h3>

                ${findingHTML || "<p>No findings were returned.</p>"}
            </div>

            <div class="result-section">
                <h3>Questions for Your Doctor</h3>
                ${listItems(data.questions_for_doctor)}
            </div>

            <div class="result-section">
                <h3>Urgency Information</h3>
                <p>${safe(data.urgency || "Unclear")}</p>
            </div>

            <div class="result-section">
                <h3>Limitations</h3>
                ${listItems(data.limitations)}
            </div>

            <div class="notice">
                AI-generated information only. This is not a diagnosis.
                Consult a qualified doctor for medical interpretation.
            </div>

            <div class="report-actions noprint">
                <button type="button" id="printReport">
                    Print Analysis
                </button>
            </div>

        `;

        document.getElementById("printReport").onclick = () => window.print();

    }


    async function loadHistory() {

        reportHistory.innerHTML = "<p class='muted'>Loading...</p>";

        try {

            const reports = await api("/api/reports");

            if (!Array.isArray(reports) || reports.length === 0) {
                reportHistory.innerHTML =
                    "<p class='empty-state'>No saved reports yet.</p>";
                return;
            }

            reportHistory.innerHTML = reports.map(report => `

                <div class="history-item">

                    <div>
                        <strong>${safe(report.filename)}</strong>

                        <p class="muted">
                            ${safe(fmt(report.created_at))}
                        </p>
                    </div>

                    <div class="report-actions">

                        <button
                            type="button"
                            data-view="${Number(report.id)}">
                            View
                        </button>

                        <button
                            type="button"
                            class="danger"
                            data-delete="${Number(report.id)}">
                            Delete
                        </button>

                    </div>

                </div>

            `).join("");


            reportHistory.querySelectorAll("[data-view]").forEach(button => {

                button.addEventListener("click", async () => {

                    const id = Number(button.dataset.view);

                    try {

                        const report = await api("/api/reports/" + id);

                        renderAnalysis(report.analysis);

                        analysisResult.scrollIntoView({
                            behavior: "smooth",
                            block: "start"
                        });

                    } catch (error) {
                        toast(error.message, true);
                    }

                });

            });


            reportHistory.querySelectorAll("[data-delete]").forEach(button => {

                button.addEventListener("click", async () => {

                    const id = Number(button.dataset.delete);

                    if (!confirm("Delete this saved report permanently?")) {
                        return;
                    }

                    try {

                        await api("/api/reports/" + id, {
                            method: "DELETE"
                        });

                        toast("Report deleted successfully.");

                        loadHistory();

                    } catch (error) {
                        toast(error.message, true);
                    }

                });

            });

        } catch (error) {

            reportHistory.innerHTML =
                "<p class='muted'>Unable to load report history.</p>";

            toast(error.message, true);

        }

    }


    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        const file = fileInput.files[0];

        if (!file) {
            toast("Please select a medical report first.", true);
            return;
        }

        if (file.size > MAX_SIZE) {
            toast("Maximum file size is 12 MB.", true);
            return;
        }

        const extension = "." + file.name.split(".").pop().toLowerCase();

        const validExtension = Object.values(allowedTypes)
            .flat()
            .includes(extension);

        if (!validExtension) {
            toast("Unsupported file format.", true);
            return;
        }

        const formData = new FormData();

        formData.append("file", file);

        formData.append(
            "language",
            document.getElementById("reportLanguage").value
        );

        analyzeButton.disabled = true;
        analyzeButton.textContent = "Analyzing...";

        uploadStatus.textContent =
            "Uploading report. Please wait...";

        analysisResult.innerHTML =
            "<p class='muted'>Your report is being processed...</p>";

        try {

            const response = await fetch(
                API + "/api/reports/analyze",
                {
                    method: "POST",

                    headers: {
                        Authorization: "Bearer " + token()
                    },

                    body: formData
                }
            );

            const result = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(
                    result.detail || "Report analysis failed."
                );
            }

            renderAnalysis(result.analysis || {});

            uploadStatus.textContent =
                "Report analyzed and saved successfully.";

            toast("Medical report analysis completed.");

            await loadHistory();

        } catch (error) {

            uploadStatus.textContent = error.message;

            analysisResult.innerHTML = `
                <div class="notice">
                    ${safe(error.message)}
                </div>
            `;

            toast(error.message, true);

        } finally {

            analyzeButton.disabled = false;
            analyzeButton.textContent = "Analyze Medical Report";

        }

    });


    document.getElementById("clearButton").addEventListener("click", () => {

        fileLabel.textContent = "No file selected";
        uploadStatus.textContent = "";

    });


    document.getElementById("refreshHistory").addEventListener(
        "click",
        loadHistory
    );

    await loadHistory();

})();