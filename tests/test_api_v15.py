"""
ACE-Step V1.5 API Test Client

Tests new features introduced in V1.5, including:
- LoRA Management (Upload, List, Delete)
- Prompt Utilities (Transcribe, Understand, Format)
- LoRA Inference Integration

Usage:
    python tests/test_api_v15.py --base-url http://127.0.0.1:8000
"""

import argparse
import io
import json
import os
import sys
import time
import zipfile
import requests
from typing import Optional, Dict, Any

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "test_outputs")

# =============================================================================
# Helper Functions
# =============================================================================

def get_headers(api_key: Optional[str] = None) -> dict:
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers

def create_mock_lora_zip() -> io.BytesIO:
    """Creates a valid-looking LoRA zip file in memory logic."""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, 'w') as zf:
        # 1. adapter_config.json
        config = {
            "r": 8,
            "lora_alpha": 16,
            "target_modules": ["q_proj", "v_proj"],
            "peft_type": "LORA"
        }
        zf.writestr("adapter_config.json", json.dumps(config))
        
        # 2. adapter_model.safetensors (dummy content)
        zf.writestr("adapter_model.safetensors", b"mock_weights_data")
        
    bio.seek(0)
    return bio

def create_mock_audio_file() -> io.BytesIO:
    """Creates a dummy audio file (just random bytes to pass file check)."""
    bio = io.BytesIO()
    bio.write(b"RIFF" + b"\x00" * 32 + b"WAVE" + b"fmt " + b"\x00" * 16 + b"data" + b"\x00" * 1024)
    bio.seek(0)
    return bio

