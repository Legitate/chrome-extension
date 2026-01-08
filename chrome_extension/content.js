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
    if (isYouTubeVideo(url)) {
        console.log('YouTube video detected:', url);
        chrome.runtime.sendMessage({ type: 'YOUTUBE_ACTIVE', url: url });
        restoreStateForCurrentVideo();
    } else {
        // Reset UI if not on a video
        updateUI('IDLE');
    }
}

function isYouTubeVideo(url) {
    return url.includes('youtube.com/watch') || url.includes('youtu.be/');
}

// --- UI INJECTION & LINK IMPLEMENTATION ---

function getOrCreateUI() {
    let container = document.getElementById(UI_CONTAINER_ID);
    if (!container) {
        container = document.createElement('div');
        container.id = UI_CONTAINER_ID;
        Object.assign(container.style, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: '300px',
            backgroundColor: '#fff',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            borderRadius: '8px',
            padding: '16px',
            zIndex: '2147483647',
            fontFamily: 'Roboto, Arial, sans-serif',
            display: 'none',
            flexDirection: 'column',
            gap: '12px'
        });
        document.body.appendChild(container);

        // Header/Status
        const statusEl = document.createElement('div');
        statusEl.id = UI_CONTAINER_ID + '-status';
        statusEl.style.fontWeight = '500';
        statusEl.style.color = '#0f0f0f';
        container.appendChild(statusEl);

        // Image Preview Container
        const imgContainer = document.createElement('div');
        imgContainer.id = UI_CONTAINER_ID + '-img-container';
        container.appendChild(imgContainer);

        // Action Container (Link)
        const actionContainer = document.createElement('div');
        actionContainer.id = UI_CONTAINER_ID + '-actions';
        container.appendChild(actionContainer);

        // Generate Button Container
        const buttonContainer = document.createElement('div');
        buttonContainer.id = UI_CONTAINER_ID + '-btn-container';
        container.appendChild(buttonContainer);

        const generateBtn = document.createElement('button');
        generateBtn.id = UI_CONTAINER_ID + '-generate-btn';
        Object.assign(generateBtn.style, {
            width: '100%',
            padding: '10px',
            backgroundColor: '#065fd4',
            color: 'white',
            border: 'none',
            borderRadius: '18px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            marginTop: '8px'
        });
        generateBtn.onclick = () => {
            const url = window.location.href;
            updateUI('RUNNING');
            chrome.runtime.sendMessage({ type: 'GENERATE_INFOGRAPHIC', url: url });
        };
        buttonContainer.appendChild(generateBtn);
    }
    return container;
}

function updateUI(status, imageUrl = null, errorMessage = null) {
    const container = getOrCreateUI();
    const statusEl = document.getElementById(UI_CONTAINER_ID + '-status');
    const imgContainer = document.getElementById(UI_CONTAINER_ID + '-img-container');
    const actionContainer = document.getElementById(UI_CONTAINER_ID + '-actions');
    const generateBtn = document.getElementById(UI_CONTAINER_ID + '-generate-btn');

    container.style.display = 'flex';

    // Status Text
    if (status === 'RUNNING') {
        statusEl.textContent = 'Generating Infographic...';
        statusEl.style.color = '#0f0f0f';
    } else if (status === 'COMPLETED') {
        statusEl.textContent = 'Infographic Ready';
        statusEl.style.color = '#0f0f0f';
    } else if (status === 'FAILED') {
        statusEl.textContent = errorMessage || 'Generation Failed';
        statusEl.style.color = '#d32f2f';
    } else {
        statusEl.textContent = 'Ready to Generate';
        statusEl.style.color = '#0f0f0f';
    }

    // Button State
    if (status === 'RUNNING') {
        generateBtn.textContent = 'Generating...';
        generateBtn.disabled = true;
        generateBtn.style.opacity = '0.7';
        generateBtn.style.cursor = 'not-allowed';
    } else if (status === 'COMPLETED') {
        generateBtn.textContent = 'Generate Again';
        generateBtn.disabled = false;
        generateBtn.style.opacity = '1';
        generateBtn.style.cursor = 'pointer';
    } else {
        generateBtn.textContent = 'Generate Infographic';
        generateBtn.disabled = false;
        generateBtn.style.opacity = '1';
        generateBtn.style.cursor = 'pointer';
    }

    // Image & Link Visibility
    if (status === 'RUNNING' || status === 'IDLE') {
        imgContainer.innerHTML = '';
        actionContainer.innerHTML = '';
    }

    if (status === 'FAILED') {
        imgContainer.innerHTML = '';
        actionContainer.innerHTML = '';
    }

    if (status === 'COMPLETED' && imageUrl) {
        imgContainer.innerHTML = '';
        actionContainer.innerHTML = '';

        const img = document.createElement('img');
        img.src = imageUrl;
        Object.assign(img.style, {
            width: '100%',
            height: 'auto',
            borderRadius: '4px',
            border: '1px solid #e5e5e5',
            cursor: 'pointer',
            marginTop: '8px'
        });
        img.onclick = () => window.open(imageUrl, '_blank');
        imgContainer.appendChild(img);

        const link = document.createElement('a');
        link.href = imageUrl;
        link.textContent = 'Open Infographic';
        link.target = '_blank';
        Object.assign(link.style, {
            display: 'block',
            textAlign: 'center',
            color: '#065fd4',
            textDecoration: 'none',
            padding: '8px',
            fontSize: '14px',
            fontWeight: '500'
        });
        link.onmouseover = () => link.style.textDecoration = 'underline';
        link.onmouseout = () => link.style.textDecoration = 'none';
        actionContainer.appendChild(link);
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
        // Only update UI if the message is for the current video
        if (currentVideoId && message.videoId === currentVideoId) {
            updateUI(message.status, message.image_url, message.error);
        }
    }
});
