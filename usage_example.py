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
    "cookie": "SEARCH_SAMESITE=CgQIzJ8B; __Secure-BUCKET=CN8G; __Secure-ENID=30.SE=J_jI30cvqdKNhXIicAOEi--ff2WamkcfvCsy-iuBzQ2Vj_jyWoEHkQA625mQKFiwEnS6uC7uyE3-mqQJy3Dw7iVLR7CfcuQ_tJ4kLRwKqwGD-BmIj1opb7Pr9bPehFNW4h5VRMTSV_iz4oL9UWZGUUqaZReZLIcBvFM0TKoq2B_psrSixQHNg-KF8uO3lKCjv27QfRKZxJ2ZzI8H264WKKJuHVgLabOq96sSNHC1xs866DwnjJ9NiHXBoT3r7mE3cDNwtozZgI_7IkB45OexOFTNHZxqXSKIpIuKGkcMN7gcBpcdHeIyMaYE5z-j4Wh7PQas_xDTbc5TvGk6YFQwp6Zk9ceh7_8-jzl6jo3ck8U_xJDKQo3dZpIZvJlwtUCl5WA5Y3n8HwMytg; _gcl_au=1.1.866551627.1766549662; _ga=GA1.1.298575599.1766549659; SID=g.a0005Agd2EYv4o9RNkRP_EvelCCcByzqMSRu8BcRPUMyMcUhdtm8Tr42x7bH7H4beu4Y3-BOLAACgYKAU8SARASFQHGX2MiRnW-sDffXSnTVh3zStHKOhoVAUF8yKpHvfvDLamu0Kmx6j01WZ5i0076; __Secure-1PSID=g.a0005Agd2EYv4o9RNkRP_EvelCCcByzqMSRu8BcRPUMyMcUhdtm8cDIyovrDL13vwjyTGaTK9QACgYKAaESARASFQHGX2MiNTPsV_v21Q5WSfzQBuMiVhoVAUF8yKpM0wrcJ76-11fc7wharopr0076; __Secure-3PSID=g.a0005Agd2EYv4o9RNkRP_EvelCCcByzqMSRu8BcRPUMyMcUhdtm88ppdldwvjMkJcxYnZhY5KwACgYKAX8SARASFQHGX2Mi2_ufdZ2DByoQXhycOjCDshoVAUF8yKoSaYioEafq3jBbvSUD4Cne0076; HSID=AmRjwQ95BwGa-AUzz; SSID=ARBKpPoBWi_nVoFaR; APISID=EC7W0BDFcJBRcXJ8/A4MjXu1VaOeW57_qj; SAPISID=PK83DMx1MzDd7aJU/AwS4S0QaPXUtTS-3U; __Secure-1PAPISID=PK83DMx1MzDd7aJU/AwS4S0QaPXUtTS-3U; __Secure-3PAPISID=PK83DMx1MzDd7aJU/AwS4S0QaPXUtTS-3U; OSID=g.a0005Agd2GgtDsr3c-GPmGQbQaN1ggJKVXeR1ODRwEb4NIXMAG6D8nHTDlxrTcBoeMjTs7gH5wACgYKAQISARASFQHGX2Mi7mG4Ts3P3iDzgcD400QkoRoVAUF8yKpYLGGr9fuotY41TtY-mS-b0076; __Secure-OSID=g.a0005Agd2GgtDsr3c-GPmGQbQaN1ggJKVXeR1ODRwEb4NIXMAG6D3LyonGMWk6j-jF1Bx-vO1gACgYKAWwSARASFQHGX2MiVfbH-PZoq7Rc2yD25ZK37RoVAUF8yKoGoIedAq0--NyzVJbvaQqj0076; __Secure-STRP=AD6DogvsqKUf0RjG08EHGE-3ElBYx_KrWyhU6De1BDeR6QCzDGAd9KQk-FTG4BvBih_MsFVCEeDJW_MbtZaejOuBJGnNPp7lVU4C; AEC=AaJma5vfcJDDj5K-aWI3S5tYqh0VxUt1h6Z18txuJGuTFMfrmPjxD9SOFws; NID=527=YZe5jsEmupbmkga3HaWw3npN4VXgYJPcNk6woBkdPNFn6u-CO7iy96NDNxnnkruGYJIhEdXrmGk7G7naT9Kbu8uS0cZBQtGc2WMfd1SqFP9M-U8fD0ceFlQtMMSXLm69qoMpgNBgjKGcnoNwDSnsETxMrcjgo7TRO0Zb-cS5lKfL96yk1cxtQ-a0kvAJPi3a9s27WoHElPtvsA_E_zE8fM0C7BkBNGHjpEVueH-jnRkBteHak4cwIuAu4OlWYVBMjuwG7sALcxzduBpLRPR8x_17cBaCfYc0-S2Qj3eE1jzPpE5fLovfzPxEymcdo6hM_RJzR_ADfuSpi5RkkCSEILcxLRJviW4DlvU3Yir2h8yG_GjB8erHjZ2-2LQB-7sDf4tPUdBKPLkmnz-gxMMLfvs1Qpc05a9l3amy5JgRoMvOv2cxnAS2X-lPGaUTrycP3jjiE99MKjeH9G5rHkwo4GZBPvj9SMne9NJsDNIir5lslEN97PMkcvCPDcK6cJFsAoU_TOy10AfrdFcXs5QeJv0idnyO4HKftm_TPOMRpzqFuRjM3PjrWnojBKZIycs-RWFbkw3Y_KIhp65OOILdtvOIYblEDR0ogC06cjW92aqRFbHHVmQpkXTfBOcutAAx3ysfsxt-ORI6UIIGZJS-TqsCSDEk13QjBIGMku1TRB6p-e2eNQMPNJq_mWArjIEXD70CEAep0JQAXFBHOhdOSr6SEt4aS1H5ZdWnCbf9GeJ5M9xVoT1qyakhb9hY; __Secure-1PSIDTS=sidts-CjIBflaCdUKiqTQukjhFkEKlEfQJPoDD1_QJILJ0WoqFxq50aqyEAkvnNHSmoNzxoo4t5RAA; __Secure-3PSIDTS=sidts-CjIBflaCdUKiqTQukjhFkEKlEfQJPoDD1_QJILJ0WoqFxq50aqyEAkvnNHSmoNzxoo4t5RAA; _gcl_aw=GCL.1767760155.Cj0KCQiAgvPKBhCxARIsAOlK_EoRqq73Qr50-zWFE2zz2pbIU-qIJSHNlcegc2dajyvwa2CgulTzIr0aAn-jEALw_wcB; _ga_W0LDH41ZCB=GS2.1.s1767760153$o16$g1$t1767760173$j40$l0$h0; SIDCC=AKEyXzWPWKxqaz9qH45vCaWWykRtJXwc1oGM5groaEMQX4x1qGAYibGMQ2HR5_y4IMsf4oM6Yg; __Secure-1PSIDCC=AKEyXzWg07Lu69Q3RQ2Eu8OvrOrOGSXcRDKUurNCVUCGEywdWGtdqsLluCxsM5BY4vXimoH-EA; __Secure-3PSIDCC=AKEyXzVdXsQgh2yq_e0HnsPhPGjAy_AgQIA-jXk7PwzltHGIiotD5HtmdjiH1Co91PmOiga7cA"
}
AT_TOKEN = "ACi2F2OqJ3g8lSdCGVYKLy6mx-uI:1767760154786"

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
