# CivicFlow - Smart Municipal Complaint & Resolution Management Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg?style=for-the-badge)](#)

**CivicFlow** is an enterprise-grade, full-lifecycle Smart Municipal Grievance Redressal and Resolution Management Platform. Designed for modern municipal corporations and city governance authorities, it digitizes public service delivery by bridging citizens, field crews, departmental engineers, and city commissioners into a unified, transparent operational workflow.

---

## 🏛️ System Architecture

CivicFlow is built strictly following Django's **Model-View-Template (MVT)** architectural standard and structured into **17 domain-specific modular applications**:

```
Smart_Municipal/
├── civicflow/                      # Core WSGI/ASGI settings and root routing
├── apps/
│   ├── core/                       # Base models, custom templatetags, health checks, error handlers
│   ├── accounts/                   # Custom User model, 4 distinct roles, clearance decorators
│   ├── citizens/                   # Resident profile extensions, identity verification
│   ├── departments/                # Administrative divisions (PWD, SWM, WSS, ESL, HOR, HVC)
│   ├── wards/                      # Municipal geographic hierarchy (Zone -> Ward -> Area)
│   ├── complaints/                 # Complaint entity, reference generator (CF-YYYYMMDD-XXXX)
│   ├── assignments/                # Work order delegation, field officer workload balancer
│   ├── workflow/                   # Finite-state machine transition engine with security guards
│   ├── sla/                        # Dynamic SLA policy engine, deadline calculation, breach alerts
│   ├── escalations/                # Multi-tier escalation engine (Supervisor -> Head -> Commissioner)
│   ├── attachments/                # Evidence pipeline (Submission, Before, During, After repair)
│   ├── communications/             # Public dialogue & internal departmental notes timeline
│   ├── feedback/                   # Post-resolution citizen satisfaction scoring & auto-reopen
│   ├── notifications/              # In-app alert center with priority dispatch
│   ├── audit/                      # Immutable compliance audit log recording all mutations
│   ├── analytics/                  # Grievance density heatmaps, resolution velocities, KPIs
│   ├── reports/                    # CSV exporter & print-ready executive certified audits
│   └── dashboard/                  # Unified role routers for Citizen, Staff, Manager, Admin, Public
├── templates/                      # Clean component-based HTML templates
├── static/                         # Custom CSS design system and JavaScript utilities
└── tests/                          # Automated unit and integration test suite
```

---

## 👥 Role-Based Access Control (RBAC)

CivicFlow provides four specialized operational portals:

1. **Citizen Portal (`CITIZEN`)**:
   - Register and manage resident verification credentials.
   - File civic complaints with category, subcategory, GPS coordinates, and photographic evidence.
   - Track docket progression in real-time via status badges and SLA clocks.
   - Communicate directly with assigned field engineers.
   - Verify completed repairs: accept to close docket with CSAT rating, or reject with cause to automatically reopen and escalate.

2. **Municipal Staff Workspace (`STAFF`)**:
   - Inspect assigned work orders filtered by urgency and deadline.
   - Accept or decline delegated assignments with justification.
   - Commence on-site field investigation and upload stage evidence (*Before-Work*, *During-Work*, *After-Resolution*).
   - Advance dockets through permitted statuses (`Investigation` &rarr; `Work In Progress` &rarr; `Resolved`).
   - Request additional citizen information or record internal departmental notes.

3. **Department Manager Console (`MANAGER`)**:
   - Oversee departmental queues, backlog velocity, and resolution percentages.
   - Delegate complaints to field crews with real-time workload visibility.
   - Monitor SLA deadlines and intervene before threshold breaches.
   - Review and resolve escalations triggered by SLA breaches or citizen rejections.
   - Generate departmental performance audits.

4. **System Administration Hub (`ADMIN`)**:
   - Configure municipal departments, geographic zones, wards, and postal areas.
   - Onboard municipal personnel and manage clearance roles.
   - Formulate dynamic SLA resolution policies and warning thresholds.
   - Audit immutable security logs tracking all mutations, logins, and transitions.

5. **Public Transparency Portal (Unauthenticated)**:
   - Access non-PII open municipal data dashboards.
   - Review resolution indices by ward and category.
   - Track any public grievance using its unique docket reference number.

---

## 🔄 Complaint Lifecycle State Machine

Transitions are governed by an immutable finite-state machine with role-based clearance guards:

