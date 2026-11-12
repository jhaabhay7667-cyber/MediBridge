
let doctorMap = null;
let doctorMarkers = null;
let doctorRadiusCircle = null;

let doctorCoordinates = null;
let doctorResultsData = [];

function doctorElement(id) {
    return document.getElementById(id);
}

function setDoctorStatus(message) {
    doctorElement("doctorStatus").textContent = message;
}

function safeDoctorUrl(value) {
    try {
        const url = new URL(value);

        if (["http:", "https:"].includes(url.protocol)) {
            return url.href;
        }

        return "";
    } catch {
        return "";
    }
}

function initDoctorMap() {
    if (doctorMap || !window.L) {
        return;
    }

    doctorMap = L.map("doctorMap").setView([20, 0], 2);

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(doctorMap);

    doctorMarkers = L.layerGroup().addTo(doctorMap);
}

function getDoctorName(doctor) {
    return doctor.doctor_name || doctor.name || "Name not listed";
}

function getDoctorSpecialty(doctor) {
    return doctor.specialty || "Specialty not listed";
}

function renderDoctorMap(doctors) {
    if (!doctorMap || !doctorCoordinates) {
        return;
    }

    doctorMarkers.clearLayers();

    const bounds = [];

    const userMarker = L.circleMarker(
        [doctorCoordinates.lat, doctorCoordinates.lon],
        {
            radius: 9,
            color: "#ffffff",
            weight: 3,
            fillColor: "#2563eb",
            fillOpacity: 1
        }
    ).bindPopup("Your selected location");

    doctorMarkers.addLayer(userMarker);

    bounds.push([
        doctorCoordinates.lat,
        doctorCoordinates.lon
    ]);

    if (doctorRadiusCircle) {
        doctorMap.removeLayer(doctorRadiusCircle);
    }

    const radius = Number(
        doctorElement("doctorRadius").value
    );

    doctorRadiusCircle = L.circle(
        [doctorCoordinates.lat, doctorCoordinates.lon],
        {
            radius: radius * 1000,
            color: "#0d9488",
            weight: 2,
            fillOpacity: 0.05
        }
    ).addTo(doctorMap);

    doctors.forEach(doctor => {
        const marker = L.marker([
            doctor.latitude,
            doctor.longitude
        ]);

        const popup = document.createElement("div");
        popup.textContent = getDoctorName(doctor);

        marker.bindPopup(popup);

        doctorMarkers.addLayer(marker);

        bounds.push([
            doctor.latitude,
            doctor.longitude
        ]);
    });

    if (bounds.length > 1) {
        doctorMap.fitBounds(bounds, {
            padding: [30, 30],
            maxZoom: 15
        });
    } else {
        doctorMap.setView(
            [doctorCoordinates.lat, doctorCoordinates.lon],
            13
        );
    }

    setTimeout(() => doctorMap.invalidateSize(), 100);
}

function renderDoctorResults() {
    const container = doctorElement("doctorResults");

    const filter = doctorElement(
        "doctorNameFilter"
    ).value.trim().toLowerCase();

    const filtered = doctorResultsData.filter(doctor => {
        const searchable = [
            doctor.name,
            doctor.doctor_name,
            doctor.specialty,
            doctor.address
        ].filter(Boolean).join(" ").toLowerCase();

        return searchable.includes(filter);
    });

    doctorElement("doctorResultCount").textContent =
        `${filtered.length} listing(s) displayed`;

    if (!filtered.length) {
        container.innerHTML = `
            <div class="doctor-empty">
                <h3>No matching listings found</h3>
                <p>
                    Try another name, specialty or location.
                    Some healthcare listings may not be available
                    in OpenStreetMap.
                </p>
            </div>
        `;

        renderDoctorMap([]);
        return;
    }

    container.innerHTML = filtered.map(doctor => {
        const name = esc(getDoctorName(doctor));
        const specialty = esc(getDoctorSpecialty(doctor));
        const address = esc(
            doctor.address || "Address not listed"
        );

        const distance = Number(
            doctor.distance_km
        ).toFixed(2);

        const phone = String(
            doctor.phone || ""
        ).replace(/[^\d+]/g, "");

        const website = safeDoctorUrl(
            doctor.website
        );

        const appointment = safeDoctorUrl(
            doctor.appointment_url
        );

        const source = safeDoctorUrl(
            doctor.source_url
        );

        return `
            <article class="doctor-card">

                <h3>${name}</h3>

                ${
                    doctor.doctor_name
                    ? `<p>Doctor: ${esc(doctor.doctor_name)}</p>`
                    : ""
                }

                <span class="doctor-specialty">
                    ${specialty}
                </span>

                <p>
                    <strong>Clinic type:</strong>
                    ${esc(doctor.listing_type || "Healthcare")}
                </p>

                <p>
                    <strong>Address:</strong>
                    ${address}
                </p>

                <p>
                    <strong>Distance:</strong>
                    ${distance} km (straight-line estimate)
                </p>

                ${
                    phone
                    ? `<p><strong>Phone:</strong> ${esc(doctor.phone)}</p>`
                    : ""
                }

                <div class="doctor-card-actions">

                    ${
                        phone
                        ? `<a href="tel:${esc(phone)}">Call</a>`
                        : ""
                    }

                    ${
                        website
                        ? `<a href="${esc(website)}"
                              target="_blank"
                              rel="noopener noreferrer">
                              Website
                           </a>`
                        : ""
                    }

                    ${
                        appointment
                        ? `<a href="${esc(appointment)}"
                              target="_blank"
                              rel="noopener noreferrer">
                              Appointment
                           </a>`
                        : ""
                    }

                    <a
                        href="https://www.google.com/maps/dir/?api=1&destination=${doctor.latitude},${doctor.longitude}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Directions
                    </a>

                    ${
                        source
                        ? `<a href="${esc(source)}"
                              target="_blank"
                              rel="noopener noreferrer">
                              OSM Source
                           </a>`
                        : ""
                    }

                </div>

                <p class="doctor-source">
                    Source: OpenStreetMap.
                    Information is not independently verified.
                </p>

            </article>
        `;
    }).join("");

    renderDoctorMap(filtered);
}

