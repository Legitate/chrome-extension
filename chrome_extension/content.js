// content.js

const UI_CONTAINER_ID = 'altrosyn-infographic-panel';

// Helper to extract video ID
function extractVideoId(url) {
    try {
        const u = new URL(url);
        if (u.hostname.includes('youtube.com')) {
            return u.searchParams.get('v');
        } else if (u.hostname.includes('youtu.be')) {
            return u.pathname.slice(1);
        }
    } catch (e) { }
    return null;
}

// run immediately
detectAndSendUrl();

// Also listen for URL changes (SPA navigation on YouTube often doesn't reload the page)
let lastUrl = location.href;
new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
        lastUrl = url;
        detectAndSendUrl();
    }
}).observe(document, { subtree: true, childList: true });

function detectAndSendUrl() {
    const url = window.location.href;
    // Always check state to ensure Auth UI shows up if needed
    checkAuthState();

    if (isYouTubeVideo(url)) {
        console.log('YouTube video detected:', url);
        chrome.runtime.sendMessage({ type: 'YOUTUBE_ACTIVE', url: url });
    }
}

function isYouTubeVideo(url) {
    return url.includes('youtube.com/watch') || url.includes('youtu.be/');
}

function checkAuthState() {
    chrome.storage.local.get(['auth'], (result) => {
        if (result.auth && result.auth.cookie && result.auth.at_token) {
            // Auth is good. Only show UI if we are on a video page.
            if (isYouTubeVideo(window.location.href)) {
                restoreStateForCurrentVideo();
            } else {
                updateUI('IDLE');
            }
        } else {
            // Auth is missing. Show the Connect UI on ALL YouTube pages so user can set it up.
            updateUI('AUTH_REQUIRED');
        }
    });
}

// --- UI INJECTION & LINK IMPLEMENTATION ---

// --- UI INJECTION & LINK IMPLEMENTATION ---

function injectStyles() {
    if (document.getElementById('altrosyn-styles')) return;
    const style = document.createElement('style');
    style.id = 'altrosyn-styles';
    style.textContent = `
        #${UI_CONTAINER_ID} {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 320px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
            border-radius: 16px;
            padding: 20px;
            z-index: 2147483647;
            font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
            display: none;
            flex-direction: column;
            gap: 16px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            color: #202124;
        }
        #${UI_CONTAINER_ID}.minimized {
            width: 48px;
            height: 48px;
            padding: 0;
            border-radius: 24px;
            cursor: pointer;
            overflow: hidden;
            background: #ffffff;
            justify-content: center;
            align-items: center;
        }
        #${UI_CONTAINER_ID}.minimized:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        }
        #${UI_CONTAINER_ID} * {
            box-sizing: border-box;
        }
        /* Header */
        .altrosyn-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .altrosyn-title {
            font-size: 16px;
            font-weight: 600;
            color: #202124;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .altrosyn-title svg {
            width: 20px;
            height: 20px;
            color: #065fd4;
        }
        .altrosyn-min-btn {
            background: transparent;
            border: none;
            cursor: pointer;
            padding: 4px;
            color: #5f6368;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        .altrosyn-min-btn:hover {
            background: rgba(0,0,0,0.05);
            color: #202124;
        }
        
        /* Inputs */
        .altrosyn-input-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .altrosyn-label {
            font-size: 12px;
            color: #5f6368;
            font-weight: 500;
        }
        .altrosyn-textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #dadce0;
            border-radius: 8px;
            font-size: 13px;
            font-family: 'Roboto Mono', monospace;
            resize: vertical;
            min-height: 48px;
            outline: none;
            background: #f8f9fa;
            transition: border-color 0.2s, background 0.2s;
        }
        .altrosyn-textarea:focus {
            border-color: #065fd4;
            background: #fff;
        }

        /* Buttons */
        .altrosyn-btn {
            width: 100%;
            padding: 10px 16px;
            background-color: #065fd4;
            color: white;
            border: none;
            border-radius: 18px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background-color 0.2s, transform 0.1s, opacity 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .altrosyn-btn:hover {
            background-color: #0556bf;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        .altrosyn-btn:active {
            transform: scale(0.98);
        }
        .altrosyn-btn:disabled {
            background-color: #dadce0;
            color: #80868b;
            cursor: not-allowed;
            transform: none;
        }
        .altrosyn-btn-secondary {
            background-color: transparent;
            color: #065fd4;
            border: 1px solid #dadce0;
        }
        .altrosyn-btn-secondary:hover {
            background-color: #f1f3f4;
            box-shadow: none;
            border-color: #dadce0;
        }

        /* Status & Content */
        .altrosyn-status {
            font-size: 14px;
            text-align: center;
            color: #5f6368;
            margin: 4px 0;
            font-weight: 500;
        }
        .altrosyn-img-preview {
            width: 100%;
            height: auto;
            border-radius: 8px;
            border: 1px solid #e8eaed;
            cursor: pointer;
            transition: transform 0.2s;
            display: none;
        }
        .altrosyn-img-preview:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .altrosyn-link {
            display: block;
            text-align: center;
            color: #065fd4;
            text-decoration: none;
            padding: 8px;
            font-size: 13px;
            font-weight: 500;
            border-radius: 4px;
        }
        .altrosyn-link:hover {
            background: #f1f3f4;
        }
        
        /* Minimized State Icon */
        .minimized-icon {
            display: none;
            width: 24px;
            height: 24px;
            color: #065fd4;
        }
        #${UI_CONTAINER_ID}.minimized .minimized-icon {
            display: block;
        }
        #${UI_CONTAINER_ID}.minimized > *:not(.minimized-icon) {
            display: none !important;
        }
    `;
    document.head.appendChild(style);
}