```
[SUBMITTED]
    │
    ├──► [UNDER_REVIEW] ──► [VERIFIED] ──► [ASSIGNED]
    │          │                               │
    │          ▼                               ▼
    │     [REJECTED]                     [INVESTIGATION]
    │     [DUPLICATE]                          │
    │                                          ▼
    │                                  [WORK_IN_PROGRESS]
    │                                          │
    │                                          ▼
    │                                     [RESOLVED]
    │                                          │
    │                                          ▼
    │                              [CITIZEN_VERIFICATION]
    │                                    │          │
    │                            (Accepted)        (Rejected)
    │                                    ▼          ▼
    │                                 [CLOSED]   [REOPENED]
    │                                               │
    ▼                                               ▼
[ESCALATED] ◄───────────────────────────────────────┘
```

---

## ⏱️ Service Level Agreement (SLA) Engine

- **Policy Matrix**: Target resolution windows are configured based on Department, Category, Priority, and Severity.
  - `CRITICAL`: 12 Hours (Response within 2h)
  - `HIGH`: 24 Hours (Response within 4h)
  - `MEDIUM`: 48 Hours (Response within 12h)
  - `LOW`: 96 Hours (Response within 24h)
- **Status Calculations**:
  - `ON_TRACK`: Remaining time > 25% of SLA window.
  - `DUE_SOON`: Remaining time &le; 25% of SLA window.
  - `BREACHED`: Deadline expired without resolution.
  - `MET_WITHIN_SLA` / `MET_AFTER_SLA`: Computed on resolution timestamp.

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- Python 3.11 or higher
- Git

### 2. Setup Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env` or use system defaults:
```bash
cp .env.example .env
```

### 5. Apply Migrations
```bash
python manage.py migrate
```

### 6. Seed Realistic Municipal Demo Data
```bash
python manage.py seed_municipal_data
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your browser.

---

## 🔑 Pre-Configured Demo Credentials

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin` | `admin123` | Full administration & security audit |
| **Manager (PWD)** | `manager_pwd` | `manager123` | Public Works department manager |
| **Manager (SWM)** | `manager_swm` | `manager123` | Sanitation & Solid Waste manager |
| **Manager (WSS)** | `manager_wss` | `manager123` | Water Supply & Sewerage manager |
| **Manager (ESL)** | `manager_esl` | `manager123` | Electrical & Street Lighting manager |
| **Field Officer** | `staff_pwd_1` | `staff123` | PWD Field engineer |
| **Field Officer** | `staff_swm_1` | `staff123` | Sanitation field supervisor |
| **Citizen** | `citizen_john` | `citizen123` | Resident of Ward 1 |
| **Citizen** | `citizen_jane` | `citizen123` | Resident of Ward 2 |

---

## 🛠️ Management Commands

CivicFlow includes purpose-built operational management commands:

1. **Seed Municipal Data**:
   ```bash
   python manage.py seed_municipal_data
   ```
2. **Audit SLA Breaches & Send Due-Soon Alerts**:
   ```bash
   python manage.py check_sla_breaches --auto-escalate
   ```
3. **Process Inactive & Reopened Escalations**:
   ```bash
   python manage.py process_escalations
   ```
4. **Compile Executive Performance Audit Summary**:
   ```bash
   python manage.py generate_civic_reports
   ```

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
python manage.py test
```

Test coverage includes:
- Authentication, role clearance, and RBAC matrix
- Complaint submission, numbering, and uniqueness
- State machine transition rules and guard validation
- SLA deadline calculations and breach detection
- Staff delegation, acceptance, rejection, and workload stats
- Citizen feedback scoring, resolution acceptance, and reopening

---

## 🔒 Security & Compliance

- **Immutable Audit Logging**: Every status transition, user login, delegation change, and upload is permanently logged with IP address and user agent in `AuditLog`.
- **Private Attachments**: Staff-only internal evidence and notes are strictly hidden from citizens at both template and view controller levels.
- **Upload Hardening**: Mime-type and file extension validation (`.jpg`, `.jpeg`, `.png`, `.pdf`, `.doc`, `.docx`, `.txt`) with a 10MB size cap and sanitized randomized filenames.
- **Data Isolation**: Citizens cannot access other citizens' dockets; staff can only access departmental queues.

---

## 📄 License
This project is licensed under the MIT License.
