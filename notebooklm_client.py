import json
import time
import random
import string
import requests
import urllib.parse
from typing import Dict, Any, Optional, Tuple

class NotebookLMClient:
    def __init__(self, base_url: str = "https://notebooklm.google.com", headers: Optional[Dict] = None, cookies: Optional[Dict] = None, at_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if headers:
            self.session.headers.update(headers)
        
        # Ensure Content-Type is set for batchexecute
        self.session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        })

        if cookies:
            self.session.cookies.update(cookies)
        
        self.at_token = at_token
        self.current_notebook_id: Optional[str] = None
        self._req_id_counter = random.randint(100000, 999999)
        
        # Dynamically fetch params to match current cookies/session
        self.f_sid, self.bl = self._fetch_params()
        print(f"DEBUG: Initialized with f.sid: {self.f_sid} and bl: {self.bl}")

    def _fetch_params(self) -> Tuple[Optional[str], Optional[str]]:
        try:
            print("DEBUG: Fetching params from homepage...")
            resp = self.session.get(self.base_url + "/")
            import re
            
            f_sid = None
            matches = re.findall(r'"FdrFJe":"([-0-9]+)"', resp.text)
            if matches:
                f_sid = matches[0]
                
            bl = None
            matches_bl = re.findall(r'"(boq_[^"]+)"', resp.text)
            if matches_bl:
                labs = [m for m in matches_bl if "labs-tailwind" in m]
                if labs:
                    bl = labs[0]
                else:
                    bl = matches_bl[0]
            
            if not bl:
                 bl = "boq_labs-tailwind-frontend_20260101.17_p0"
                 
            return f_sid, bl
        except Exception as e:
            print(f"Warning: Failed to fetch params: {e}")
            return None, "boq_labs-tailwind-frontend_20260101.17_p0"

    def _get_req_id(self) -> str:
        self._req_id_counter += 1000
        return str(self._req_id_counter)

    def _parse_envelope(self, content: bytes) -> Any:
        try:
            # Robust Text-Based Parsing
            # Ignore the byte-length prefixes and just look for valid JSON lines
            text = content.decode('utf-8', errors='ignore')
            
            # Remove header prefix
            if text.startswith(")]}'"):
                text = text[4:]
            
            # The format is typically: length \n json \n length \n json
            # We can try to parse everything that looks like a JSON array
            lines = text.split('\n')
            results = []
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Heuristic: Valid batchexecute chunks are arrays starting with [[
                if line.startswith('[['):
                    try:
                        obj = json.loads(line)
                        results.append(obj)
                    except:
                        pass
                elif line.startswith('[') and 'wrb.fr' in line:
                     # Sometimes the structure is simpler
                     try:
                        obj = json.loads(line)
                        results.append(obj)
                     except:
                        pass

            # Flatten results
            flattened = []
            for res in results:
                if isinstance(res, list):
                    flattened.extend(res)
            
            # Debug: Log if we found nothing
            if not flattened and len(text) > 50:
                 print(f"DEBUG: ParseEnvelope found no objects. Text sample: {text[:200]}")
                 
            return flattened
            
        except Exception as e:
            print(f"Error parsing envelope: {e}")
            return []

    def _execute_rpc(self, rpc_id: str, payload: Any) -> Any:
        if not self.at_token:
            # Try to fetch or warn. For now, proceeding assumes token might be in cookies or not needed (unlikely)
            pass

        url = f"{self.base_url}/_/LabsTailwindUi/data/batchexecute"
        
        # Update Referer if inside a notebook
        # if self.current_notebook_id:
        #      self.session.headers.update({
        #          "Referer": f"{self.base_url}/notebook/{self.current_notebook_id}"
        #      })
        
        # Serialize payload: [payload_json, null, generic_id] wrapped in envelope
        f_req = json.dumps([[[rpc_id, json.dumps(payload), null, "generic"] for null in [None]]])
        
        params = {
            "rpcids": rpc_id,
            "source-path": f"/notebook/{self.current_notebook_id}" if self.current_notebook_id else "/",
            "f.sid": self.f_sid,
            "bl": self.bl,
            "hl": "en-GB",
            "_reqid": self._get_req_id(),
            "rt": "c"
        }
        
        data = {
            "f.req": f_req,
            "at": self.at_token or ""
        }
        
        # DEBUG PAYLOAD
        print(f"DEBUG REQ to {url} rpc={rpc_id} f.sid={params['f.sid']}")
        # print(f"DEBUG REQ to {url} params={params} data={data}")
        # print(f"DEBUG REQ f.req={f_req}")
        
        response = self.session.post(url, params=params, data=data)
        if response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}: {response.text}")
            
        parsed = self._parse_envelope(response.content)
        
        if not parsed or not isinstance(parsed, list):
            # It's possible the response was empty or just status updates.
            # Return raw parsed to be safe.
            print(f"DEBUG: Empty/Invalid Parsed Response. Raw Body: {response.text[:200]}")
            return parsed
            
        # print(f"DEBUG: Full Parsed Response: {json.dumps(parsed, indent=2)}") 
        
        combined_results = []
        found_any = False
        
        for chunk in parsed:
            if isinstance(chunk, list) and len(chunk) > 2 and chunk[1] == rpc_id:
                inner_payload = chunk[2]
                if inner_payload is not None:
                    found_any = True
                    try:
                        data = json.loads(inner_payload)
                        if isinstance(data, list):
                            combined_results.extend(data)
                        else:
                            # If it's a dict or other, just append? RPCs usually return lists of items.
                            # For safety, if it's not a list, maybe we shouldn't extend. 
                            # But gArtLc returns [ [Item], [Item] ]
                            combined_results.append(data)
                    except:
                        pass
        
        if found_any:
            # print(f"DEBUG RPC '{rpc_id}' found {len(combined_results)} items.")
            return combined_results
            
        # If no valid payload found, return empty list
        # print(f"DEBUG RPC '{rpc_id}' returned EMPTY list. Raw parsed count: {len(parsed)}")
        return []

    def create_notebook(self, title: str, description: Optional[str] = None) -> Dict:
        # RPC: CCqFvf
        payload = [title, None, None, [2], [1, None, None, None, None, None, None, None, None, None, [1]]]
        
        resp = self._execute_rpc("CCqFvf", payload)
        
        try:
           notebook_id = resp[2]
           if not notebook_id or not isinstance(notebook_id, str):
               # Fallback search
               for item in resp:
                   if isinstance(item, str) and len(item) == 36 and '-' in item:
                       notebook_id = item
                       break
        except:
             notebook_id = None

        if not notebook_id:
             raise Exception(f"Failed to create notebook. API Response: {resp}")

        self.current_notebook_id = notebook_id
        return {"notebook_id": notebook_id, "title": title}

    def _find_uuid(self, obj: Any) -> Optional[str]:
        # Recursive search for UUID string
        if isinstance(obj, str):
            if len(obj) == 36 and obj.count('-') == 4:
                return obj
            # Check for nested JSON string
            if obj.strip().startswith('[') or obj.strip().startswith('{'):
                try:
                    nested = json.loads(obj)
                    res = self._find_uuid(nested)
                    if res: return res
                except:
                    pass
                    
        if isinstance(obj, list):
            for item in obj:
                res = self._find_uuid(item)
                if res: return res
                
        if isinstance(obj, dict):
            for val in obj.values():
                res = self._find_uuid(val)
                if res: return res
                
        return None

    def get_sources(self, notebook_id: str) -> list:
        return self._get_sources(notebook_id)

    def wait_for_ingestion_job(self, job_id: str) -> Dict:
        print(f"DEBUG: Waiting for ingestion job {job_id}...")
        print("Note: YouTube videos may take 1-2 minutes to process (transcription)...")
        for i in range(60): # 5 minutes max
            info = self.get_ingestion_status(job_id)
            if info["status"] == "completed":
                print("DEBUG: Ingestion job completed.")
                return info
            if i % 2 == 0:
                 print("... still processing video ...")
            time.sleep(5)
        raise TimeoutError(f"Ingestion job {job_id} timed out")

    def add_source(self, notebook_id: Optional[str], source_type: str, content: str) -> Dict:
        if notebook_id:
            self.current_notebook_id = notebook_id
        
        if not self.current_notebook_id:
            raise ValueError("Notebook ID required")
            
        # Get initial sources to track new additions
        initial_sources = set(self._get_sources(self.current_notebook_id))
            
        source_type = source_type.upper()
        
        # Check for YouTube URL
        is_youtube = False
        if "youtube.com" in content or "youtu.be" in content:
            is_youtube = True
            print("DEBUG: YouTube URL detected. Handling as async media source.")
            
        # RPC: izAoDd
        
        if source_type == "URL" or is_youtube:
            # Extract content as dictionary
            try:
                url_val = json.loads(content).get("url")
            except:
                url_val = content 
                
            source_payload = [None] * 11
            source_payload[7] = [url_val]
            # HAR analysis shows 1 is used for YouTube as well
            source_payload[10] = 1 
            
            payload = [
                [source_payload], 
                self.current_notebook_id,
                [2],
                [1, None, None, None, None, None, None, None, None, None, [1]]
            ]
        else:
            raise NotImplementedError(f"Source type {source_type} not supported in this version")
            
        resp = self._execute_rpc("izAoDd", payload)
        print(f"DEBUG: Add Source Response: {json.dumps(resp, indent=2)}")
        
        # Try to extract ID from response first
        extracted_source_id = self._find_uuid(resp)
        
        if extracted_source_id:
             print(f"DEBUG: Found Source ID immediately: {extracted_source_id}")
             return {"source_id": extracted_source_id, "status": "pending_background" if is_youtube else "completed"}
        
        # Baseline Diffing Logic for Async Sources (YouTube) ONLY if ID not found
        if is_youtube: 
            print("DEBUG: Polling for new source ID via baseline diffing...")
            for attempt in range(20): # 40 seconds max
                # Refresh notebook state to trigger updates
                self.refresh_notebook(self.current_notebook_id)
                
                # Fetch current sources
                current_sources = set(self._get_sources(self.current_notebook_id))
                
                # Check for new items
                new_items = current_sources - initial_sources
                if new_items:
                    found_id = list(new_items)[0]
                    print(f"DEBUG: Found new source ID: {found_id}")
                    return {"source_id": found_id, "status": "completed"}
                
                print(f"DEBUG: Attempt {attempt+1}/20: No new source yet. Sleeping...")
                time.sleep(2)
                
            print("Warning: Polling timed out. No new source ID found.")
            raise Exception("Failed to resolve new source ID after polling (Timeout)")
        
        print(f"DEBUG: Add Source Response: {json.dumps(resp, indent=2)}")

        # Try to extract ID from response first
        extracted_source_id = self._find_uuid(resp)
        
        # If standard find failed, parse nested JSON from izAoDd structure
        if not extracted_source_id and isinstance(resp, list) and len(resp) > 2:
             try:
                 inner_json = resp[2]
                 if isinstance(inner_json, str):
                     parsed_inner = json.loads(inner_json)
                     extracted_source_id = self._find_uuid(parsed_inner)
             except:
                 pass

        final_source_id = extracted_source_id
        
        if is_youtube:
            # Async ingestion handling
            print("DEBUG: Async media source. Skipping blocking wait for user convenience.")
            
            # If we got an ID, verify it exists or just return it
            if final_source_id:
                 # Check 'wait_for_ingestion_job' ONLY if we want to block.
                 # User requested "terminal ease", so we assume server will handle it.
                 # Just return success.
                 return {"source_id": final_source_id, "status": "pending_background"}
            else:
                 # If we didn't get an ID immediately, it likely failed or is being weird.
                 # But we should try polling anyway because sometimes the backend is silent but effective.
                 print("Warning: No Source ID returned from API. Will attempt to poll for new source...")
                 # Do not return early. Fall through to polling logic.
            
            # Refresh notebook state
            self.refresh_notebook(self.current_notebook_id)
            
            # Verify final ID exists
            current_sources = self._get_sources(self.current_notebook_id)
            if final_source_id and final_source_id in current_sources:
                 return {"source_id": final_source_id, "status": "completed"}
            elif not final_source_id:
                 # Check if any new source appeared
                 new_items = set(current_sources) - initial_sources
                 if new_items:
                     return {"source_id": list(new_items)[0], "status": "completed"}

        if not final_source_id:
             print("DEBUG: Source ID extraction failed. Attempting to poll for new source...")
             try:
                 new_source_id = self._poll_for_new_source(initial_sources)
                 final_source_id = new_source_id
             except TimeoutError:
                 print("Warning: Ingestion polling timed out or source not found in list.")
                 return {"source_id": None, "status": "unknown"}

        return {"source_id": final_source_id, "status": "pending"}

    def _poll_for_new_source(self, initial_sources: set) -> Optional[str]:
        # Poll up to ~8 minutes (100 * 5s)
        for i in range(100):
            current_sources = self._get_sources(self.current_notebook_id)
            # Use logic to find diff
            curr_set = set(current_sources)
            new_items = curr_set - initial_sources
            if new_items:
                return list(new_items)[0]
            time.sleep(5)
        raise TimeoutError("Ingestion timed out")

    def _get_sources(self, notebook_id: str) -> list:
        # Use _get_all_artifacts which uses correct HAR payload
        resp = self._get_all_artifacts(notebook_id)
        
        if not resp:
            return []

        # Flatten response to find source IDs
        ids = []
        def collect_uuids(obj):
            if isinstance(obj, str) and len(obj) == 36 and obj.count('-') == 4:
                ids.append(obj)
            if isinstance(obj, list):
                for item in obj:
                    collect_uuids(item)
                    
        collect_uuids(resp)
        return ids

    def get_operation_status(self, operation_id: str) -> Dict:
        if not self.current_notebook_id:
             raise ValueError("Notebook ID required to check operation status")
             
        artifacts = self._get_all_artifacts(self.current_notebook_id)
        
        target = None
        for art in artifacts:
            if isinstance(art, list) and len(art) > 0 and art[0] == operation_id:
                target = art
                break
                
        if not target:
            return {"operation_id": operation_id, "status": "UNKNOWN"}

    def get_ingestion_status(self, job_id: str) -> Dict:
        # Check if job_id (source_id) exists in notebook sources
        sources = self._get_sources(self.current_notebook_id)
        status = "completed" if job_id in sources else "processing"
        return {"job_id": job_id, "status": status}

    def refresh_notebook(self, notebook_id: str) -> Dict:
        self.current_notebook_id = notebook_id
        # Call gArtLc to get fresh state (sources etc)
        self._get_sources(notebook_id)
        return {"notebook_id": notebook_id, "status": "refreshed"}

    def run_stdio_tool(self, notebook_id: Optional[str], tool_type: str, input_text: str, source_ids: Optional[list] = None, options: Optional[Dict] = None) -> Dict:
        if notebook_id:
            self.current_notebook_id = notebook_id
        
        if not self.current_notebook_id:
            raise ValueError("Notebook ID required")

        # Map tools
        tools = {
            "audio_overview": 1,
            "summary": 3,
            "study_guide": 4,
            "mindmap": 5,
            "infographic": 7,
            "slide_deck": 8,
            "timeline": 9,
        }
        
        tool_id = tools.get(tool_type.lower())
        if not tool_id and "infographic" in tool_type.lower():
             tool_id = 7
             
        if not tool_id:
             raise ValueError(f"Unknown tool: {tool_type}")

        # Need Source IDs. 
        if not source_ids:
             source_ids = self._get_sources(self.current_notebook_id)
             
        if not source_ids:
            raise ValueError("No sources in notebook to run tool on")
            
        source_param = [[[sid]] for sid in source_ids]
        
        # Payload structures based on HAR analysis
        
        if tool_id == 7: # Infographic
            # [None, None, 7, source, None * 10, [[None, None, None, 1, 2]]]
             tool_payload = [None, None, 7, source_param] + [None]*10 + [[[None, None, None, 1, 2]]]
             
        elif tool_id == 8: # Slide Deck
            # [None, None, 8, source, None * 12, [[]]]
            # Count from HAR: 16 nulls/items before tail?
            # HAR: [N, N, 8, Source, N,N,N,N, N,N,N,N, N,N,N,N, [[]]] - 4 blocks of 4?
            # HAR Step 360 dump for ID 8 had HUGE null padding.
            # PRETTY PAYLOAD shows: [N,N,8,Source, N x 12, [[]]]
            # Let's trust the pattern [N, N, ID, Source] + Padding + Tail
            tool_payload = [None, None, 8, source_param] + [None]*12 + [[[]]]
            
        elif tool_id == 9: # Timeline
            # [N, N, 9, Source, N x 14, [None, []]]
            tool_payload = [None, None, 9, source_param] + [None]*14 + [[None, []]]
            
        elif tool_id == 4: # Study Guide
            # [N, N, 4, Source, N x 5, [None, [1, None, None, None, None, None, [2,2]]]]
            tail = [None, [1, None, None, None, None, None, [2,2]]]
            tool_payload = [None, None, 4, source_param] + [None]*5 + [tail]
            
        elif tool_id == 3: # Summary
             # Try simpler structure: [None, None, 3, source, None * 12, [[]]]
             # Matches Slide Deck / Generic
             # tool_payload = [None, None, 3, source_param] + [None]*10 + [[[None, None, None, 1, 2]]]
             # FAILED with empty result. Trying Slide Deck style
             tool_payload = [None, None, 3, source_param] + [None]*12 + [[[]]]
             
        elif tool_id == 1: # Audio Overview
             # HAR Structure (approx):
             # [None, None, 1, source_param, None, None, [None, [None, None, None, source_simple, "en-GB", True]], ...]
             # source_simple seems to be [["UUID"]] instead of [[["UUID"]]]
             source_simple = source_param[0] if source_param else []
             conf_block = [None, [None, None, None, source_simple, "en-GB", True]]
             
             # The timestamps in HAR might be optional or generated? 
             # Let's try matching the head and see if tail is defaulted.
             # [..., conf_block, None, None, None, [TS, TS], ...]
             # Using a shorter version first to see if server accepts it (often defaults work).
             # If not, we might need to copy the FULL struct.
             # For now, let's look at the fallback I used before:
             # [None, [1, None, None, "en-GB", None, None, [2,2], None, True]]
             # That fallback was for "Audio" in some contexts? 
             
             # Let's use the structure derived from Step 360 HAR dump for ID 1:
             # [N, N, 1, Source, N, N, [N, [N,N,N, S_Simple, "en-GB", True]]]
             tool_payload = [None, None, 1, source_param, None, None, conf_block]
             
        elif tool_id == 5: # Mind Map
             # No HAR data available. Assume similar to Summary/Infographic (ID 3/7)
             # as they are standard text-processing tools.
             tool_payload = [None, None, 5, source_param] + [None]*10 + [[[None, None, None, 1, 2]]]
             
        else:
             # Fallback
             tool_payload = [
                None, None, tool_id, source_param, 1, None, None, None, None,
                [None, [1, None, None, "en-GB", None, None, [2,2], None, True]] 
            ]

        payload = [[2], self.current_notebook_id, tool_payload]
        
        resp = self._execute_rpc("R7cb6c", payload)
        
        op_id = None
        if isinstance(resp, list) and len(resp) > 0 and isinstance(resp[0], list):
             op_id = resp[0][0]
             
        if not op_id:
             print(f"Warning: Could not extract Operation ID from response: {resp}")

        return {"operation_id": op_id, "status": "PENDING"}

    def _get_all_artifacts(self, notebook_id: str) -> list:
        # RPC: gArtLc
        # Use filter from HAR
        # payload = [[2], notebook_id, "NOT artifact.status = \"ARTIFACT_STATUS_SUGGESTED\""]
        # Try no filter to ensure we get everything
        payload = [[2], notebook_id, None]
        resp = self._execute_rpc("gArtLc", payload)
        if not resp:
            return []
        
        # Flatten if response is nested (common in gArtLc: [[Art1, Art2]])
        flat = []
        for item in resp:
             if isinstance(item, list) and len(item) > 0 and isinstance(item[0], list):
                 flat.extend(item)
             else:
                 flat.append(item)
        return flat

    def get_operation_status(self, operation_id: str) -> Dict:
        if not self.current_notebook_id:
             raise ValueError("Notebook ID required to check operation status")
             
        artifacts = self._get_all_artifacts(self.current_notebook_id)
        
        target = None
        for art in artifacts:
            if isinstance(art, list) and len(art) > 0 and art[0] == operation_id:
                target = art
                break
                
        if not target:
            return {"operation_id": operation_id, "status": "UNKNOWN"}
            
        status_code = target[4] if len(target) > 4 else None
        
        if status_code == 3:
            state = "COMPLETED" # Mapped to DONE in wait wrapper
        elif status_code == 1:
            state = "RUNNING"
        elif status_code is None:
             state = "PENDING"
        else:
            state = "FAILED"
            
        return {"operation_id": operation_id, "status": state}

    def wait_for_tool_execution(self, operation_id: str, tool_type: str, poll_interval: int = 3) -> Dict:
        """
        Polls for the completion of a tool execution.
        tool_type: "infographic", "summary", "audio_overview", "study_guide", etc.
        Returns: { "status": "DONE", "operationId": ..., "data": ... }
        """
        print(f"DEBUG: wait_for_tool_execution ({tool_type}) started for {operation_id}")
        last_print = 0
        
        while True:
            status_info = self.get_operation_status(operation_id)
            state = status_info.get("status")
            
            # Map COMPLETED to DONE
            if state == "COMPLETED":
                state = "DONE"
            
            if time.time() - last_print > 5:
                print(f"DEBUG: Operation {operation_id} status: {state}")
                last_print = time.time()
            
            if state == "DONE":
                try:
                    data = self.get_generated_artifact(self.current_notebook_id, tool_type)
                    return {
                        "status": "DONE",
                        "operationId": operation_id,
                        "data": data
                    }
                except Exception as e:
                    print(f"Operation DONE but extraction failed: {e}. Retrying extraction...")
                    time.sleep(2)
                    data = self.get_generated_artifact(self.current_notebook_id, tool_type)
                    return {
                        "status": "DONE",
                        "operationId": operation_id,
                        "data": data
                    }

            # Fallback: If UNKNOWN (lost op) or RUNNING, check if artifact exists anyway
            if state in ["UNKNOWN", "RUNNING"]:
                 try:
                     # Check if we can find a *recent* artifact of this type
                     # AND verify we can extract data from it (proving it's done)
                     temp_data = self.get_generated_artifact(self.current_notebook_id, tool_type)
                     if temp_data:
                         print(f"DEBUG: Operation {state} but Artifact content found. Returning DONE.")
                         return {
                            "status": "DONE", 
                            "operationId": operation_id,
                            "data": temp_data
                         }
                 except:
                     pass # Not ready

            if state == "FAILED":
                return {
                    "status": "FAILED",
                    "operationId": operation_id,
                    "error": "Operation reported failure"
                }

            time.sleep(poll_interval)

    def get_generated_artifact(self, notebook_id: str, tool_type: str) -> Any:
        self.current_notebook_id = notebook_id
        artifacts = self._get_all_artifacts(notebook_id)
        
        tools_map = {
            "audio_overview": 1,
            "summary": 3,
            "study_guide": 4,
            "mindmap": 5,
            "infographic": 7,
            "slide_deck": 8,
            "timeline": 9,
        }
        
        target_type_id = tools_map.get(tool_type.lower())
        if not target_type_id:
             raise ValueError(f"Unknown tool type: {tool_type}")
             
        candidates = []
        for art in artifacts:
            if isinstance(art, list) and len(art) > 2 and art[2] == target_type_id:
                candidates.append(art)
                
        if not candidates:
            # raise Exception(f"No assets of type {tool_type} found in notebook")
            return None # Allow None so polling loop can continue
            
        def get_ts(item):
            # timestamp usually at index 10: [sec, nanos]
            if len(item) > 10 and isinstance(item[10], list) and len(item[10]) > 0:
                 return item[10][0]
            return 0
            
        candidates.sort(key=get_ts, reverse=True)
        latest = candidates[0]
        
        # Extraction logic per type
        if target_type_id == 7: # Infographic
             return self._extract_infographic(latest)
        elif target_type_id == 3: # Summary
             return self._extract_summary(latest)
        elif target_type_id == 1: # Audio
             return self._extract_audio(latest)
        
        # Default return raw artifact for unmapped types
        return latest

    def _extract_infographic(self, artifact: list) -> str:
        try:
            content_block = artifact[14]
            items = content_block[2]
            url = items[0][1][0]
            return url
        except:
             raise Exception("Failed to extract Infographic URL")

    def _extract_summary(self, artifact: list) -> str:
        try:
             # Summary text is usually in index 14 -> 2 -> 0 -> 0 (text)
             # Structure inspection needed. Assuming generic text block.
             # Based on previous HAR dumps for text content:
             content_block = artifact[14]
             # print(content_block) # Debug
             # Usually [None, None, [ [ "Text Content", ... ] ] ]
             text = content_block[2][0][0]
             return text
        except:
             # Fallback: dump whole thing to debug or just return string rep
             return str(artifact[14])

    def _extract_audio(self, artifact: list) -> Optional[str]:
         try:
             # content_block is at index 14. If it's None, no audio yet.
             if len(artifact) <= 14 or artifact[14] is None:
                 return None
                 
             content_block = artifact[14]
             # For Audio, we expect a URL or specific structure. 
             return str(content_block) 
         except:
             return None

    # Deprecated but kept for compatibility if needed
    def get_generated_infographic(self, notebook_id: str) -> str:
        res = self.get_generated_artifact(notebook_id, "infographic")
        if not res:
            raise Exception("No infographic found")
        return res
