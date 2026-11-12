
let editingFamilyProfileId = null;
let activeFamilyShareProfileId = null;

const familyById = new Map();

function familyMessage(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) element.textContent = message;
}

function familyValue(id) {
    return document.getElementById(id)?.value?.trim() || "";
}

function familySetValue(id, value) {
    const element = document.getElementById(id);
    if (element) element.value = value || "";
}

function familySafeText(value) {
    if (typeof esc === "function") return esc(String(value ?? ""));
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function familyResetForm() {
    editingFamilyProfileId = null;
    document.getElementById("familyProfileForm").reset();

    document.getElementById("familyFormHeading").textContent =
        "Create a family profile";

    document.getElementById("familySaveButton").textContent =
        "Save profile";

    document.getElementById("familyCancelEdit").classList.add("family-hidden");
    familyMessage("familyFormStatus", "");
}

function familyFillForm(profile) {
    editingFamilyProfileId = profile.id;

    familySetValue("familyName", profile.full_name);
    familySetValue("familyRelationship", profile.relationship);
    familySetValue("familyDob", profile.date_of_birth);
    familySetValue("familyBloodGroup", profile.blood_group);
    familySetValue("familyAllergies", profile.allergies);
    familySetValue("familyEmergencyNotes", profile.emergency_notes);

    document.getElementById("familyFormHeading").textContent =
        "Edit family profile";

    document.getElementById("familySaveButton").textContent =
        "Update profile";

    document.getElementById("familyCancelEdit").classList.remove("family-hidden");

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function familyProfilePayload() {
    return {
        full_name: familyValue("familyName"),
        relationship: familyValue("familyRelationship"),
        date_of_birth: familyValue("familyDob") || null,
        blood_group: familyValue("familyBloodGroup") || null,
        allergies: familyValue("familyAllergies") || null,
        emergency_notes: familyValue("familyEmergencyNotes") || null
    };
}

async function saveFamilyProfile(event) {
    event.preventDefault();

    const payload = familyProfilePayload();

    try {
        familyMessage("familyFormStatus", "Saving profile...");

        if (editingFamilyProfileId) {
            await api(`/api/family/profiles/${editingFamilyProfileId}`, {
                method: "PUT",
                body: payload
            });
            toast("Family profile updated successfully");
        } else {
            await api("/api/family/profiles", {
                method: "POST",
                body: payload
            });
            toast("Family profile created successfully");
        }

        familyResetForm();
        await loadOwnedFamilyProfiles();
    } catch (error) {
        familyMessage(
            "familyFormStatus",
            error.message || "Could not save the profile."
        );
    }
}

async function loadOwnedFamilyProfiles() {
    const container = document.getElementById("familyOwnedList");
    container.textContent = "Loading profiles...";

    try {
        const data = await api("/api/family/profiles");
        const profiles = data.profiles || [];

        familyById.clear();

        if (!profiles.length) {
            container.textContent = "You have not created any family profiles yet.";
            return;
        }

        container.innerHTML = profiles.map(profile => {
            familyById.set(profile.id, profile);

            return `
                <article class="family-card">
                    <h3>${familySafeText(profile.full_name)}</h3>
                    <p>${familySafeText(profile.relationship)}</p>
                    <p class="family-muted">
                        Blood group: ${familySafeText(profile.blood_group || "Not specified")}
                    </p>
                    <div class="family-actions">
                        <button class="family-button family-secondary"
                            data-family-action="view" data-id="${profile.id}">
                            View
                        </button>
                        <button class="family-button family-secondary"
                            data-family-action="edit" data-id="${profile.id}">
                            Edit
                        </button>
                        <button class="family-button family-secondary"
                            data-family-action="share" data-id="${profile.id}">
                            Manage sharing
                        </button>
                        <button class="family-button family-danger"
                            data-family-action="delete" data-id="${profile.id}">
                            Delete
                        </button>
                    </div>
                </article>
            `;
        }).join("");
    } catch (error) {
        container.textContent = error.message || "Could not load family profiles.";
    }
}

function familyRenderDetails(profile, readOnly = false) {
    const panel = document.getElementById("familyDetailsPanel");
    const container = document.getElementById("familyDetails");

    panel.classList.remove("family-hidden");

    container.innerHTML = `
        <h3>${familySafeText(profile.full_name)}</h3>
        <p><strong>Relationship:</strong> ${familySafeText(profile.relationship)}</p>
        <p><strong>Date of birth:</strong> ${familySafeText(profile.date_of_birth || "Not specified")}</p>
        <p><strong>Blood group:</strong> ${familySafeText(profile.blood_group || "Not specified")}</p>
        <p><strong>Allergies:</strong> ${familySafeText(profile.allergies || "Not specified")}</p>
        <p><strong>Emergency notes:</strong> ${familySafeText(profile.emergency_notes || "Not specified")}</p>
        ${readOnly ? '<p class="family-muted">Read-only shared profile.</p>' : ""}
    `;

    panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function viewFamilyProfile(profileId, shared = false) {
    try {
        const data = await api(`/api/family/profiles/${profileId}`);
        familyRenderDetails(data.profile, data.read_only || shared);
    } catch (error) {
        toast(error.message || "Could not open this profile.");
    }
}

async function deleteFamilyProfile(profileId) {
    if (!confirm("Delete this family profile? This cannot be undone.")) return;

    try {
        await api(`/api/family/profiles/${profileId}`, {
            method: "DELETE"
        });

        toast("Family profile deleted");
        document.getElementById("familyDetailsPanel").classList.add("family-hidden");
        document.getElementById("familySharePanel").classList.add("family-hidden");

        await loadOwnedFamilyProfiles();
    } catch (error) {
        toast(error.message || "Could not delete the profile.");
    }
}

async function openFamilyShareManager(profileId) {
    activeFamilyShareProfileId = profileId;

    document.getElementById("familySharePanel").classList.remove("family-hidden");
    familyMessage("familyShareStatus", "");

    await loadFamilyShares(profileId);

    document.getElementById("familySharePanel").scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

async function loadFamilyShares(profileId) {
    const container = document.getElementById("familyShareList");
    container.textContent = "Loading sharing permissions...";

    try {
        const data = await api(`/api/family/profiles/${profileId}/shares`);
        const shares = data.shares || [];

        if (!shares.length) {
            container.textContent = "No sharing invitations for this profile.";
            return;
        }

        container.innerHTML = shares.map(share => `
            <article class="family-card">
                <p><strong>${familySafeText(share.email || "User")}</strong></p>
                <p>Status: ${familySafeText(share.status)}</p>
                <button class="family-button family-danger"
                    data-family-action="revoke"
                    data-profile-id="${profileId}"
                    data-share-id="${share.share_id}">
                    Revoke access
                </button>
            </article>
        `).join("");
    } catch (error) {
        container.textContent = error.message || "Could not load sharing permissions.";
    }
}

async function sendFamilyInvitation(event) {
    event.preventDefault();

    if (!activeFamilyShareProfileId) return;

    const email = familyValue("familyShareEmail");

    try {
        familyMessage("familyShareStatus", "Sending invitation...");

        await api(
            `/api/family/profiles/${activeFamilyShareProfileId}/shares`,
            {
                method: "POST",
                body: { email }
            }
        );

        familySetValue("familyShareEmail", "");
        familyMessage("familyShareStatus", "Invitation created successfully.");
        await loadFamilyShares(activeFamilyShareProfileId);
    } catch (error) {
        familyMessage(
            "familyShareStatus",
            error.message || "Could not send invitation."
        );
    }
}

async function revokeFamilyShare(profileId, shareId) {
    if (!confirm("Revoke this user's access to the profile?")) return;

    try {
        await api(
            `/api/family/profiles/${profileId}/shares/${shareId}`,
            { method: "DELETE" }
        );

        toast("Sharing access revoked");
        await loadFamilyShares(profileId);
    } catch (error) {
        toast(error.message || "Could not revoke access.");
    }
}

async function loadFamilyInvitations() {
    const container = document.getElementById("familyInvitations");
    container.textContent = "Loading invitations...";

    try {
        const data = await api("/api/family/invitations");
        const invitations = data.invitations || [];

        if (!invitations.length) {
            container.textContent = "You have no pending invitations.";
            return;
        }

        container.innerHTML = invitations.map(invitation => `
            <article class="family-card">
                <p>
                    A family profile has been shared with you.
                    Profile: <strong>${familySafeText(invitation.profile.full_name)}</strong>
                </p>
                <div class="family-actions">
                    <button class="family-button family-primary"
                        data-family-action="accept"
                        data-share-id="${invitation.share_id}">
                        Accept
                    </button>
                    <button class="family-button family-danger"
                        data-family-action="reject"
                        data-share-id="${invitation.share_id}">
                        Reject
                    </button>
                </div>
            </article>
        `).join("");
    } catch (error) {
        container.textContent = error.message || "Could not load invitations.";
    }
}

async function respondToFamilyInvitation(shareId, decision) {
    try {
        await api(`/api/family/invitations/${shareId}/respond`, {
            method: "POST",
            body: { decision }
        });

        toast(`Invitation ${decision}`);
        await loadFamilyInvitations();
        await loadSharedFamilyProfiles();
    } catch (error) {
        toast(error.message || "Could not update invitation.");
    }
}

async function loadSharedFamilyProfiles() {
    const container = document.getElementById("familySharedList");
    container.textContent = "Loading shared profiles...";

    try {
        const data = await api("/api/family/shared-with-me");
        const profiles = data.profiles || [];

        if (!profiles.length) {
            container.textContent = "No family profiles have been shared with you.";
            return;
        }

        container.innerHTML = profiles.map(item => `
            <article class="family-card">
                <h3>${familySafeText(item.profile.full_name)}</h3>
                <p>${familySafeText(item.profile.relationship)}</p>
                <p class="family-muted">Shared with you — read-only access</p>
                <button class="family-button family-secondary"
                    data-family-action="view-shared"
                    data-id="${item.profile.id}">
                    View profile
                </button>
            </article>
        `).join("");
    } catch (error) {
        container.textContent = error.message || "Could not load shared profiles.";
    }
}

document.addEventListener("click", async event => {
    const button = event.target.closest("[data-family-action]");
    if (!button) return;

    const action = button.dataset.familyAction;
    const id = Number(button.dataset.id);
    const shareId = Number(button.dataset.shareId);
    const profileId = Number(button.dataset.profileId);

    if (action === "view") await viewFamilyProfile(id);
    if (action === "edit") {
        const profile = familyById.get(id);
        if (profile) familyFillForm(profile);
    }
    if (action === "delete") await deleteFamilyProfile(id);
    if (action === "share") await openFamilyShareManager(id);
    if (action === "revoke") await revokeFamilyShare(profileId, shareId);
    if (action === "accept") await respondToFamilyInvitation(shareId, "accepted");
    if (action === "reject") await respondToFamilyInvitation(shareId, "rejected");
    if (action === "view-shared") await viewFamilyProfile(id, true);
});

document.addEventListener("DOMContentLoaded", async () => {
    await shell("family");

    document.getElementById("familyProfileForm")
        .addEventListener("submit", saveFamilyProfile);

    document.getElementById("familyCancelEdit")
        .addEventListener("click", familyResetForm);

    document.getElementById("familyShareForm")
        .addEventListener("submit", sendFamilyInvitation);

    await Promise.all([
        loadOwnedFamilyProfiles(),
        loadFamilyInvitations(),
        loadSharedFamilyProfiles()
    ]);
});
