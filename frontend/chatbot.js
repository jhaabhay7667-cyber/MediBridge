
let activeConversationId = null;
let conversations = [];

const chatLang = {
    en: "English",
    hi: "Hindi",
    bn: "Bengali"
};

function chatElement(id) {
    return document.getElementById(id);
}

function renderChatMessages(messages) {
    const container = chatElement("chat-messages");

    if (!messages || messages.length === 0) {
        container.innerHTML =
            '<p class="muted">Start by asking a health question.</p>';
        return;
    }

    container.innerHTML = messages.map(message => `
        <div class="chat-bubble ${message.role === "user" ? "user" : "assistant"}">
            ${esc(message.content)}
        </div>
    `).join("");

    container.scrollTop = container.scrollHeight;
}

function renderConversationList() {
    const container = chatElement("conversation-list");

    if (!conversations.length) {
        container.innerHTML =
            '<p class="muted">No conversations yet.</p>';
        return;
    }

    container.innerHTML = conversations.map(item => `
        <button
            type="button"
            class="conversation-item ${item.id === activeConversationId ? "active" : ""}"
            data-id="${Number(item.id)}"
        >
            ${esc(item.title)}
        </button>
    `).join("");

    container.querySelectorAll("[data-id]").forEach(button => {
        button.addEventListener("click", () => {
            openConversation(Number(button.dataset.id));
        });
    });
}

async function loadConversations() {
    conversations = await api("/api/chat/conversations");
    renderConversationList();
}

async function openConversation(id) {
    try {
        const data = await api(`/api/chat/conversations/${id}`);

        activeConversationId = data.id;
        chatElement("chat-title").textContent = data.title;

        renderChatMessages(data.messages);
        renderConversationList();
    } catch (error) {
        toast(error.message, true);
    }
}

async function createConversation() {
    try {
        const data = await api("/api/chat/conversations", {
            method: "POST",
            body: {
                title: "New conversation",
                language: chatLang[lang] || "English"
            }
        });

        activeConversationId = data.id;

        await loadConversations();
        await openConversation(data.id);
    } catch (error) {
        toast(error.message, true);
    }
}

async function sendChatMessage(message) {
    if (!activeConversationId) {
        await createConversation();
    }

    const input = chatElement("chat-input");
    const sendButton = chatElement("send-chat");
    const container = chatElement("chat-messages");

    sendButton.disabled = true;
    input.disabled = true;

    const temporary = document.createElement("div");
    temporary.className = "chat-bubble user";
    temporary.textContent = message;

    container.appendChild(temporary);

    const waiting = document.createElement("p");
    waiting.className = "muted";
    waiting.textContent = "MediBridge AI is preparing a response...";
    container.appendChild(waiting);

    container.scrollTop = container.scrollHeight;

    try {
        const data = await api(
            `/api/chat/conversations/${activeConversationId}/messages`,
            {
                method: "POST",
                body: { message }
            }
        );

        waiting.remove();

        await openConversation(activeConversationId);

        input.value = "";
        await loadConversations();

    } catch (error) {
        waiting.remove();
        toast(error.message, true);
        await openConversation(activeConversationId);
    } finally {
        sendButton.disabled = false;
        input.disabled = false;
        input.focus();
    }
}

async function getCurrentMessages() {
    const data = await api(
        `/api/chat/conversations/${activeConversationId}`
    );

    return data.messages;
}

async function initChatbot() {
    if (!await shell("chatbot")) return;

    chatElement("new-chat").addEventListener(
        "click",
        createConversation
    );

    chatElement("chat-form").addEventListener("submit", async event => {
        event.preventDefault();

        const input = chatElement("chat-input");
        const message = input.value.trim();

        if (!message) return;

        await sendChatMessage(message);
    });

    try {
        await loadConversations();

        if (conversations.length) {
            await openConversation(conversations[0].id);
        }
    } catch (error) {
        toast(error.message, true);
    }
}

document.addEventListener("DOMContentLoaded", initChatbot);
