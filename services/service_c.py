from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import random
import threading

app = Flask(__name__)

# SRE Metrics
REQUEST_COUNT = Counter('service_c_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('service_c_request_latency_seconds', 'Request latency')
UPTIME_GAUGE = Gauge('service_c_up', 'Service C uptime status')
FAILURE_COUNT = Counter('service_c_failures_total', 'Total simulated failures')

START_TIME = time.time()
UPTIME_GAUGE.set(1)

# Failure simulation state
failure_mode = {"active": False, "type": None}

def random_failure_simulator():
    """Randomly triggers failure modes to simulate real world incidents"""
    while True:
        # Every 30-60 seconds randomly trigger a failure
        time.sleep(random.uniform(30, 60))
        failure_types = ["latency_spike", "partial_outage", "healthy"]
        failure_mode["type"] = random.choice(failure_types)
        if failure_mode["type"] != "healthy":
            failure_mode["active"] = True
            print(f"[Service C] ⚠️  Failure mode activated: {failure_mode['type']}")
            FAILURE_COUNT.inc()
            # Failure lasts 10-20 seconds
            time.sleep(random.uniform(10, 20))
            failure_mode["active"] = False
            failure_mode["type"] = None
            print("[Service C] ✅ Recovered from failure")

# Start failure simulator thread
failure_thread = threading.Thread(target=random_failure_simulator, daemon=True)
failure_thread.start()

@app.route('/health')
def health():
    if failure_mode["active"] and failure_mode["type"] == "partial_outage":
        UPTIME_GAUGE.set(0)
        REQUEST_COUNT.labels(method='GET', endpoint='/health', status='503').inc()
        return jsonify({
            "service": "service_c",
            "status": "unhealthy",
            "failure_type": failure_mode["type"],
            "uptime_seconds": round(time.time() - START_TIME, 2)
        }), 503

    UPTIME_GAUGE.set(1)
    REQUEST_COUNT.labels(method='GET', endpoint='/health', status='200').inc()
    return jsonify({
        "service": "service_c",
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": "1.0.0"
    }), 200

@app.route('/api/data')
def get_data():
    start = time.time()

    if failure_mode["active"] and failure_mode["type"] == "latency_spike":
        # Simulate severe latency
        time.sleep(random.uniform(3, 8))

    if failure_mode["active"] and failure_mode["type"] == "partial_outage":
        REQUEST_COUNT.labels(method='GET', endpoint='/api/data', status='503').inc()
        return jsonify({
            "service": "service_c",
            "error": "service unavailable",
            "failure_type": "partial_outage"
        }), 503

    duration = time.time() - start
    REQUEST_LATENCY.observe(duration)
    REQUEST_COUNT.labels(method='GET', endpoint='/api/data', status='200').inc()
    return jsonify({
        "service": "service_c",
        "data": "flaky data response",
        "latency_ms": round(duration * 1000, 2),
        "failure_mode": failure_mode["type"]
    }), 200

@app.route('/api/trigger-failure/<failure_type>')
def trigger_failure(failure_type):
    """Manual failure trigger for demo purposes"""
    valid_types = ["latency_spike", "partial_outage"]
    if failure_type not in valid_types:
        return jsonify({"error": f"Invalid failure type. Use: {valid_types}"}), 400
    failure_mode["active"] = True
    failure_mode["type"] = failure_type
    FAILURE_COUNT.inc()
    UPTIME_GAUGE.set(0)
    print(f"[Service C] ⚠️  Manual failure triggered: {failure_type}")
    return jsonify({
        "service": "service_c",
        "message": f"Failure mode '{failure_type}' activated",
        "duration": "15 seconds"
    }), 200

@app.route('/api/recover')
def recover():
    """Manual recovery trigger for demo purposes"""
    failure_mode["active"] = False
    failure_mode["type"] = None
    UPTIME_GAUGE.set(1)
    print("[Service C] ✅ Manual recovery triggered")
    return jsonify({
        "service": "service_c",
        "message": "Service recovered",
        "status": "healthy"
    }), 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    print("Service C running on port 5003 (intentionally flaky)")
    app.run(port=5003, debug=False)