function getOrCreateUI() {
    injectStyles();
    let container = document.getElementById(UI_CONTAINER_ID);

    if (!container) {
        container = document.createElement('div');
        container.id = UI_CONTAINER_ID;
        document.body.appendChild(container);

        // --- Structure ---

        // Minimized Icon (Visible only when minimized)
        const minIcon = document.createElement('div');
        minIcon.className = 'minimized-icon';
        minIcon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"></path><path d="M12 12 2.1 11.9"></path><path d="M12 12V2.1"></path></svg>`; // Pie Chart-ish icon
        container.appendChild(minIcon);

        // Restore from minimized click
        container.onclick = (e) => {
            if (container.classList.contains('minimized')) {
                container.classList.remove('minimized');
                e.stopPropagation();
            }
        };

        // Header
        const header = document.createElement('div');
        header.className = 'altrosyn-header';
        header.innerHTML = `
            <div class="altrosyn-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                Notebook Gen
            </div>
            <button class="altrosyn-min-btn" title="Minimize">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            </button>
        `;
        container.appendChild(header);

        // Minimize Handler
        header.querySelector('.altrosyn-min-btn').onclick = (e) => {
            e.stopPropagation();
            container.classList.add('minimized');
        };

        // Status
        const statusEl = document.createElement('div');
        statusEl.id = UI_CONTAINER_ID + '-status';
        statusEl.className = 'altrosyn-status';
        container.appendChild(statusEl);

        // Auth Container
        const authContainer = document.createElement('div');
        authContainer.id = UI_CONTAINER_ID + '-auth-container';
        authContainer.style.display = 'none';
        authContainer.style.flexDirection = 'column';
        authContainer.style.gap = '12px';
        container.appendChild(authContainer);

        // Auth Inputs
        const cookieGroup = document.createElement('div');
        cookieGroup.className = 'altrosyn-input-group';
        cookieGroup.innerHTML = `
            <span class="altrosyn-label">NotebookLM Cookie</span>
            <textarea id="${UI_CONTAINER_ID}-cookie-input" class="altrosyn-textarea" placeholder="Paste full cookie string"></textarea>
        `;
        authContainer.appendChild(cookieGroup);

        const tokenGroup = document.createElement('div');
        tokenGroup.className = 'altrosyn-input-group';
        tokenGroup.innerHTML = `
            <span class="altrosyn-label">AT Token</span>
            <textarea id="${UI_CONTAINER_ID}-token-input" class="altrosyn-textarea" placeholder="Paste token"></textarea>
        `;
        authContainer.appendChild(tokenGroup);

        const saveBtn = document.createElement('button');
        saveBtn.className = 'altrosyn-btn';
        saveBtn.textContent = 'Connect & Save';
        saveBtn.onclick = () => {
            const cookieInput = document.getElementById(`${UI_CONTAINER_ID}-cookie-input`);
            const tokenInput = document.getElementById(`${UI_CONTAINER_ID}-token-input`);

            let cookie = cookieInput.value.trim();
            if (cookie.toLowerCase().startsWith('cookie:')) cookie = cookie.substring(7).trim();
            if ((cookie.startsWith('"') && cookie.endsWith('"')) || (cookie.startsWith("'") && cookie.endsWith("'"))) cookie = cookie.slice(1, -1);

            let at_token = tokenInput.value.trim();
            if ((at_token.startsWith('"') && at_token.endsWith('"')) || (at_token.startsWith("'") && at_token.endsWith("'"))) at_token = at_token.slice(1, -1);

            if (cookie && at_token) {
                chrome.storage.local.set({ auth: { cookie, at_token } }, () => checkAuthState());
            } else {
                alert('Please provide both Cookie and AT Token.');
            }
        };
        authContainer.appendChild(saveBtn);

        // Main Interaction Container (Generate, Preview)
        const interactionContainer = document.createElement('div');
        interactionContainer.id = UI_CONTAINER_ID + '-interaction-container';
        interactionContainer.style.display = 'flex';
        interactionContainer.style.flexDirection = 'column';
        interactionContainer.style.gap = '12px';
        container.appendChild(interactionContainer);

        // Generate Button
        const generateBtn = document.createElement('button');
        generateBtn.id = UI_CONTAINER_ID + '-generate-btn';
        generateBtn.className = 'altrosyn-btn';
        generateBtn.textContent = 'Generate Infographic';
        generateBtn.onclick = () => {
            const url = window.location.href;
            updateUI('RUNNING');
            chrome.runtime.sendMessage({ type: 'GENERATE_INFOGRAPHIC', url: url });
        };
        interactionContainer.appendChild(generateBtn);

        // Image Preview
        const img = document.createElement('img');
        img.id = UI_CONTAINER_ID + '-img-preview';
        img.className = 'altrosyn-img-preview';
        interactionContainer.appendChild(img);

        // Link
        const link = document.createElement('a');
        link.id = UI_CONTAINER_ID + '-link';
        link.className = 'altrosyn-link';
        link.textContent = 'Open Full Size';
        link.target = '_blank';
        link.style.display = 'none';
        interactionContainer.appendChild(link);
    }
    return container;
}

