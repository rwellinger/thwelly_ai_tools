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
            const response = await fetchWithTimeout(statusUrl, {timeout: 60000});
            const data = await response.json();

            if (data.status === 'SUCCESS') {
                const resultData = data.result.result;

                const id = resultData.id;
                const modelUsed = resultData.model;

                // Generiere die HTML-Struktur
                const infoHtml = `
                    <div class="info-box">
                        <strong>ID:</strong> ${id}<br>
                        <strong>Model used:</strong> ${modelUsed}
                    </div>
                    <table class="result-table">
                        <thead>
                            <tr>
                                <th>Song Id</th>
                                <th>Duration</th>
                                <th>FLAC File</th>
                                <th>MP3 File</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${resultData.choices.map(choice => {
                                const song_id = choice.id
                                const durationMilliseconds = choice.duration;
                                const totalSeconds = Math.floor(durationMilliseconds / 1000);
                                const minutes = Math.floor(totalSeconds / 60);
                                const seconds = totalSeconds % 60;
                                const formattedMinutes = String(minutes).padStart(2, '0');
                                const formattedSeconds = String(seconds).padStart(2, '0');
                                const flacFilename = choice.flac_url.split('/').pop();
                                const mp3Filename = choice.url.split('/').pop()
                                return `
                                    <tr>
                                        <td>${song_id}</td>
                                        <td>${formattedMinutes}:${formattedSeconds}</td>
                                        <td><a href="${choice.flac_url}">${flacFilename}</a></td>
                                        <td><a href="${choice.url}">${mp3Filename}</a></td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                `;

                document.getElementById('result').innerHTML = infoHtml;
                completed = true;
            } else {
                const murekaStatus = data.progress.mureka_status || "Initialize";
                document.getElementById('loading').innerText = `Processing (${murekaStatus}) ... Please wait until finished.`;
                interval = Math.min(interval * 1.5, 60000);
                await new Promise(resolve => setTimeout(resolve, interval));
            }
        } catch (error) {
            document.getElementById('result').innerText = `Error fetching status: ${error.message}`;
            completed = true;
        }
    }
    document.getElementById('loading').style.display = 'none';
}
