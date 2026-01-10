# Infographic Generator for YouTube

This is a Chrome Extension that integrates with NotebookLM to generate infographics from YouTube videos directly from your browser.

## Features

- **One-Click Generation**: Adds a button to generate infographics while watching YouTube videos.
- **Auto-Authentication**: Uses your existing NotebookLM session.
- **Background Processing**: Handles the creation of notebooks, source addition, and tool execution.

## Prerequisites

Before setting up the extension, ensure you have the following installed:

- **Google Chrome** (or a Chromium-based browser)
- **Python 3.x**
- **pip** (Python package installer)

## Setup Instructions

### 1. Backend Server Setup

The extension relies on a local Python backend to communicate with the NotebookLM API.

1.  Open your terminal.
2.  Navigate to the project root directory (where `server.py` is located):
    ```bash
    cd /path/to/project_root
    ```
3.  Install the required Python dependencies:
    ```bash
    pip install requests
    ```
4.  Start the backend server:
    ```bash
    python3 server.py
    ```
    You should see output indicating the server is starting on port 8000. Keep this terminal window open.

### 2. Chrome Extension Installation

1.  Open Google Chrome.
2.  Navigate to `chrome://extensions/` in the address bar.
3.  Enable **Developer mode** using the toggle switch in the top right corner.
4.  Click the **Load unpacked** button in the top left.
5.  Select the `chrome_extension` folder located inside your project directory.
    - Path: `/path/to/project_root/chrome_extension`

The extension "Infographic Generator for YouTube" should now appear in your list of extensions.

## Usage

1.  Ensure the backend server is running (`python3 server.py`).
2.  Open YouTube and navigate to any video you want to process.
3.  Click the extension icon (a puzzle piece or the specific icon if pinned) in the Chrome toolbar.
4.  If prompted, follow the instructions to authenticate or ensure you are logged into NotebookLM in another tab.
    - *Note: The extension attempts to reuse your existing session cookies.*
5.  Click the **Generate Infographic** button.
6.  Wait for the process to complete (this may take a minute or two as it transcribes usage and generates the image).
7.  The generated infographic will be displayed.

## Troubleshooting

- **Server Error**: Ensure `server.py` is running and port 8000 is not blocked.
- **Authentication Failed**: Make sure you are logged into [NotebookLM](https://notebooklm.google.com/) in the same browser.
- **No Infographic**: Some videos may not support transcription or may be too short/long. Check the server console logs for detailed error messages.
