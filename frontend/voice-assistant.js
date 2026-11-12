
let voiceConversationId = null;
let voiceConversations = [];
let lastAssistantReply = "";
let recognition = null;
let isMuted = false;
let isSendingVoiceMessage = false;

const voiceLanguages = {
  en: {
    name: "English",
    recognition: "en-IN",
    speech: "en-IN"
  },
  hi: {
    name: "Hindi",
    recognition: "hi-IN",
    speech: "hi-IN"
  },
  bn: {
    name: "Bengali",
    recognition: "bn-IN",
    speech: "bn-IN"
  }
};

function voiceElement(id) {
  return document.getElementById(id);
}

function selectedVoiceLanguage() {
  return voiceLanguages[voiceElement("voice-language").value] ||
    voiceLanguages.en;
}

function selectedChatLanguage() {
  return selectedVoiceLanguage().name;
}

function setVoiceStatus(message) {
  voiceElement("voice-status").textContent = message;
}

function stopVoiceOutput() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}

function speakAssistant(text) {
  if (isMuted || !("speechSynthesis" in window) || !text) {
    return;
  }

  stopVoiceOutput();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = selectedVoiceLanguage().speech;
  utterance.rate = 0.95;
  utterance.pitch = 1;

  utterance.onstart = () => {
    setVoiceStatus("MediBridge is speaking...");
  };

  utterance.onend = () => {
    setVoiceStatus("Voice assistant is ready.");
  };

  utterance.onerror = () => {
    setVoiceStatus("Voice playback is unavailable. You can read the answer.");
  };

  window.speechSynthesis.speak(utterance);
}

function renderVoiceMessages(messages) {
  const container = voiceElement("voice-messages");

  if (!messages || !messages.length) {
    container.innerHTML =
      '<p class="muted">Start by asking a health question.</p>';
    return;
  }

  container.innerHTML = messages.map(message => `
    <div class="voice-message ${message.role === "user" ? "user" : "assistant"}">
      <b>${message.role === "user" ? "You" : "MediBridge AI"}</b>
      <p>${esc(message.content)}</p>
    </div>
  `).join("");

  container.scrollTop = container.scrollHeight;

  const assistantMessages = messages.filter(
    message => message.role === "assistant"
  );

  if (assistantMessages.length) {
    lastAssistantReply =
      assistantMessages[assistantMessages.length - 1].content;
  }
}

function renderVoiceConversationList() {
  const select = voiceElement("voice-list");

  select.innerHTML =
    '<option value="">Select a conversation</option>' +
    voiceConversations.map(item => `
      <option value="${Number(item.id)}"
        ${item.id === voiceConversationId ? "selected" : ""}>
        ${esc(item.title)}
      </option>
    `).join("");
}

async function loadVoiceConversations() {
  voiceConversations = await api("/api/chat/conversations");
  renderVoiceConversationList();
}

async function openVoiceConversation(id) {
  try {
    const data = await api(`/api/chat/conversations/${id}`);

    voiceConversationId = data.id;

    voiceElement("voice-chat-title").textContent = data.title;
    voiceElement("voice-language").value =
      data.language === "Hindi" ? "hi" :
      data.language === "Bengali" ? "bn" : "en";

    lastAssistantReply = "";
    renderVoiceMessages(data.messages);
    renderVoiceConversationList();

    stopVoiceOutput();
    setVoiceStatus("Conversation loaded.");
  } catch (error) {
    toast(error.message, true);
  }
}

async function createVoiceConversation() {
  try {
    stopVoiceOutput();

    const data = await api("/api/chat/conversations", {
      method: "POST",
      body: {
        title: "New conversation",
        language: selectedChatLanguage()
      }
    });

    voiceConversationId = data.id;
    lastAssistantReply = "";

    await loadVoiceConversations();
    await openVoiceConversation(data.id);

    voiceElement("voice-chat-input").focus();
    setVoiceStatus("New conversation created.");
  } catch (error) {
    toast(error.message, true);
  }
}

