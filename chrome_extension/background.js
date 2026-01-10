// background.js

// Disable icon by default on install
chrome.runtime.onInstalled.addListener(async () => {
    chrome.action.disable();
    const tabs = await chrome.tabs.query({ url: "*://*.youtube.com/*" });
    for (const tab of tabs) {
        chrome.action.enable(tab.id);
    }
});

// Store the latest known YouTube URL.
let currentYouTubeUrl = null;

// Listen for messages from the content script and popup.
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'YOUTUBE_ACTIVE') {
        const tabId = sender.tab.id;
        currentYouTubeUrl = message.url;

        // Enable the popup for this specific tab
        chrome.action.enable(tabId);

        console.log('Enabled action for tab:', tabId, message.url);
        sendResponse({ status: 'enabled' });

    } else if (message.type === 'GENERATE_INFOGRAPHIC') {
        handleGenerateInfographic(message.url, sendResponse);
        return true; // Keep the message channel open for async response
    }
});

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

async function broadcastStatus(url, status, payload = {}) {
    try {
        const videoId = extractVideoId(url);
        // If AUTH_EXPIRED, we might not have a video ID context if it failed generically, 
        // but typically we do. Even if not, we can broadcast to all YT tabs.

        const allYoutubeTabs = await chrome.tabs.query({ url: "*://*.youtube.com/*" });
        for (const tab of allYoutubeTabs) {
            // Check if tab is displaying the same video or if it's a generic auth error
            if ((videoId && tab.url && extractVideoId(tab.url) === videoId) || status === 'AUTH_EXPIRED') {
                chrome.tabs.sendMessage(tab.id, {
                    type: status === 'AUTH_EXPIRED' ? 'AUTH_EXPIRED' : "INFOGRAPHIC_UPDATE",
                    videoId: videoId,
                    status: status,
                    ...payload
                }).catch(() => { });
            }
        }
    } catch (e) {
        console.error("Broadcast failed:", e);
    }
}

async function updateState(videoId, newState) {
    if (!videoId) return;
    const result = await chrome.storage.local.get(['infographicStates']);
    const states = result.infographicStates || {};
    states[videoId] = newState;
    await chrome.storage.local.set({ infographicStates: states });
}

async function handleGenerateInfographic(url, sendResponse) {
    const videoId = extractVideoId(url);
    if (!videoId) {
        sendResponse({ success: false, error: 'Invalid YouTube URL' });
        return;
    }

    // Get Auth
    const storage = await chrome.storage.local.get(['auth']);
    const auth = storage.auth;

    if (!auth || !auth.cookie || !auth.at_token) {
        const err = 'Authentication missing. Please connect using the panel in the bottom right corner of the YouTube page.';
        broadcastStatus(url, 'AUTH_EXPIRED');
        sendResponse({ success: false, error: err });
        return;
    }

    try {
        await updateState(videoId, {
            status: 'RUNNING',
            operation_id: Date.now()
        });
        broadcastStatus(url, 'RUNNING');

        const backendUrl = 'http://localhost:8000/generate-infographic';
        console.log(`Sending request to backend: ${backendUrl} with url: ${url}`);

        const response = await fetch(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                youtube_url: url,
                auth: {
                    cookie: auth.cookie,
                    at_token: auth.at_token
                }
            })
        });

        if (response.status === 401 || response.status === 403) {
            console.warn('Authentication failed. Clearing credentials.');
            await chrome.storage.local.remove('auth');
            await updateState(videoId, { status: 'FAILED', error: 'Authentication Expired' }); // Reset state
            broadcastStatus(url, 'AUTH_EXPIRED');
            sendResponse({ success: false, error: 'Authentication Expired' });
            return;
        }

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error: ${response.status} ${errorText}`);
        }

        const data = await response.json();
        console.log('Backend response:', data);

        if (data.image_url) {
            await updateState(videoId, {
                status: 'COMPLETED',
                image_url: data.image_url
            });
            broadcastStatus(url, 'COMPLETED', { image_url: data.image_url });
            sendResponse({ success: true, imageUrl: data.image_url });
        } else {
            const err = 'No image URL returned from backend.';
            await updateState(videoId, {
                status: 'FAILED',
                error: err
            });
            broadcastStatus(url, 'FAILED', { error: err });
            sendResponse({ success: false, error: err });
        }

    } catch (error) {
        console.error('Error generating infographic:', error);
        await updateState(videoId, {
            status: 'FAILED',
            error: error.message
        });
        broadcastStatus(url, 'FAILED', { error: error.message });
        sendResponse({ success: false, error: error.message });
    }
}
