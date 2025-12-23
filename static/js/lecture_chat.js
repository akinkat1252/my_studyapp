document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const endLectureButton = document.getElementById("end-lecture");
    const chatUrl = chatForm.dataset.url;
    const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

    function appendMessage(sender, text="", isLoading=false) {
        const wrapper = document.createElement("div");
        wrapper.classList.add("mb-3", "d-flex");

        let content = text;
        if (isLoading) content ="...";

        if (sender === "AI") {
            wrapper.classList.add("justify-content-start");
            wrapper.innerHTML = `
                <div class="text-start d-flex flex-column">
                    <span class="badge bg-success mb-1">AI</span>
                    <div class="d-inline-block bg-white border p-2 rounded">${content}</div>
                </div>
            `;
        } else {
            wrapper.classList.add("justify-content-end");
            wrapper.innerHTML = `
                <div class="text-end d-flex flex-column">
                    <span class="badge bg-primary mb-1">You</span>
                    <div class="d-inline-block bg-light border p-2 rounded">${content}</div>
                </div>
            `;
        }
        chatBox.appendChild(wrapper)
        chatBox.scrollTop = chatBox.scrollHeight;
        return wrapper.querySelector(".message")
    }

    chatForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const userMessage = userInput.value.trim();

        if (!userMessage) {
            return;
        }

        appendMessage("You", userMessage);
        userInput.value = ""

        const aiContainer = appendMessage("AI", "", true);

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
        });
    });

    endLectureButton.addEventListener("click", function () {
        fetch(chatUrl, {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: new URLSearchParams({ user_input: "End"})
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            }
        });
    });
});
