import os
import time
from notebooklm_client import NotebookLMClient
import json

# Credentials
HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-goog-authuser": "0",
    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    "origin": "https://notebooklm.google.com", 
    "referer": "https://notebooklm.google.com/",
    "cookie": ""
}
AT_TOKEN = ""

def main():
    print("Initializing Client...")
    
    client = NotebookLMClient(headers=HEADERS, at_token=AT_TOKEN)
    
    try:
        print("\n--- Creating Notebook ---")
        nb = client.create_notebook("AI")
        print(f"✅ Created: {nb}")
        nb_id = nb['notebook_id']
        
        print("\n--- Adding Sources ---")
        urls = [
            "https://www.youtube.com/watch?v=qfVbRAZ-4rs",
            "https://www.youtube.com/watch?v=rgvBhn9xQrM&pp=2AYB"
        ]
        
        added_source_ids = []
        for url in urls:
            print(f"Adding: {url}")
            source_res = client.add_source(nb_id, "URL", json.dumps({"url": url}))
            print(f"✅ Source Result: {source_res}")
            
            sid = source_res.get("source_id")
            if sid:
                added_source_ids.append(sid)
            time.sleep(2)

        if not added_source_ids:
             print("Check if sources exist anyway...")
             sources = client._get_sources(nb_id)
             if sources:
                 added_source_ids = sources
                 print(f"✅ Found sources in notebook: {len(added_source_ids)}")
        
        if added_source_ids:
             # Wait for ingestion to complete
             print("Waiting for sources to stabilize (10s)...")
             time.sleep(10)
             
             print(f"\n--- Running Tool (Infographic) on Sources {added_source_ids} ---")
             op_id = None
             for attempt in range(3):
                 # Run on ALL added sources (client will handle list)
                 tool_res = client.run_stdio_tool(nb_id, "infographic", "", source_ids=added_source_ids)
                 op_id = tool_res.get("operation_id")
                 if op_id:
                     print(f"✅ Operation Started: {op_id}")
                     break
                 print(f"DEBUG: Tool run failed (Attempt {attempt+1}/3). Retrying in 10s...")
                 time.sleep(10)
             
             if op_id:
                 print(f"--- Waiting for Infographic (Operation: {op_id}) ---")
                 try:
                     result = client.wait_for_tool_execution(op_id, "infographic")
                     
                     if result.get("status") == "DONE":
                         print(f"✅ Generated Infographic URL: {result.get('data')}")
                     else:
                         print("❌ Operation failed or did not complete successfully.")
                 except Exception as e:
                     print(f"❌ Error waiting for infographic: {e}")
             else:
                 print("Skipping wait as Operation ID was not retrieved.")

        else:
             print("Skipping tool run (no source_ids)")
             
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
