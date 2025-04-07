// Check if Annyang is available
if (annyang) {
    // Automatically detect the language based on the user's browser settings
    let detectedLanguage = navigator.language || 'en-US';  // Default to 'en-US' if no language detected

    // Set the language for speech recognition
    annyang.setLanguage(detectedLanguage);

    const voiceButton = document.getElementById('voiceBtn');
    const queryField = document.getElementById('query');
    const sendButton = document.getElementById('sendBtn');
    const messagesContainer = document.getElementById("messagesContainer");

    let inactivityTimer;
    const silenceDelay = 3000; // 3 seconds delay after speech stops

    // Define the commands for Annyang
    const commands = {
        '*query': function(query) {
            // While the user is speaking, update the query field with the live transcription
            queryField.value = query;  // Display the current transcription in the input field

            // Reset inactivity timer each time speech is recognized
            clearTimeout(inactivityTimer);

            // Set a timer to process the query after 3 seconds of no speech
            inactivityTimer = setTimeout(function() {
                const trimmedQuery = queryField.value.trim();
                if (trimmedQuery) {
                    sendQueryToServer(trimmedQuery);
                }
            }, silenceDelay);
        }
    };

    // Add the commands to Annyang
    annyang.addCommands(commands);

    // Start/Stop voice recognition when the voice button is clicked
    voiceButton.addEventListener('click', () => {
        if (annyang.isListening()) {
            annyang.abort();  // Stop recognition
            voiceButton.querySelector('img').classList.remove('mic-active');  // Remove the active state class
        } else {
            annyang.start({ continuous: true, autoRestart: false });  // Start listening continuously
            voiceButton.querySelector('img').classList.add('mic-active');  // Add the active state class
        }
    });

    // Send Query to Server
    async function sendQueryToServer(query) {
        const queryDiv = document.createElement('div');
        queryDiv.classList.add('query-message');
        queryDiv.innerHTML = query;  // Set the user query

        const loadingSpinner = document.createElement('div');
        loadingSpinner.classList.add('loading-spinner');
        
        messagesContainer.appendChild(queryDiv);
        messagesContainer.appendChild(loadingSpinner);

        // Clear the input field
        queryField.value = "";
        messagesContainer.scrollTop = messagesContainer.scrollHeight;  // Scroll to the bottom

        const data = { query: query };

        try {
            const response = await fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            if (response.ok) {
                const result = await response.json();
                loadingSpinner.remove();

                const responseDiv = document.createElement('div');
                responseDiv.classList.add('response');
                responseDiv.innerHTML = result.response.replace(/\n/g, "<br>");

                messagesContainer.appendChild(responseDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;  // Scroll to the bottom after response

                // After processing the query, stop listening and reset the mic button
                annyang.abort();  // Stop recognition
                voiceButton.querySelector('img').classList.remove('mic-active');  // Remove active state class

            } else {
                const errorResult = await response.json();
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('error');
                errorDiv.innerText = "Error: " + JSON.stringify(errorResult, null, 2);
                messagesContainer.appendChild(errorDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;  // Scroll to the bottom
            }
        } catch (error) {
            console.error("Error:", error);
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('error');
            errorDiv.innerHTML = "An error occurred while processing your query. Please try again later.";
            messagesContainer.appendChild(errorDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;  // Scroll to the bottom
        }
    }

    // Show an error if the query box is empty when clicking the Send button
    sendButton.addEventListener('click', function() {
        const query = queryField.value.trim();

        if (query === "") {
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('error');
            errorDiv.innerHTML = "Error: Please enter a query before sending.";
            messagesContainer.appendChild(errorDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;  // Scroll to the bottom to show the error message
        } else {
            sendQueryToServer(query);
        }
    });

    // Allow the "Enter" key to trigger the Send button
    document.getElementById("query").addEventListener("keydown", function(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            const query = queryField.value.trim();

            if (query === "") {
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('error');
                errorDiv.innerHTML = "Error: Please enter a query before sending.";
                messagesContainer.appendChild(errorDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;  // Scroll to the bottom to show the error message
            } else {
                sendQueryToServer(query);
            }

            event.preventDefault();
        }
    });
} else {
    alert("Speech recognition is not supported in this browser.");
}
