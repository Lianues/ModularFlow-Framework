#!/usr/bin/env python3
"""
Robust smoke test for API definition listing endpoint.

This script:
- Loads project modules (to ensure all api/* adapters are registered)
- Starts the API Gateway in background (if possible; detects port-in-use and skips)
- Calls /api/modules/api_gateway/list_apis via SDK with retry
- Prints summary and validates:
  - Non-empty API list
  - Each item has name/path/namespace and dict schemas
- Stops the API Gateway only if started by this script

Run:
  python tests/test_list_apis.py
"""

import sys
import time
from pathlib import Path

def main() -> int:
    # Ensure framework root is on sys.path
    this_file = Path(__file__).resolve()
    framework_root = this_file.parent.parent
    if str(framework_root) not in sys.path:
        sys.path.insert(0, str(framework_root))

    # Lazy imports after sys.path adjustment
    try:
        from core.services import get_service_manager
        from core.api_gateway import get_api_gateway
        from core.api_client import call_api
        from core.api_registry import get_registry
    except Exception as e:
        print(f"[ERROR] Failed to import core modules: {e}")
        return 1

    # Load project modules to register all APIs
    try:
        svc = get_service_manager()
        loaded_count = svc.load_project_modules()
        print(f"[INFO] Loaded project modules: {loaded_count}")
    except Exception as e:
        print(f"[WARN] Failed to load project modules: {e}")

    # Print registry count before starting gateway
    try:
        reg = get_registry()
        fn_count = len(reg.list_functions())
        print(f"[INFO] Registered APIs in registry before gateway: {fn_count}")
        if fn_count == 0:
            print("[WARN] Registry is empty. Ensure api/* adapters call @register_api and modules are loaded.")
    except Exception as e:
        print(f"[WARN] Failed to inspect registry: {e}")

    # Start API Gateway in background
    started_by_script = False
    try:
        gw = get_api_gateway()
        gw.start_server(background=True)
        started_by_script = True
        print("[INFO] API Gateway started in background")
        # Wait a bit for auto registration
        time.sleep(2.0)
    except OSError as e:
        # Handle Windows socket error 10048 (address in use)
        msg = str(e)
        if "10048" in msg or "only one usage" in msg.lower() or "address already in use" in msg.lower():
            print("[WARN] Port 8050 already in use. Assuming API Gateway is already running. Proceeding without starting a new instance.")
            started_by_script = False
        else:
            print(f"[ERROR] Failed to start API Gateway: {e}")
            return 1
    except Exception as e:
        print(f"[ERROR] Failed to start API Gateway: {e}")
        return 1

    # Retry calling list_apis
    max_attempts = 5
    attempt_delay = 1.0
    result = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = call_api("api_gateway/list_apis", method="GET", namespace="modules")
            if isinstance(result, dict) and isinstance(result.get("apis"), list):
                # Good shape; break on success
                break
        except Exception as e:
            print(f"[WARN] Attempt {attempt} failed: {e}")
        time.sleep(attempt_delay)

    # Validate result
    if not isinstance(result, dict):
        print(f"[ERROR] Unexpected response type: {type(result).__name__}")
        # Try to stop gateway if we started it
        if started_by_script:
            try:
                gw = get_api_gateway()
                gw.stop_server()
                print("[INFO] API Gateway stopped")
            except Exception as e:
                print(f"[WARN] Failed to stop API Gateway: {e}")
        return 1

    apis = result.get("apis", [])
    total = result.get("total", len(apis))
    print(f"[INFO] Total APIs: {total}")

    if total == 0:
        print("[ERROR] No APIs returned by list_apis.")
        print("Possible causes and fixes:")
        print("  - API Gateway not running or not fully started. Try increasing wait time or ensure no port conflicts.")
        print("  - Project modules not loaded. Ensure get_service_manager().load_project_modules() ran successfully.")
        print("  - Adapters not updated to new @register_api format or placed under api/modules or api/workflow.")
        # Stop if we started
        if started_by_script:
            try:
                gw = get_api_gateway()
                gw.stop_server()
                print("[INFO] API Gateway stopped")
            except Exception as e:
                print(f"[WARN] Failed to stop API Gateway: {e}")
        return 2

    # Show sample
    for i, api in enumerate(apis[:10], start=1):
        name = api.get("name")
        desc = api.get("description")
        path = api.get("path")
        ns = api.get("namespace")
        print(f"  {i:02d}. [{ns}] {name} -> {path} | {desc}")

    # Basic validations
    problems = []
    for api in apis:
        if not api.get("name"):
            problems.append(f"Missing name for: {api.get('path')}")
        if not api.get("path"):
            problems.append(f"Missing path for api with name: {api.get('name')}")
        if api.get("namespace") not in ("modules", "workflow"):
            problems.append(f"Invalid namespace for {api.get('path')}: {api.get('namespace')}")
        # Validate input/output schema presence (dict types)
        if not isinstance(api.get("input_schema"), dict):
            problems.append(f"input_schema not a dict for {api.get('path')}")
        if not isinstance(api.get("output_schema"), dict):
            problems.append(f"output_schema not a dict for {api.get('path')}")

    if problems:
        print("[ERROR] Validation issues found:")
        for p in problems:
            print("  -", p)
        # Stop if we started
        if started_by_script:
            try:
                gw = get_api_gateway()
                gw.stop_server()
                print("[INFO] API Gateway stopped")
            except Exception as e:
                print(f"[WARN] Failed to stop API Gateway: {e}")
        return 3

    print("[SUCCESS] API definition listing endpoint works and passed validations.")
    # Stop Gateway only if we started it
    if started_by_script:
        try:
            gw = get_api_gateway()
            gw.stop_server()
            print("[INFO] API Gateway stopped")
        except Exception as e:
            print(f"[WARN] Failed to stop API Gateway: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())