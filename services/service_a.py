from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import random

app = Flask(__name__)

# SRE Metrics
REQUEST_COUNT = Counter('service_a_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('service_a_request_latency_seconds', 'Request latency')
UPTIME_GAUGE = Gauge('service_a_up', 'Service A uptime status')
ERROR_RATE = Counter('service_a_errors_total', 'Total errors')

START_TIME = time.time()
UPTIME_GAUGE.set(1)

@app.route('/health')
def health():
    UPTIME_GAUGE.set(1)
    REQUEST_COUNT.labels(method='GET', endpoint='/health', status='200').inc()
    return jsonify({
        "service": "service_a",
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": "1.0.0"
    }), 200

@app.route('/api/data')
def get_data():
    start = time.time()
    # Simulate occasional slow responses
    if random.random() < 0.1:
        time.sleep(2)
    duration = time.time() - start
    REQUEST_LATENCY.observe(duration)
    REQUEST_COUNT.labels(method='GET', endpoint='/api/data', status='200').inc()
    return jsonify({
        "service": "service_a",
        "data": ["item1", "item2", "item3"],
        "latency_ms": round(duration * 1000, 2)
    }), 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.errorhandler(500)
def internal_error(e):
    ERROR_RATE.inc()
    UPTIME_GAUGE.set(0)
    REQUEST_COUNT.labels(method='GET', endpoint='unknown', status='500').inc()
    return jsonify({"error": "internal server error"}), 500

if __name__ == '__main__':
    print("Service A running on port 5001")
    app.run(port=5001, debug=False)