import requests
import time
import subprocess
import os
import sys
import json
from datetime import datetime

RECOVERY_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'recovery.json')

RECOVERY_CONFIG = {
    "service_a": {
        "url": "http://localhost:5001/health",
        "restart_command": [sys.executable, "services/service_a.py"],
        "max_retries": 3,
        "retry_interval": 5
    },
    "service_b": {
        "url": "http://localhost:5002/health",
        "restart_command": [sys.executable, "services/service_b.py"],
        "max_retries": 3,
        "retry_interval": 5
    },
    "service_c": {
        "url": "http://localhost:5003/health",
        "restart_command": [sys.executable, "services/service_c.py"],
        "max_retries": 3,
        "retry_interval": 5
    }
}

recovery_state = {
    name: {"attempts": 0, "last_recovery": None, "status": "idle"}
    for name in RECOVERY_CONFIG
}

running_processes = {}

def load_recovery_log():
    try:
        with open(RECOVERY_LOG, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except:
        return []

def save_recovery_event(event):
    events = load_recovery_log()
    events.append(event)
    with open(RECOVERY_LOG, 'w') as f:
        json.dump(events, f, indent=2)

def is_service_healthy(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def attempt_recovery(name, config):
    state = recovery_state[name]

    if state["attempts"] >= config["max_retries"]:
        print(f"\n❌ [{name}] Max retries reached — manual intervention required")
        state["status"] = "failed"
        return False

    state["attempts"] += 1
    state["last_recovery"] = datetime.now().isoformat()
    state["status"] = "recovering"

    print(f"\n🔄 [{name}] Recovery attempt {state['attempts']}/{config['max_retries']}")

    # Kill existing process
    if name in running_processes:
        try:
            running_processes[name].terminate()
            running_processes[name].wait(timeout=5)
        except:
            pass

    # Restart service
    try:
        process = subprocess.Popen(
            config["restart_command"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        running_processes[name] = process
        print(f"   🚀 Restarted {name} (PID: {process.pid})")

        time.sleep(config["retry_interval"])

        if is_service_healthy(config["url"]):
            state["status"] = "recovered"
            state["attempts"] = 0
            print(f"   ✅ {name} recovered successfully!")
            save_recovery_event({
                "service": name,
                "event": "recovery_successful",
                "timestamp": datetime.now().isoformat(),
                "action": "Service restarted",
                "success": True
            })
            return True
        else:
            print(f"   ⚠️  {name} still unhealthy after restart")
            save_recovery_event({
                "service": name,
                "event": "recovery_failed",
                "timestamp": datetime.now().isoformat(),
                "action": "Restart attempted but service still unhealthy",
                "success": False
            })
            return False

    except Exception as e:
        print(f"   ❌ Recovery error: {e}")
        save_recovery_event({
            "service": name,
            "event": "recovery_error",
            "timestamp": datetime.now().isoformat(),
            "action": f"Error: {str(e)}",
            "success": False
        })
        return False

def get_recovery_status():
    return recovery_state

def print_recovery_summary():
    print("\n  🔧 Recovery Status:")
    for name, state in recovery_state.items():
        icon = {"idle": "✅", "recovering": "🔄", "recovered": "✅", "failed": "❌"}.get(state["status"], "❓")
        print(f"     {icon} {name}: {state['status']} (attempts: {state['attempts']})")