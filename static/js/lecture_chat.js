document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");

    const sendButton = document.getElementById("send-button");
    const nextTopicButton = document.getElementById("next-topic");
    const endLectureButton = document.getElementById("end-lecture");

    const chatUrl = chatForm.dataset.chatUrl;
    const nextTopicUrl = chatForm.dataset.nextTopicUrl;
    const endLectureUrl = chatForm.dataset.endLectureUrl;

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let isBusy = false;

    function setBusy(state) {
        isBusy = state;
        sendButton.disabled = state;
        nextTopicButton.disabled = state;
        endLectureButton.disabled = state;
    }

    function appendMessage(sender, text="", isLoading=false) {
        const wrapper = document.createElement("div");
        wrapper.classList.add("mb-3", "d-flex");

        let content = text;
        if (isLoading) content ="...";

        if (sender === "AI") {
            wrapper.classList.add("justify-content-start");
            wrapper.innerHTML = `
                <div class="d-flex align-items-start">
                    <span class="badge bg-success me-2">AI</span>
                    <div class="bg-white border p-2 rounded message">
                        ${content}
                    </div>
                </div>
            `;
        } else {
            wrapper.classList.add("justify-content-end");
            wrapper.innerHTML = `
                <div class="d-flex align-items-start">
                    <span class="badge bg-primary me-2">You</span>
                    <div class="bg-light border p-2 rounded message">
                        ${content}
                    </div>
                </div>
            `;
        }
        chatBox.appendChild(wrapper)
        chatBox.scrollTop = chatBox.scrollHeight;
        return wrapper.querySelector(".message")
    }

    // Send (chat)
    chatForm.addEventListener("submit", function (e) {
        e.preventDefault();
        if (isBusy) return;

        const userMessage = userInput.value.trim();
        if (!userMessage) return;

        appendMessage("You", userMessage);
        userInput.value = ""

        const aiContainer = appendMessage("AI", "", true);
        setBusy(true);

        fetch(chatUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": csrfToken,
            },
            body: new URLSearchParams({ user_input: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            const html = data.ai_response;
            aiContainer.innerHTML = html;
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(err => {
            aiContainer.innerHTML = "An error has occurred";
            console.error("Error: ", err);
        })
        .finally(() => {
            setBusy(false);
        });
    });

    // Next Topic
    nextTopicButton.addEventListener("click", function () {
        if (isBusy) return;

        setBusy(true);

        fetch(nextTopicUrl, {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                throw new Error("No reidirect URL");
            }
        })
        .catch(err => {
            console.error(err);
            alert("Failed to proceed to next topic.");
            setBusy(false);
        });
    });

    // End Lecture
    endLectureButton.addEventListener("click", function () {
        if (isBusy) return;

        if (!confirm("End the lecture and generate the report?"))

        setBusy(true);

        fetch(endLectureUrl, {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                throw new Error("No redirect URL");
            }
        })
        .catch(err => {
            console.error(err);
            alert("Failed to end the lecture.");
            setBusy(false);
        });
    });
});
