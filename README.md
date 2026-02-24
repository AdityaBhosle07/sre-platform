# 🚀 SRE Platform

A production-inspired Site Reliability Engineering platform built to demonstrate core SRE principles including fault detection, SLO tracking, automated alerting, auto-recovery, and real-time observability.

Built as a portfolio project aligned with Google SRE practices.

---

## 📐 Architecture

```
sre-platform/
├── services/
│   ├── service_a.py       # Core REST API service (port 5001)
│   ├── service_b.py       # Background job processing service (port 5002)
│   └── service_c.py       # Intentionally flaky service (port 5003)
├── monitoring/
│   ├── health_checker.py  # Continuous health checks + SLO tracking
│   ├── alert_manager.py   # Threshold-based alerting engine
│   └── auto_recovery.py   # Automated service recovery
├── dashboard/
│   └── dashboard.py       # Real-time web dashboard (port 5000)
├── logs/
│   ├── incidents.json     # Incident log
│   ├── alerts.json        # Alert history
│   └── recovery.json      # Recovery event log
└── main.py                # Platform entrypoint
```

---

## ⚙️ SRE Concepts Implemented

### Service Level Objectives (SLOs)
Each service targets **99.9% uptime** — the same standard used for Google's production services.

### Error Budgets
The platform tracks real-time error budget consumption per service:
- **Error budget** = allowable downtime at 99.9% SLO = **43.8 minutes/month**
- When a service consumes >50% of its error budget an alert fires automatically

### Health Checking
Every 10 seconds the health checker:
- Pings all 3 services
- Records latency, status and uptime
- Updates SLO and error budget calculations
- Triggers alerts and recovery if thresholds are breached

### Automated Alerting
Alerts fire automatically when:
| Alert Type | Threshold | Severity |
|-----------|-----------|----------|
| Consecutive failures | 3+ failures | P1 |
| SLO breach | Uptime < 99% | P1 |
| Error budget | >50% consumed | P2 |
| High latency | >1000ms | P2 |

### Auto-Recovery (Toil Elimination)
When a service fails 3+ consecutive health checks the platform:
1. Logs the incident with timestamp and severity
2. Automatically restarts the failed service
3. Verifies recovery with a follow-up health check
4. Resolves the incident if service returns healthy
5. Retries up to 3 times before escalating

### Blameless Incident Logging
Every incident is logged with:
- Unique incident ID (e.g. `INC-1234567890`)
- Detection timestamp
- Severity (P1/P2)
- Root cause (auto-populated on recovery)
- Resolution timestamp

---

## 🖥️ Dashboard

The real-time dashboard at `http://localhost:5000` shows:
- **Incident log** with severity, status and root cause
- **Alert history** with fire and resolution times
- **Auto-recovery log** with success/failure outcomes
- Auto-refreshes every 10 seconds

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Services | Python 3 + Flask |
| Metrics | Prometheus Client |
| Dashboard | Flask + Jinja2 |
| Monitoring | Custom Python health checker |
| Alerting | Custom threshold-based alert engine |
| Recovery | Subprocess-based auto-restart |
| Version Control | Git + GitHub |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/AdityaBhosle07/sre-platform.git
cd sre-platform

# Install dependencies
pip3 install flask prometheus-client requests

# Run the platform
python3 main.py
```

### Access Points
| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5000 |
| Service A | http://localhost:5001 |
| Service B | http://localhost:5002 |
| Service C | http://localhost:5003 |

---

## 🧪 Simulating Incidents

### Trigger a manual failure on Service C:
```bash
# Trigger partial outage
curl http://localhost:5003/api/trigger-failure/partial_outage

# Trigger latency spike
curl http://localhost:5003/api/trigger-failure/latency_spike

# Manual recovery
curl http://localhost:5003/api/recover
```

### What happens next:
1. Health checker detects failure within **10 seconds**
2. Incident is logged to `logs/incidents.json`
3. Alert fires if threshold is breached
4. Auto-recovery triggers after **3 consecutive failures**
5. Dashboard updates automatically

---

## 📊 Sample Incident Log

```json
{
  "id": "INC-1771925709",
  "service": "service_c",
  "detected_at": "2026-02-24T04:35:09",
  "type": "service_degradation",
  "severity": "P1",
  "resolved_at": "2026-02-24T04:35:42",
  "root_cause": "Auto-detected recovery — service returned healthy status",
  "action_taken": "Auto-recovery triggered"
}
```

---

## 📖 SRE Principles Referenced

This project is inspired by Google's SRE practices as documented in:
- [Site Reliability Engineering](https://sre.google/sre-book/table-of-contents/) — Google
- [The Site Reliability Workbook](https://sre.google/workbook/table-of-contents/) — Google

Key concepts applied:
- **Toil elimination** through automated recovery
- **Blameless postmortems** through structured incident logging
- **Error budgets** as a reliability management tool
- **SLO-based alerting** over threshold-based monitoring

---

## 👨‍💻 Author

**Aditya Bhosle**
- GitHub: [@AdityaBhosle07](https://github.com/AdityaBhosle07)
- LinkedIn: [Aditya Bhosle](https://linkedin.com/in/adityabhosle)
