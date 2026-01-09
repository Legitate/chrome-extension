# notebooklm_endpoints.py

BASE_URL = "https://notebooklm.google.com"
BATCH_EXECUTE_ENDPOINT = "/_/LabsTailwindUi/data/batchexecute"

# RPC IDs
RPC_LIST_NOTEBOOKS = "CCqFvf"
RPC_CREATE_NOTEBOOK = "hPTbtc"
RPC_ADD_SOURCE = "izAoDd"#url
RPC_RUN_TOOL = "R7cb6c"
RPC_GET_ARTIFACT_STATUS = "gArtLc"

# Tool IDs
TOOL_ID_AUDIO_OVERVIEW = 1
TOOL_ID_SUMMARY = 3
TOOL_ID_STUDY_GUIDE = 4
TOOL_ID_MIND_MAP = 5
TOOL_ID_INFOGRAPHIC = 7
TOOL_ID_SLIDE_DECK = 8
TOOL_ID_TIMELINE = 9

TOOL_NAME_MAP = {
    TOOL_ID_AUDIO_OVERVIEW: "Audio Overview",
    TOOL_ID_SUMMARY: "Summary",
    TOOL_ID_STUDY_GUIDE: "Study Guide",
    TOOL_ID_INFOGRAPHIC: "Infographic",
    TOOL_ID_SLIDE_DECK: "Slide Deck",
    TOOL_ID_TIMELINE: "Timeline"
}