async function sendVoiceChatMessage(message) {
  const cleanMessage = String(message || "").trim();

  if (!cleanMessage || isSendingVoiceMessage) {
    return;
  }

  isSendingVoiceMessage = true;

  const input = voiceElement("voice-chat-input");
  const sendButton = voiceElement("voice-send");
  const container = voiceElement("voice-messages");

  sendButton.disabled = true;
  input.disabled = true;

  stopVoiceOutput();

  try {
    if (!voiceConversationId) {
      await createVoiceConversation();
    }

    const temporary = document.createElement("div");
    temporary.className = "voice-message user";

    const heading = document.createElement("b");
    heading.textContent = "You";

    const paragraph = document.createElement("p");
    paragraph.textContent = cleanMessage;

    temporary.append(heading, paragraph);
    container.appendChild(temporary);

    const waiting = document.createElement("p");
    waiting.className = "muted";
    waiting.textContent = "MediBridge AI is preparing a response...";

    container.appendChild(waiting);
    container.scrollTop = container.scrollHeight;

    const conversationId = voiceConversationId;

    await api(
      `/api/chat/conversations/${conversationId}/messages`,
      {
        method: "POST",
        body: { message: cleanMessage }
      }
    );

    waiting.remove();

    await openVoiceConversation(conversationId);
    await loadVoiceConversations();

    input.value = "";

    if (lastAssistantReply) {
      speakAssistant(lastAssistantReply);
    }

    setVoiceStatus("Answer received.");
  } catch (error) {
    toast(error.message, true);
    setVoiceStatus("Message could not be sent. Please try again.");

    if (voiceConversationId) {
      try {
        await openVoiceConversation(voiceConversationId);
      } catch (_) {
        // Keep the existing screen if history cannot be refreshed.
      }
    }
  } finally {
    isSendingVoiceMessage = false;
    sendButton.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

function setupSpeechRecognition() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    setVoiceStatus(
      "Speech recognition is not supported by this browser. Please type your question."
    );
    voiceElement("voice-start").disabled = true;
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {
    voiceElement("voice-start").disabled = true;
    voiceElement("voice-stop").disabled = false;
    setVoiceStatus("Listening... Speak your health question.");
  };

  recognition.onresult = event => {
    let transcript = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }

    voiceElement("voice-chat-input").value = transcript.trim();
  };

  recognition.onerror = event => {
    const messages = {
      "not-allowed": "Microphone permission denied. Allow microphone access in your browser.",
      "no-speech": "No speech detected. Please try again.",
      "audio-capture": "No microphone was found.",
      "network": "Speech recognition network error. Please try again.",
      "service-not-allowed": "Speech recognition service is unavailable."
    };

    setVoiceStatus(
      messages[event.error] || "Microphone error: " + event.error
    );
  };

  recognition.onend = () => {
    voiceElement("voice-start").disabled = false;
    voiceElement("voice-stop").disabled = true;

    if (voiceElement("voice-chat-input").value.trim()) {
      setVoiceStatus(
        "Speech captured. Review your question and press Send message."
      );
    } else {
      setVoiceStatus("Voice assistant is ready.");
    }
  };
}

function startVoiceRecognition() {
  if (!recognition) {
    toast("Speech recognition is not available in this browser.", true);
    return;
  }

  stopVoiceOutput();

  recognition.lang = selectedVoiceLanguage().recognition;

  try {
    recognition.start();
  } catch (error) {
    setVoiceStatus("Microphone is already active. Please try again.");
  }
}

function stopVoiceRecognition() {
  if (recognition) {
    recognition.stop();
  }
}

async function initVoiceAssistant() {
  if (!await shell("voice")) return;

  voiceElement("voice-chat-form").addEventListener(
    "submit",
    async event => {
      event.preventDefault();

      const message = voiceElement("voice-chat-input").value.trim();

      if (message) {
        await sendVoiceChatMessage(message);
      }
    }
  );

  voiceElement("new-voice-chat").addEventListener(
    "click",
    createVoiceConversation
  );

  voiceElement("voice-list").addEventListener("change", event => {
    const id = Number(event.target.value);

    if (id) {
      openVoiceConversation(id);
    }
  });

  voiceElement("voice-start").addEventListener(
    "click",
    startVoiceRecognition
  );

  voiceElement("voice-stop").addEventListener(
    "click",
    stopVoiceRecognition
  );

  voiceElement("voice-read").addEventListener("click", () => {
    if (!lastAssistantReply) {
      toast("There is no AI response to read yet.", true);
      return;
    }

    speakAssistant(lastAssistantReply);
  });

  voiceElement("voice-mute").addEventListener("click", () => {
    isMuted = !isMuted;

    if (isMuted) {
      stopVoiceOutput();
    }

    voiceElement("voice-mute").textContent =
      isMuted ? "Unmute voice" : "Mute voice";

    setVoiceStatus(
      isMuted ? "Voice output muted." : "Voice output enabled."
    );
  });

  voiceElement("voice-clear").addEventListener(
    "click",
    stopVoiceOutput
  );

  voiceElement("voice-language").addEventListener("change", () => {
    stopVoiceOutput();

    setVoiceStatus(
      "Language selected. New conversations will use " +
      selectedChatLanguage() + "."
    );
  });

  setupSpeechRecognition();

  try {
    await loadVoiceConversations();

    if (voiceConversations.length) {
      await openVoiceConversation(voiceConversations[0].id);
    }
  } catch (error) {
    toast(error.message, true);
  }
}

document.addEventListener("DOMContentLoaded", initVoiceAssistant);
