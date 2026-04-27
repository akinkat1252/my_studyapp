document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");

    const submitButton = document.getElementById("submit");
    const nextButton = document.getElementById("next");
    const endButton = document.getElementById("end");

    const sendURL = chatForm.dataset.sendUrl;
    const nextURL = chatForm.dataset.nextUrl;
    const endURL = chatForm.dataset.endUrl;

    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let isBusy = false;

    
    function setBusy(state) {
        isBusy = state;
        submitButton.disabled = state;
        nextButton.disabled = state;
        endButton.disabled = state;
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
            if (!data.lecture_content) {
                throw new Error("lecture_content is missing")
            }
            aiContainer.innerHTML = data.lecture_content;
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
});