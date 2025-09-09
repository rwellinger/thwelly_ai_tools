/**
 * Fetch helper – aborts after `timeout` ms
 */
function fetchWithTimeout(resource, options = {}) {
    const { timeout = 30000 } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    return fetch(resource, { ...options, signal: controller.signal })
        .finally(() => clearTimeout(id));
}

/**
 * Render result table (identical to generator page)
 */
function renderResult(result) {
    const id = result.id;
    const modelUsed = result.model;

    const infoHtml = `
        <div class="info-box">
            <strong>ID:</strong> ${id}<br>
            <strong>Model used:</strong> ${modelUsed}
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
        const flacFilename = choice.flac_url.split('/').pop();
        const mp3Filename = choice.url.split('/').pop();

        return `
            <tr>
                <td>${song_id}</td>
                <td>${formattedMinutes}:${formattedSeconds}</td>
                <td><a href="${choice.flac_url}">${flacFilename}</a></td>
                <td><a href="${choice.url}">${mp3Filename}</a></td>
            </tr>
        `;
    }).join('');

    const tableHtml = `
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
                ${tableRows}
            </tbody>
        </table>
    `;

    return infoHtml + tableHtml;
}

/**
 * Submit handler
 */
document.getElementById('viewForm').addEventListener('submit', async e => {
    e.preventDefault();
    const jobId = document.getElementById('jobId').value.trim();
    if (!jobId) return;

    const loadingEl = document.getElementById('loading');
    const resultEl = document.getElementById('result');

    loadingEl.style.display = 'block';
    loadingEl.innerText = 'Fetching result…';
    resultEl.innerHTML = '';

    try {
        const resp = await fetchWithTimeout(`/api/song/query/${jobId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            timeout: 60000
        });

        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }

        const data = await resp.json();

        // API returns status in root and detailed result inside data.result
        if (data.status === 'SUCCESS' && data.result) {
            resultEl.innerHTML = renderResult(data.result);
        } else if (data.status === 'FAILED') {
            resultEl.innerText = 'Job failed.';
        } else {
            resultEl.innerText = `Unknown status: ${data.status}`;
        }
    } catch (err) {
        resultEl.innerText = `Error: ${err.message}`;
    } finally {
        loadingEl.style.display = 'none';
    }
});