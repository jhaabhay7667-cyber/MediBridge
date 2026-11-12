let hospitalMap;
let hospitalMarkers;
let selectedCoordinates = null;
let selectedLocationName = "";
function safeExternalUrl(value) {
  try {
    const url = new URL(value);

    return ["http:", "https:"].includes(url.protocol)
      ? url.href
      : "";
  } catch {
    return "";
  }
}
function setHospitalStatus(message) {
  document.getElementById("hospitalStatus").textContent = message;
}

function initHospitalMap() {
  if (hospitalMap) return;

  // Generic India map view, not the user's detected location.
  hospitalMap = L.map("hospitalMap").setView([20.5937, 78.9629], 5);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }).addTo(hospitalMap);

  hospitalMarkers = L.layerGroup().addTo(hospitalMap);
}

function updateSelectedLocation(lat, lon, name) {
  selectedCoordinates = {
    latitude: Number(lat),
    longitude: Number(lon)
  };

  selectedLocationName = name || "Selected location";

  document.getElementById("selectedLocation").textContent =
    `${selectedLocationName} (${selectedCoordinates.latitude.toFixed(5)}, ${selectedCoordinates.longitude.toFixed(5)})`;

  hospitalMap.setView(
    [selectedCoordinates.latitude, selectedCoordinates.longitude],
    13
  );

  L.circleMarker(
    [selectedCoordinates.latitude, selectedCoordinates.longitude],
    {
      radius: 8,
      color: "#2563eb",
      fillColor: "#60a5fa",
      fillOpacity: 0.9
    }
  ).addTo(hospitalMarkers).bindPopup("Selected search location");
}

async function useCurrentLocation() {
  if (!navigator.geolocation) {
    toast("Location is not supported by this browser.", true);
    return;
  }

  setHospitalStatus("Getting your current location…");

  try {
    const coords = await getPosition();

    hospitalMarkers.clearLayers();

    updateSelectedLocation(
      coords.latitude,
      coords.longitude,
      "Your current location"
    );

    await loadNearbyHospitals();

  } catch (error) {
    setHospitalStatus(error.message);
    toast(error.message, true);
  }
}

async function searchManualLocation(event) {
  event.preventDefault();

  const input = document.getElementById("locationInput");
  const query = input.value.trim();

  if (query.length < 2) {
    toast("Please enter a valid location.", true);
    return;
  }

  setHospitalStatus("Searching location…");

  try {
    const response = await fetch(
      `${API}/api/places/geocode?q=${encodeURIComponent(query)}`
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || "Location search failed.");
    }

    if (!data.results || data.results.length === 0) {
      throw new Error("No matching location found. Try another search.");
    }

    const result = data.results[0];

    hospitalMarkers.clearLayers();

    updateSelectedLocation(
      result.latitude,
      result.longitude,
      result.name
    );

    await loadNearbyHospitals();

  } catch (error) {
    setHospitalStatus(error.message);
    toast(error.message, true);
  }
}


async function loadNearbyHospitals() {
  if (!selectedCoordinates) {
    toast("Select a location first.", true);
    return;
  }

  const radius = Number(
    document.getElementById("radiusSelect").value
  );

  setHospitalStatus("Searching nearby hospitals…");
  document.getElementById("hospitalResults").innerHTML = "";

  hospitalMarkers.clearLayers();

  // Show selected location marker.
  L.circleMarker(
    [
      selectedCoordinates.latitude,
      selectedCoordinates.longitude
    ],
    {
      radius: 8,
      color: "#2563eb",
      fillColor: "#60a5fa",
      fillOpacity: 0.9
    }
  ).addTo(hospitalMarkers).bindPopup("Selected location");

  const params = new URLSearchParams({
    lat: selectedCoordinates.latitude,
    lon: selectedCoordinates.longitude,
    radius_km: radius
  });

  try {
    const data = await api(
      `/api/places/hospitals?${params.toString()}`
    );

    // Display hospital cards and map markers.
    renderHospitalResults(data.hospitals || []);

    setHospitalStatus(
      `${data.count} hospital(s) found within ${radius} km.`
    );

  } catch (error) {
    setHospitalStatus(error.message);
    toast(error.message, true);
  }
}


function renderHospitalResults(hospitals) {
  const container = document.getElementById("hospitalResults");

  if (!hospitals.length) {
    container.innerHTML =
      "<p>No mapped hospitals were found in this radius. Try a larger radius or another location.</p>";
    return;
  }

  container.innerHTML = hospitals.map((hospital, index) => {
    const lat = Number(hospital.latitude);
    const lon = Number(hospital.longitude);

    const directionsUrl =
      `https://www.openstreetmap.org/directions?from=${selectedCoordinates.latitude},${selectedCoordinates.longitude}&to=${lat},${lon}`;

    const phoneHtml = hospital.phone
      ? `<p><strong>Phone:</strong> ${esc(hospital.phone)}</p>`
      : `<p class="hospital-muted">Phone number not listed</p>`;

    const addressHtml = hospital.address
      ? `<p><strong>Address:</strong> ${esc(hospital.address)}</p>`
      : `<p class="hospital-muted">Address not listed</p>`;

    
const safeWebsite = safeExternalUrl(hospital.website);

const websiteHtml = safeWebsite
  ? `<a href="${esc(safeWebsite)}" target="_blank" rel="noopener noreferrer">Website</a>`
  : "";

    return `
      <article class="hospital-card">
        <h3>${index + 1}. ${esc(hospital.name)}</h3>

        <p><strong>Distance:</strong> ${Number(hospital.distance_km).toFixed(2)} km (straight-line)</p>

        ${addressHtml}
        ${phoneHtml}

        <p class="hospital-muted">
          Source: OpenStreetMap. Details are not independently verified.
        </p>

        <div class="hospital-actions">
          <a href="${directionsUrl}" target="_blank" rel="noopener noreferrer">
            Directions
          </a>
          ${websiteHtml}
          ${
            hospital.phone
              ? `<a href="tel:${esc(String(hospital.phone).replace(/[^0-9+*#,;]/g, ""))}">Call</a>`
              : ""
          }
        </div>
      </article>
    `;
  }).join("");

  hospitals.forEach((hospital) => {
    const marker = L.marker([
      hospital.latitude,
      hospital.longitude
    ]);

    marker.bindPopup(`
      <strong>${esc(hospital.name)}</strong><br>
      ${Number(hospital.distance_km).toFixed(2)} km away
    `);

    marker.addTo(hospitalMarkers);
  });

  if (hospitals.length) {
    const points = [
      [
        selectedCoordinates.latitude,
        selectedCoordinates.longitude
      ],
      ...hospitals.map(h => [h.latitude, h.longitude])
    ];

    hospitalMap.fitBounds(points, { padding: [25, 25] });
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!await shell("hospitals")) return;

  initHospitalMap();

  document.getElementById("currentLocationBtn")
    .addEventListener("click", useCurrentLocation);

  document.getElementById("findHospitalsBtn")
    .addEventListener("click", loadNearbyHospitals);

  document.getElementById("locationSearchForm")
    .addEventListener("submit", searchManualLocation);

  document.getElementById("radiusSelect")
    .addEventListener("change", () => {
      if (selectedCoordinates) loadNearbyHospitals();
    });
});