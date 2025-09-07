async function fetchWithTimeout(resource, options = {}) {
    const {timeout = 30000} = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(resource, {...options, signal: controller.signal});
        clearTimeout(id);
        return response;
    } catch (e) {
        clearTimeout(id);
        if (e.name === 'AbortError') throw new Error('Request timed out');
        throw e;
    }
}

document.getElementById('songForm').addEventListener('submit', async e => {
    e.preventDefault();
    if (!e.target.checkValidity()) {
        e.target.reportValidity();
        return;
    }
    await generateSong();
});

async function generateSong() {
    const lyrics = document.getElementById('lyrics').value.trim();
    const prompt = document.getElementById('prompt').value.trim();
    const model = document.getElementById('model').value;
    document.getElementById('loading').style.display = 'block';
    document.getElementById('loading').innerText = 'Starting song generation...';
    document.getElementById('result').innerHTML = '';
    try {
        const resp = await fetchWithTimeout('/api/song/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({lyrics, model, prompt}),
            timeout: 60000
        });
        const data = await resp.json();
        if (data.task_id) checkSongStatus(data.task_id);
        else document.getElementById('result').innerText = 'Error initiating song generation.';
    } catch (err) {
        document.getElementById('result').innerText = `Error: ${err.message}`;
    }
}

async function checkSongStatus(taskId) {
    const statusUrl = `/api/song/status/${taskId}`;
    let completed = false;
    let interval = 5000; // Start mit 5 Sekunden
    document.getElementById('loading').style.display = 'block';
    while (!completed) {
        try {
            const response = await fetchWithTimeout(statusUrl, {timeout: 60000}); // 1-minute timeout
            const data = await response.json();
            if (data.status === 'SUCCESS') {
                const resultData = data.result.result;
                document.getElementById('result').innerHTML = resultData.choices.map(choice => {
                    const durationMilliseconds = choice.duration;
                    const totalSeconds = Math.floor(durationMilliseconds / 1000);
                    const minutes = Math.floor(totalSeconds / 60);
                    const seconds = totalSeconds % 60;
                    const formattedMinutes = String(minutes).padStart(2, '0');
                    const formattedSeconds = String(seconds).padStart(2, '0');
                    const flacFilename = choice.flac_url.split('/').pop();
                    return `
                                <div class="choice-box">
                                    <p>Duration: ${formattedMinutes}:${formattedSeconds}</p>
                                    <a href="${choice.flac_url}">${flacFilename}</a>
                                </div>
                            `;
                }).join('');
                completed = true;
            } else {
                document.getElementById('loading').innerText = `Processing... Status: ${data.progress.mureka_status}`;
                interval = Math.min(interval * 1.5, 60000); // Exponentielles Backoff
                await new Promise(resolve => setTimeout(resolve, interval));
            }
        } catch (error) {
            document.getElementById('result').innerText = `Error fetching status: ${error.message}`;
            completed = true; // Schleife bei Fehler beenden
        }
    }
    document.getElementById('loading').style.display = 'none';
}