function updateUI(status, imageUrl = null, errorMessage = null) {
    const container = getOrCreateUI();
    const statusEl = document.getElementById(UI_CONTAINER_ID + '-status');
    const authContainer = document.getElementById(UI_CONTAINER_ID + '-auth-container');
    const interactionContainer = document.getElementById(UI_CONTAINER_ID + '-interaction-container');
    const generateBtn = document.getElementById(UI_CONTAINER_ID + '-generate-btn');
    const imgPreview = document.getElementById(UI_CONTAINER_ID + '-img-preview');
    const link = document.getElementById(UI_CONTAINER_ID + '-link');

    // Default container display
    container.style.display = 'flex';

    if (status === 'AUTH_REQUIRED') {
        statusEl.textContent = 'Setup Connection';
        authContainer.style.display = 'flex';
        interactionContainer.style.display = 'none';
        return;
    }

    // Auth is good
    authContainer.style.display = 'none';
    interactionContainer.style.display = 'flex';

    // Status Text
    if (status === 'RUNNING') {
        statusEl.textContent = 'Generating...';
        statusEl.style.color = '#5f6368';
    } else if (status === 'COMPLETED') {
        statusEl.textContent = 'Done!';
        statusEl.style.color = '#137333';
    } else if (status === 'FAILED') {
        statusEl.textContent = errorMessage || 'Failed';
        statusEl.style.color = '#d93025';
    } else {
        statusEl.textContent = 'Ready';
        statusEl.style.color = '#5f6368';
    }

    // Button State
    if (status === 'RUNNING') {
        generateBtn.textContent = 'Creating Magic...';
        generateBtn.disabled = true;
    } else if (status === 'COMPLETED') {
        generateBtn.textContent = 'Generate New';
        generateBtn.className = 'altrosyn-btn altrosyn-btn-secondary'; // Secondary style for "Again"
        generateBtn.disabled = false;
    } else {
        generateBtn.textContent = 'Generate Infographic';
        generateBtn.className = 'altrosyn-btn';
        generateBtn.disabled = false;
    }

    // Image & Link
    if (status === 'COMPLETED' && imageUrl) {
        imgPreview.src = imageUrl;
        imgPreview.style.display = 'block';
        imgPreview.onclick = () => window.open(imageUrl, '_blank');

        link.href = imageUrl;
        link.style.display = 'block';
    } else {
        imgPreview.style.display = 'none';
        link.style.display = 'none';
    }
}

// Scoped State Restoration
function restoreStateForCurrentVideo() {
    const videoId = extractVideoId(window.location.href);
    if (!videoId) return;

    chrome.storage.local.get(['infographicStates'], (result) => {
        const states = result.infographicStates || {};
        const state = states[videoId];

        if (state) {
            updateUI(state.status, state.image_url, state.error);
        } else {
            updateUI('IDLE');
        }
    });
}

// Listen for status updates
chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'INFOGRAPHIC_UPDATE') {
        const currentVideoId = extractVideoId(window.location.href);
        if (currentVideoId && message.videoId === currentVideoId) {
            updateUI(message.status, message.image_url, message.error);
        }
    } else if (message.type === 'AUTH_EXPIRED') {
        updateUI('AUTH_REQUIRED');
    }
});