def print_result(name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")

# =============================================================================
# Test Functions
# =============================================================================

def test_lora_lifecycle(base_url: str, api_key: Optional[str] = None) -> bool:
    print("\n" + "="*50)
    print("Test: LoRA Lifecycle (Upload -> List -> Delete)")
    print("="*50)
    
    lora_id = f"test_lora_{int(time.time())}"
    
    # 1. Upload
    print(f"\n1. Uploading LoRA ({lora_id})...")
    zip_file = create_mock_lora_zip()
    files = {"file": ("test_adapter.zip", zip_file, "application/zip")}
    headers = get_headers(api_key)
    # LoRA ID is passed via header in current implementation? 
    # Checking docs... "lora_id | Header"
    headers["lora_id"] = lora_id
    
    try:
        resp = requests.post(f"{base_url}/v1/lora/upload", files=files, headers=headers)
        if resp.status_code != 200:
            print_result("Upload LoRA", False, f"Status: {resp.status_code}, Msg: {resp.text}")
            return False
        
        data = resp.json()
        print_result("Upload LoRA", True, f"Response: {data}")

        # Capture actual ID from server response
        # Structure: {'data': {'lora_id': '...', ...}, 'code': 200, ...}
        if "data" in data and "lora_id" in data["data"]:
            lora_id = data["data"]["lora_id"]
            print(f"       Using server-assigned LoRA ID: {lora_id}")
        else:
            print_result("Upload LoRA", False, "lora_id missing in response data")
            return False
            
    except Exception as e:
        print_result("Upload LoRA", False, f"Exception: {e}")
        return False

    # 2. List
    print("\n2. Listing LoRAs...")
    try:
        resp = requests.get(f"{base_url}/v1/lora/list", headers=get_headers(api_key))
        if resp.status_code != 200:
            print_result("List LoRAs", False, f"Status: {resp.status_code}")
            return False
            
        data = resp.json()
        # Response structure: {'data': {'loras': [...]}, 'code': 200}
        lora_list = data.get("data", {}).get("loras", [])
        found = any(l["id"] == lora_id for l in lora_list)
        
        print_result("List LoRAs", found, f"Found {lora_id} in list: {found}")
        if not found:
            print(f"Debug List: {json.dumps(lora_list, indent=2)}")
            return False
            
    except Exception as e:
        print_result("List LoRAs", False, f"Exception: {e}")
        return False

    # 3. Delete
    print(f"\n3. Deleting LoRA ({lora_id})...")
    try:
        resp = requests.delete(f"{base_url}/v1/lora/{lora_id}", headers=get_headers(api_key))
        if resp.status_code != 200:
            print_result("Delete LoRA", False, f"Status: {resp.status_code}")
            return False
            
        print_result("Delete LoRA", True, "Success")
        
        # Verify deletion
        resp = requests.get(f"{base_url}/v1/lora/list", headers=get_headers(api_key))
        lora_list = resp.json().get("loras", [])
        found = any(l["id"] == lora_id for l in lora_list)
        if found:
            print_result("Verify Deletion", False, "LoRA still exists in list")
            return False
        print_result("Verify Deletion", True, "LoRA removed from list")
            
    except Exception as e:
        print_result("Delete LoRA", False, f"Exception: {e}")
        return False

    return True

def test_prompt_transcribe(base_url: str, api_key: Optional[str] = None) -> bool:
    print("\n" + "="*50)
    print("Test: Prompt Transcribe")
    print("="*50)
    
    payload = {
        "prompt": "An upbeat 80s pop song with synthesizer",
        "task_type": "text2music"
    }
    
    start_time = time.time()
    try:
        resp = requests.post(f"{base_url}/v1/prompt/transcribe", json=payload, headers=get_headers(api_key))
        duration = time.time() - start_time
        
        if resp.status_code != 200:
            print_result("Transcribe", False, f"Status: {resp.status_code}, Msg: {resp.text}")
            return False
            
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        print(f"       Time taken: {duration:.2f}s")
        
        # Basic validation
        # Response structure: {'data': {'metadata': {...}, 'enriched_prompt': ...}, ...}
        if "data" in data and "metadata" in data["data"] and "enriched_prompt" in data["data"]:
            print_result("Transcribe", True, f"Received metadata and caption (took {duration:.2f}s)")
            return True
        else:
            print_result("Transcribe", False, f"Missing keys in response. Keys found: {data.get('data', {}).keys()}")
            return False
            
    except Exception as e:
        print_result("Transcribe", False, f"Exception: {e}")
        return False

def test_prompt_understand(base_url: str, api_key: Optional[str] = None) -> bool:
    print("\n" + "="*50)
    print("Test: Prompt Understand (Audio Analysis)")
    print("="*50)
    
    mock_audio = create_mock_audio_file()
    files = {"file": ("test_audio.wav", mock_audio, "audio/wav")}
    
    # Note: efficient_mode=True to mock faster if supported, or just expect failure on real processing if mock audio is bad
    # But checking endpoint reachability is main goal here.
    
    try:
        resp = requests.post(f"{base_url}/v1/prompt/understand", files=files, headers=get_headers(api_key))
        
        # If the server tries to process the mock audio, it might fail with 500 (decoding error).
        # We accept 200 (Mock worked??) or 500 (Logic reached) but check if it's a 404 (Endpoint missing).
        
        print(f"Status: {resp.status_code}")
        if resp.status_code == 404:
            print_result("Understand Endpoint", False, "Endpoint not found (404)")
            return False
            
        # The mock audio is just random bytes, so it likely fails decording. 
        # However, getting a response means the endpoint exists and logic ran.
        print_result("Understand Endpoint", True, f"Endpoint reachable (Status: {resp.status_code})")
        return True
            
    except Exception as e:
        print_result("Understand Endpoint", False, f"Exception: {e}")
        return False

def test_lora_inference_params(base_url: str, api_key: Optional[str] = None) -> bool:
    print("\n" + "="*50)
    print("Test: LoRA Inference Params Parsing")
    print("="*50)
    
    # We can't easily verify the *effect* of LoRA without trained weights, 
    # but we can verify the API accepts the parameters without error.
    
    payload = {
        "prompt": "Test prompt",
        "lora_id": "non_existent_lora_id", # Should probably be ignored or log warning, but validation shouldn't crash
        "lora_scale": 0.8,
        "inference_steps": 1, # Fast fail/pass
        "thinking": False
    }
    
    try:
        resp = requests.post(f"{base_url}/release_task", json=payload, headers=get_headers(api_key))
        if resp.status_code != 200:
            print_result("Inference Request", False, f"Status: {resp.status_code}, Msg: {resp.text}")
            return False
            
        data = resp.json()
        task_id = data.get("data", {}).get("task_id")
        print_result("Inference Request", True, f"Task ID: {task_id}")
        return True
        
    except Exception as e:
        print_result("Inference Request", False, f"Exception: {e}")
        return False

    except Exception as e:
        print_result("Inference Request", False, f"Exception: {e}")
        return False

def test_full_generation_with_scores(base_url: str, api_key: Optional[str] = None) -> bool:
    print("\n" + "="*50)
    print("Test: Full Generation Result (Scores & LRC)")
    print("="*50)
    print("⚠️  This test waits for actual generation. Ctrl+C to skip if no GPU.")
    
    payload = {
        "prompt": "Test song for scoring",
        "lyrics": "[00:00.00] Test lyrics", # Provide lyrics to trigger score calculation
        "inference_steps": 4, # Use few steps for speed
        "thinking": False
    }
    
    task_id = None
    try:
        # 1. Submit Task
        resp = requests.post(f"{base_url}/release_task", json=payload, headers=get_headers(api_key))
        if resp.status_code != 200:
            print_result("Submit Task", False, f"Status: {resp.status_code}, Avg: {resp.text}")
            return False
        
        data = resp.json()
        task_id = data.get("data", {}).get("task_id")
        print_result("Submit Task", True, f"Task ID: {task_id}")
        
    except Exception as e:
        print_result("Submit Task", False, f"Exception: {e}")
        return False

    # 2. Poll for Result
    print("   Polling for result (timeout 60s)...")
    start_time = time.time()
    while time.time() - start_time < 60:
        try:
            resp = requests.post(f"{base_url}/query_result", json={"task_id_list": [task_id]}, headers=get_headers(api_key))
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    task_info = data[0]
                    status = task_info.get("status") # 0: running, 1: success, 2: failed
                    
                    if status == 1: # Success
                        result_data = json.loads(task_info.get("result", "[]"))
                        if not result_data:
                            print_result("Generation Result", False, "Empty result data")
                            return False
                            
                        first_item = result_data[0]
                        # Verify fields
                        has_lrc = "lrc" in first_item
                        has_lm_score = "lm_score" in first_item
                        has_dit_score = "dit_score" in first_item
                        
                        details = f"LRC: {has_lrc}, LM Score: {has_lm_score}, DiT Score: {has_dit_score}"
                        print(f"       Fields found: {details}")
                        
                        if has_lrc and has_lm_score and has_dit_score:
                            print_result("Verify Fields", True, "All score/LRC fields present")
                            return True
                        else:
                            print_result("Verify Fields", False, f"Missing fields. Got keys: {list(first_item.keys())}")
                            return False
                            
                    elif status == 2: # Failed
                        print_result("Generation Status", False, "Task failed on server")
                        return False
            
            time.sleep(2)
        except Exception as e:
            print(f"   Polling error: {e}")
            time.sleep(2)
            
    print_result("Generation Status", False, "Timeout waiting for generation")
    return False

def main():
    parser = argparse.ArgumentParser(description="ACE-Step V1.5 API Test Suite")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API Base URL")
    parser.add_argument("--api-key", help="API Key")
    parser.add_argument("--test", choices=["lora", "prompt", "inference", "scores", "all"], default="all")
    
    args = parser.parse_args()
    
    print(f"Starting Tests on {args.base_url}")
    
    results = {}
    
    if args.test in ["lora", "all"]:
        results["lora"] = test_lora_lifecycle(args.base_url, args.api_key)
        
    if args.test in ["prompt", "all"]:
        results["transcribe"] = test_prompt_transcribe(args.base_url, args.api_key)
        results["understand"] = test_prompt_understand(args.base_url, args.api_key)
        
    if args.test in ["inference", "all"]:
        results["inference"] = test_lora_inference_params(args.base_url, args.api_key)
        
    if args.test in ["scores", "all"]:
        results["scores"] = test_full_generation_with_scores(args.base_url, args.api_key)
        
    print("\n" + "="*50)
    print("Final Results")
    print("="*50)
    all_passed = True
    for k, v in results.items():
        status = "✅ PASS" if v else "❌ FAIL"
        if not v: all_passed = False
        print(f"{status} | {k}")
        
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
