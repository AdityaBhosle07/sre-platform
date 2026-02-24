import threading
import time
import os
import sys
import json
import requests
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitoring.alert_manager import evaluate_alerts, print_alert_summary
from monitoring.auto_recovery import attempt_recovery, print_recovery_summary, RECOVERY_CONFIG

SERVICES = {
    "service_a": "http://localhost:5001/health",
    "service_b": "http://localhost:5002/health",
    "service_c": "http://localhost:5003/health",
}

SLO_TARGET = 99.9
ERROR_BUDGET_MINUTES = 43.8

local_state = {
    name: {
        "status": "unknown",
        "last_check": None,
        "consecutive_failures": 0,
        "total_checks": 0,
        "total_failures": 0,
        "uptime_percent": 100.0,
        "error_budget_consumed": 0.0,
        "last_latency": None
    }
    for name in SERVICES
}

running_processes = []

def start_service(name, script_path):
    process = subprocess.Popen(
        [sys.executable, script_path],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print(f"  ✅ {name} started (PID: {process.pid})")
    return process

def start_dashboard():
    from dashboard.dashboard import app
    app.run(port=5000, debug=False, use_reloader=False)

def check_service(url):
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        latency = round((time.time() - start) * 1000, 2)
        return response.status_code == 200, latency, response.status_code
    except requests.exceptions.Timeout:
        return False, 5000, "TIMEOUT"
    except:
        return False, None, "DOWN"

def update_state(name, is_healthy, latency):
    state = local_state[name]
    state["last_latency"] = latency
    state["total_checks"] += 1

    if not is_healthy:
        state["total_failures"] += 1
        state["consecutive_failures"] += 1
        state["status"] = "down" if latency is None else "unhealthy"
    else:
        state["consecutive_failures"] = 0
        state["status"] = "healthy"

    checks = state["total_checks"]
    failures = state["total_failures"]
    state["uptime_percent"] = round(((checks - failures) / checks) * 100, 3)
    downtime_pct = 100 - state["uptime_percent"]
    state["error_budget_consumed"] = round(
        (downtime_pct / (100 - SLO_TARGET)) * ERROR_BUDGET_MINUTES, 2
    )

def print_status_table():
    print(f"\n{'='*65}")
    print(f"  HEALTH CHECK — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*65}")
    print(f"  {'SERVICE':<15} {'STATUS':<12} {'LATENCY':<12} {'UPTIME':<10} BUDGET")
    print(f"  {'-'*60}")
    for name, state in local_state.items():
        icon = "✅" if state["status"] == "healthy" else "🔴"
        latency_str = f"{state['last_latency']}ms" if state['last_latency'] else "N/A"
        budget = f"{state['error_budget_consumed']}/{ERROR_BUDGET_MINUTES}m"
        print(f"  {icon} {name:<15} {state['status']:<12} {latency_str:<12} {state['uptime_percent']}%  {budget}")
    print(f"{'='*65}")

def run_health_checker():
    print("\n🚀 SRE Platform Started Successfully!")
    print("="*65)
    print(f"  Dashboard  → http://localhost:5000")
    print(f"  Service A  → http://localhost:5001")
    print(f"  Service B  → http://localhost:5002")
    print(f"  Service C  → http://localhost:5003 (flaky)")
    print(f"  SLO Target → {SLO_TARGET}% | Budget → {ERROR_BUDGET_MINUTES} min/month")
    print("="*65)

    while True:
        for name, url in SERVICES.items():
            is_healthy, latency, code = check_service(url)
            update_state(name, is_healthy, latency)

        print_status_table()
        evaluate_alerts(local_state)
        print_alert_summary()

        # Auto recovery
        for name, state in local_state.items():
            if state["consecutive_failures"] >= 3 and name in RECOVERY_CONFIG:
                print(f"\n⚡ Auto-recovery triggered for {name}")
                attempt_recovery(name, RECOVERY_CONFIG[name])

        print_recovery_summary()
        time.sleep(10)

def main():
    print("\n" + "="*65)
    print("  🚀 STARTING SRE PLATFORM")
    print("="*65)

    # Initialize log files
    for log_file in ['logs/incidents.json', 'logs/alerts.json', 'logs/recovery.json']:
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump([], f)

    # Start microservices
    print("\n📦 Starting microservices...")
    running_processes.append(start_service("Service A", "services/service_a.py"))
    running_processes.append(start_service("Service B", "services/service_b.py"))
    running_processes.append(start_service("Service C", "services/service_c.py"))

    print("\n⏳ Waiting for services to boot...")
    time.sleep(3)

    # Start dashboard
    print("\n🖥️  Starting dashboard...")
    dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
    dashboard_thread.start()
    print("  ✅ Dashboard started → http://localhost:5000")

    # Start health checker
    print("\n🔍 Starting health checker...\n")
    try:
        run_health_checker()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down SRE Platform...")
        for p in running_processes:
            p.terminate()
        print("  ✅ All services stopped\n")

if __name__ == '__main__':
    main()