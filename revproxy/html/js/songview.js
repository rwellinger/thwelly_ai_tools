document.addEventListener('DOMContentLoaded', () => {
    const taskSelect = document.getElementById('taskSelect');
    if (!taskSelect) return; // Fall: Select-Element existiert nicht
    fetch('/api/redis/keys')
        .then(resp => {
            if (!resp.ok) throw new Error('Network response was not ok');
            return resp.json();
        })
        .then(data => {
            data.tasks.forEach(task => {
                const opt = document.createElement('option');
                opt.value = task.task_id; // task_id als Wert der Option
                opt.textContent = task.task_id; // Anzeige im Dropdown
                taskSelect.appendChild(opt);
            });
            const viewForm = document.getElementById('viewForm');
            if (!viewForm) return;
            viewForm.addEventListener('submit', async e => {
                e.preventDefault();
                const taskId = taskSelect.value; // Aktuell gewählte Task-ID
                if (!taskId) {
                    console.error('Keine Task ID ausgewählt.');
                    return;
                }
                const loadingEl = document.getElementById('loading');
                const resultEl = document.getElementById('result');
                loadingEl.style.display = 'block';
                loadingEl.innerText = 'Fetching result…';
                resultEl.innerHTML = '';
                try {
                    const resp = await fetchWithTimeout(`/api/song/status/${taskId}`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        timeout: 60000
                    });
                    if (!resp.ok) {
                        console.error(`HTTP ${resp.status}`);
                        resultEl.innerText = `Error: HTTP ${resp.status}`;
                        return;
                    }
                    const data = await resp.json();
                    console.log('Response Data:', data);
                    if (data.status === 'SUCCESS' && data.result) {
                        resultEl.innerHTML = renderResultTask(data.result);
                    } else if (data.status === 'FAILED') {
                        resultEl.innerText = 'Job failed.';
                    } else {
                        resultEl.innerText = `Unknown status: ${data.status}`;
                    }
                } catch (err) {
                    resultEl.innerText = `Error: ${err.message}`;
                    console.error('Fetch error:', err);
                } finally {
                    loadingEl.style.display = 'none';
                }
            });
        })
        .catch(err => {
            const resultEl = document.getElementById('result');
            resultEl.innerText = `Error loading tasks: ${err.message}`;
            console.error('Fehler beim Laden der Task-IDs:', err);
        });
});

function fetchWithTimeout(resource, options = {}) {
    const { timeout = 30000 } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    return fetch(resource, { ...options, signal: controller.signal })
        .finally(() => clearTimeout(id));
}

function renderResultTask(data) {
    if (!data || !data.result || !data.result.choices || !Array.isArray(data.result.choices)) {
        return '<p>Not yet loaded...</p>';
    }
    const result = data.result;
    const id = result.id;
    const modelUsed = result.model;
    const createdAt = result.created_at;
    const finishedAt = result.finished_at;
    const createdAtMs = createdAt * 1000;
    const finishedAtMs = finishedAt * 1000;
    const durationMs = finishedAtMs - createdAtMs;
    const totalSeconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const formattedDuration = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    const infoHtml = `
        <div class="info-box">
            <p><strong>ID:</strong> ${id}</p>
            <p><strong>Model used:</strong> ${modelUsed}</p>
            <p><strong>Created:</strong> ${new Date(finishedAtMs).toUTCString()}</p>
            <p><strong>Duration:</strong> ${formattedDuration} Minutes</p>
        </div>
    `;
    const tableRows = result.choices.map(choice => {
        const song_id = choice.id;
        const durationMs = choice.duration;
        const totalSeconds = Math.floor(durationMs / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        const formattedMinutes = String(minutes).padStart(2, '0');
        const formattedSeconds = String(seconds).padStart(2, '0');
        return `
            <tr>
                <td>${song_id}</td>
                <td>${formattedMinutes}:${formattedSeconds}</td>
                <td><a href="${choice.flac_url}">FLAC-Download</a></td>
                <td><a href="${choice.url}">MP3-Download</a></td>
                <td><button onclick="generateStem('${choice.url}')">Generate</button></td>
            </tr>
        `;
    }).join('');
    return `
        ${infoHtml}
        <table class="result-table">
            <thead>
                <tr>
                    <th>Song Id</th>
                    <th>Duration</th>
                    <th>FLAC File</th>
                    <th>MP3 File</th>
                    <th>Stem</th>
                </tr>
            </thead>
            <tbody>
                ${tableRows}
            </tbody>
        </table>
    `;
}

async function generateStem(mp3Url) {
    const loadingEl = document.getElementById('loading');
    loadingEl.style.display = 'block';
    loadingEl.innerText = 'Generating stems...';

    try {
        const response = await fetch('/api/song/stems', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: mp3Url })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Stem Generation Response:', data);

        const resultEl = document.getElementById('result');
        if (data.status === 'SUCCESS' && data.result && data.result.zip_url) {
            resultEl.insertAdjacentHTML('beforeend', `
                <p><strong>Download Stems: </strong><a href="${data.result.zip_url}" target="_blank">Download</a></p>
            `);
        } else {
            resultEl.insertAdjacentHTML('beforeend', '<p>Stem generation failed or incomplete.</p>');
        }
    } catch (error) {
        const resultEl = document.getElementById('result');
        resultEl.insertAdjacentHTML('beforeend', `<p>Error generating stem: ${error.message}</p>`);
        console.error('Error generating stem:', error);
    } finally {
        loadingEl.style.display = 'none';
    }
}
