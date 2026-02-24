from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import random
import threading

app = Flask(__name__)

REQUEST_COUNT = Counter('service_b_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('service_b_request_latency_seconds', 'Request latency')
UPTIME_GAUGE = Gauge('service_b_up', 'Service B uptime status')
JOBS_PROCESSED = Counter('service_b_jobs_processed_total', 'Total jobs processed')
JOBS_FAILED = Counter('service_b_jobs_failed_total', 'Total jobs failed')

START_TIME = time.time()
UPTIME_GAUGE.set(1)
job_queue = []

def background_worker():
    while True:
        if job_queue:
            job = job_queue.pop(0)
            try:
                time.sleep(random.uniform(0.1, 0.5))
                if random.random() < 0.05:
                    raise Exception(f"Failed to process job {job['id']}")
                JOBS_PROCESSED.inc()
                print(f"[Service B] Processed job {job['id']}")
            except Exception as e:
                JOBS_FAILED.inc()
                print(f"[Service B] Job failed: {e}")
        time.sleep(0.1)

worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()

@app.route('/health')
def health():
    UPTIME_GAUGE.set(1)
    REQUEST_COUNT.labels(method='GET', endpoint='/health', status='200').inc()
    return jsonify({
        "service": "service_b",
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "queue_size": len(job_queue),
        "version": "1.0.0"
    }), 200

@app.route('/api/process', methods=['POST'])
def process():
    start = time.time()
    job_id = "job_{}_{}".format(int(time.time()), random.randint(100, 999))
    job_queue.append({"id": job_id, "created_at": time.time()})
    duration = time.time() - start
    REQUEST_LATENCY.observe(duration)
    REQUEST_COUNT.labels(method='POST', endpoint='/api/process', status='202').inc()
    return jsonify({
        "service": "service_b",
        "job_id": job_id,
        "status": "queued",
        "queue_size": len(job_queue)
    }), 202

@app.route('/api/status')
def status():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/status', status='200').inc()
    return jsonify({
        "service": "service_b",
        "queue_size": len(job_queue),
        "worker_status": "running"
    }), 200

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    print("Service B running on port 5002")
    app.run(port=5002, debug=False)