async function searchDoctors() {
    if (!doctorCoordinates) {
        setDoctorStatus(
            "Please select your location or use the location button."
        );
        return;
    }

    const specialty = doctorElement(
        "doctorSpecialty"
    ).value;

    const radius = doctorElement(
        "doctorRadius"
    ).value;

    const searchButton = doctorElement(
        "doctorSearchBtn"
    );

    searchButton.disabled = true;
    searchButton.textContent = "Searching...";

    setDoctorStatus(
        `Searching OpenStreetMap healthcare listings within ${radius} km...`
    );

    try {
        const params = new URLSearchParams({
            lat: doctorCoordinates.lat,
            lon: doctorCoordinates.lon,
            radius_km: radius,
            specialty: specialty
        });

        const data = await api(
            `/api/doctors/search?${params.toString()}`
        );

        doctorResultsData = data.results || [];

        doctorElement("doctorResultCount").textContent =
            `${data.count || 0} listing(s) found within ${data.radius_km} km`;

        renderDoctorResults();

        if (doctorResultsData.length) {
            setDoctorStatus(
                `${doctorResultsData.length} healthcare listing(s) found. ` +
                `Results are sorted by straight-line distance.`
            );
        } else {
            setDoctorStatus(
                "No matching healthcare listings were found in the selected radius. " +
                "Try another specialty or location."
            );
        }

    } catch (error) {
        console.error("Doctor search error:", error);

        setDoctorStatus(
            error.message ||
            "Unable to search healthcare listings. Please try again."
        );

        doctorResultsData = [];
        renderDoctorResults();

    } finally {
        searchButton.disabled = false;
        searchButton.textContent = "Search Doctors";
    }
}

async function searchDoctorLocation() {
    const location = doctorElement(
        "doctorLocation"
    ).value.trim();

    if (!location) {
        setDoctorStatus(
            "Please enter a city, locality or PIN code."
        );
        return;
    }

    setDoctorStatus(
        "Finding your selected location..."
    );

    try {
        const data = await api(
            `/api/places/geocode?q=${encodeURIComponent(location)}`
        );

        const lat = Number(
            data.lat ?? data.latitude
        );

        const lon = Number(
            data.lon ?? data.longitude
        );

        if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
            throw new Error(
                "Location could not be identified. Try a more specific address."
            );
        }

        doctorCoordinates = { lat, lon };

        initDoctorMap();

        doctorMap.setView([lat, lon], 13);

        await searchDoctors();

    } catch (error) {
        console.error("Location search error:", error);

        setDoctorStatus(
            error.message ||
            "Unable to find this location. Please try another address."
        );
    }
}

function useDoctorCurrentLocation() {
    if (!navigator.geolocation) {
        setDoctorStatus(
            "Your browser does not support location services. Enter a location manually."
        );
        return;
    }

    setDoctorStatus(
        "Requesting your location permission..."
    );

    navigator.geolocation.getCurrentPosition(
        async position => {
            doctorCoordinates = {
                lat: position.coords.latitude,
                lon: position.coords.longitude
            };

            doctorElement("doctorLocation").value =
                "Current location";

            initDoctorMap();

            doctorMap.setView([
                doctorCoordinates.lat,
                doctorCoordinates.lon
            ], 13);

            await searchDoctors();
        },

        error => {
            let message =
                "Unable to access your location.";

            if (error.code === error.PERMISSION_DENIED) {
                message =
                    "Location permission was denied. Enter your city or locality manually.";
            } else if (error.code === error.POSITION_UNAVAILABLE) {
                message =
                    "Your current location is unavailable. Try manual location search.";
            } else if (error.code === error.TIMEOUT) {
                message =
                    "Location request timed out. Please try again.";
            }

            setDoctorStatus(message);
        },

        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 60000
        }
    );
}

document.addEventListener("DOMContentLoaded", async () => {
    await shell("doctors");

    initDoctorMap();

    doctorElement("doctorSearchBtn").addEventListener(
        "click",
        async () => {
            if (doctorElement("doctorLocation").value.trim()
                && doctorElement("doctorLocation").value.trim() !== "Current location") {
                await searchDoctorLocation();
            } else {
                await searchDoctors();
            }
        }
    );

    doctorElement("doctorLocationBtn").addEventListener(
        "click",
        useDoctorCurrentLocation
    );

    doctorElement("doctorNameFilter").addEventListener(
        "input",
        renderDoctorResults
    );

    doctorElement("doctorRadius").addEventListener(
        "change",
        () => {
            if (doctorCoordinates) {
                searchDoctors();
            }
        }
    );

    doctorElement("doctorSpecialty").addEventListener(
        "change",
        () => {
            if (doctorCoordinates) {
                searchDoctors();
            }
        }
    );
});
