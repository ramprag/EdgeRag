<script>
let apiKey = '';
const API_BASE = 'http://localhost:8000';

// Load API key from localStorage
window.onload = function() {
    const saved = localStorage.getItem('apiKey');
    if (saved) {
        apiKey = saved;
        document.getElementById('apiKey').value = saved;
        document.getElementById('apiKeyStatus').textContent = '✓ Saved';
        document.getElementById('apiKeyStatus').style.color = 'green';
    }
};

function saveApiKey() {
    apiKey = document.getElementById('apiKey').value;
    localStorage.setItem('apiKey', apiKey);
    document.getElementById('apiKeyStatus').textContent = '✓ Saved';
    document.getElementById('apiKeyStatus').style.color = 'green';
}

function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(tabName + 'Tab').classList.add('active');
}

async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;

    if (files.length === 0) {
        showStatus('uploadStatus', 'Please select files to upload', 'error');
        return;
    }

    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = '<div class="loading"></div> Uploading...';

    const uploadedDiv = document.getElementById('uploadedFiles');
    uploadedDiv.innerHTML = '';

    for (let file of files) {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                headers: { 'X-API-Key': apiKey },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            uploadedDiv.innerHTML += `<div class="status-success">✓ ${file.name} → ${result.doc_id} (${result.pages} pages)</div>`;
        } catch (error) {
            uploadedDiv.innerHTML += `<div class="status-error">✗ ${file.name}: ${error.message}</div>`;
        }
    }

    statusDiv.innerHTML = '';
    fileInput.value = '';
}

async function buildIndex() {
    const statusDiv = document.getElementById('indexStatus');
    statusDiv.innerHTML = '<div class="loading"></div> Building index... This may take a few minutes.';

    try {
        const response = await fetch(`${API_BASE}/build-index`, {
            method: 'POST',
            headers: { 'X-API-Key': apiKey }
        });

        if (!response.ok) {
            throw new Error(`Build failed: ${response.statusText}`);
        }

        const result = await response.json();
        statusDiv.innerHTML = `
            <div class="status-success">
                <h3>✓ Index Built Successfully</h3>
                <p>Documents indexed: ${result.documents_indexed}</p>
                <p>Total chunks: ${result.total_chunks}</p>
                <p>Time: ${result.embedding_time_seconds.toFixed(2)}s</p>
                <p>Index size: ${result.index_size_mb.toFixed(2)} MB</p>
            </div>
        `;
    } catch (error) {
        statusDiv.innerHTML = `<div class="status-error">Error: ${error.message}</div>`;
    }
}

async function submitQuery() {
    const query = document.getElementById('queryInput').value.trim();
    const topK = parseInt(document.getElementById('topK').value);

    if (!query) {
        showStatus('queryResults', 'Please enter a question', 'error');
        return;
    }

    const resultsDiv = document.getElementById('queryResults');
    resultsDiv.innerHTML = '<div class="loading"></div> Generating answer...';

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'X-API-Key': apiKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query, top_k: topK })
        });

        if (!response.ok) {
            throw new Error(`Query failed: ${response.statusText}`);
        }

        const result = await response.json();
        displayQueryResults(result);
    } catch (error) {
        resultsDiv.innerHTML = `<div class="status-error">Error: ${error.message}</div>`;
    }
}

function displayQueryResults(result) {
    const resultsDiv = document.getElementById('queryResults');

    let html = `
        <div class="answer-box">
            <h3>Answer</h3>
            <p>${result.answer}</p>
            <div class="stats">
                <span>⏱️ Total: ${result.latency_ms}ms</span>
                <span>🔍 Retrieval: ${result.retrieval_time_ms}ms</span>
                <span>🤖 Generation: ${result.generation_time_ms}ms</span>
            </div>
        </div>
    `;

    if (result.sources && result.sources.length > 0) {
        html += '<div class="sources"><h3>Sources</h3>';

        result.sources.forEach((source, idx) => {
            html += `
                <div class="source-item">
                    <strong>Source ${idx + 1}</strong>: ${source.filename} (Page ${source.page})
                    <br><small>Score: ${source.score.toFixed(3)}</small>
                    <p style="margin-top: 10px; color: #666;">${source.text}</p>
                </div>
            `;
        });

        html += '</div>';
    }

    resultsDiv.innerHTML = html;
}

async function loadDocuments() {
    const docsDiv = document.getElementById('documentsList');
    docsDiv.innerHTML = '<div class="loading"></div> Loading documents...';

    try {
        const response = await fetch(`${API_BASE}/docs-list`, {
            headers: { 'X-API-Key': apiKey }
        });

        if (!response.ok) {
            throw new Error(`Failed to load documents: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.total === 0) {
            docsDiv.innerHTML = '<p>No documents uploaded yet.</p>';
            return;
        }

        let html = `<p><strong>Total documents: ${result.total}</strong></p>`;

        result.documents.forEach(doc => {
            html += `
                <div class="document-item">
                    <strong>${doc.filename}</strong>
                    <br>ID: ${doc.doc_id}
                    <br>Pages: ${doc.pages}
                    <br>Chunks: ${doc.chunks ? doc.chunks.length : 0}
                </div>
            `;
        });

        docsDiv.innerHTML = html;
    } catch (error) {
        docsDiv.innerHTML = `<div class="status-error">Error: ${error.message}</div>`;
    }
}

function showStatus(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="status-${type}">${message}</div>`;
}
</script>