document.getElementById('promptForm').onsubmit = async function (event) {
    event.preventDefault(); // Prevent the default form submission behavior

    const prompt = document.getElementById('prompt').value;
    const size = document.getElementById('size').value; // Hole die ausgewählte Größe vom Dropdown

    // Show loading animation
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').innerHTML = ''; // Clear previous result

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({prompt: prompt, size: size}) // Sende den Prompt zusammen mit der ausgewählten Größe
        });

        if (response.ok) {
            const result = await response.json();
            // Extract the link and path
            const imageUrl = result.url;
            const savedPath = result.saved_path;
            document.getElementById('result').innerHTML = `
                        <h2>Image successfully generated!</h2>
                        <p>Saved at: ${savedPath}</p>
                        <a href="${imageUrl}" target="_blank">Click here to view the image</a>
                    `;
        } else {
            const errorData = await response.json();
            document.getElementById('result').innerText = 'Error: ' + errorData.error.message || response.statusText;
        }
    } catch (error) {
        document.getElementById('result').innerText = 'Network error: ' + error.message;
    } finally {
        // Hide loading animation
        document.getElementById('loading').style.display = 'none';
    }
};
