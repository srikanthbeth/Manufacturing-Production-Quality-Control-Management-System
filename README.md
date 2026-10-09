# Manufacturing Production & Quality Control Management System

**Project Type:** Advanced Backend Development
**Framework:** FastAPI
**Language:** Python 3.11+

---

## Project Overview

The Manufacturing Production & Quality Control Management System is a RESTful backend application developed using FastAPI and PostgreSQL. It helps manufacturing organizations manage production planning, inventory, machines, workers, quality inspections, defects, maintenance, and operational reporting.

The application demonstrates real-world backend development concepts, including authentication, role-based access control, database relationships, validation, business logic, inventory transactions, production workflows, and automated testing.

## Technology Stack

* Python 3.11+
* FastAPI
* Pydantic
* SQLAlchemy
* PostgreSQL
* JWT Authentication
* Alembic
* Pytest
* Uvicorn
* Swagger UI / OpenAPI

## Key Features

### 1. Authentication and Authorization

* User registration and login
* JWT access and refresh tokens
* Password hashing
* Role-based access control (RBAC)
* Protected API endpoints

### 2. Plant Management

* Create, retrieve, update, and manage manufacturing plants
* Plant status and production capacity
* Plant manager assignment

### 3. Production Line Management

* Production line creation and updates
* Line capacity and status management
* Plant and supervisor assignment
* Search, filtering, and pagination where implemented

### 4. Product and Bill of Materials (BOM)

* Product master management
* SKU and product details
* BOM creation and management
* Raw material requirements for production

### 5. Raw Material and Inventory Management

* Raw material master records
* Stock-in and stock-out operations
* Material consumption tracking
* Inventory movement history
* Stock adjustments
* Before-and-after stock tracking

### 6. Machine Management

* Machine registration and updates
* Production line assignment
* Machine status tracking
* Machine usage and downtime monitoring

### 7. Production Order Management

* Production order creation and updates
* Product and quantity assignment
* Priority and target date management
* Production order status transitions

### 8. Production Batch Management

* Batch creation and updates
* Planned, produced, and rejected quantities
* Completion percentage
* Rejection percentage
* Production efficiency tracking

### 9. Worker Management

* Worker records and employee codes
* Skill and department tracking
* Production line assignment
* Worker-to-batch assignments

### 10. Shift Management

* Shift creation and management
* Worker-to-shift assignments
* Shift production output recording
* Machine usage recording
* Shift performance reporting

### 11. Quality Inspection

* Quality inspection records
* Inspection parameters
* Expected and actual values
* Inspection result tracking

### 12. Defect Management

* Defect registration
* Defect type and severity
* Quantity affected
* Root cause analysis
* Corrective action tracking
* Resolution status

### 13. Machine Maintenance

* Preventive maintenance scheduling
* Maintenance status tracking
* Technician assignment
* Scheduled and next-due dates
* Maintenance cost tracking
* Spare parts recording

### 14. Dashboard and Reporting

* Production order summaries
* Daily and monthly production metrics
* Production efficiency
* Machine utilization and downtime
* Rejection statistics
* Quality metrics
* Defect statistics
* Inventory and maintenance indicators

### 15. API Documentation

* Interactive Swagger UI
* Request and response schemas
* Input validation
* HTTP status codes and error responses

---

## Project Setup

### Prerequisites

* Python 3.11 or later
* PostgreSQL
* Git
* Visual Studio Code (recommended)

### 1. Clone the Repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd manufacturing_production_quality
```

Replace the placeholder with your actual repository URL.

### 2. Create a Virtual Environment

```powershell
python -m venv venv
```

Activate the environment in Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and configure your database and security settings.

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:<YOUR_PASSWORD>@localhost:5433/manufacturing_production_quality
SECRET_KEY=<YOUR_SECRET_KEY>
```

Replace placeholders with your actual values. Never commit passwords, secret keys, or access tokens to source control.

### 5. Apply Database Migrations

If Alembic is configured:

```powershell
python -m alembic upgrade head
```

### 6. Start the Application

```powershell
python -m uvicorn main:app --reload
```

The command assumes the FastAPI instance is named `app` in `main.py`.

## Application URLs

| Resource     | URL                         |
| ------------ | --------------------------- |
| API Base URL | http://127.0.0.1:8000       |
| Swagger UI   | http://127.0.0.1:8000/docs  |
| ReDoc        | http://127.0.0.1:8000/redoc |

---

## Automated Testing

The project test suite has been reported as successfully completed with **559 passing tests**.

Run the complete test suite from the project root:

```powershell
python -m pytest -v -s
```

Run integration tests:

```powershell
python -m pytest tests/integration -v -s
```

Run an individual test module:

```powershell
python -m pytest tests/integration/test_auth.py -v -s
```

### Test Coverage Areas

The automated tests cover the application's implemented behavior across areas such as:

* Authentication and authorization
* User roles and access restrictions
* Plant and production line management
* Product and BOM operations
* Raw material and inventory management
* Machine management
* Production orders and batches
* Worker assignments
* Shift management and production output
* Quality inspections
* Defect tracking
* Machine maintenance
* Dashboard and reporting
* Request validation and error handling

### Test Result

```text
Test Suite: Manufacturing Production & Quality Control Management System
Framework: Pytest
Reported Result: 559 passed
Failed Tests: 0 reported
```

---

## Successfully Verified Manual API Workflow

The following API operations were manually verified through Swagger UI.

| Operation                         | Endpoint                                   | HTTP Status |
| --------------------------------- | ------------------------------------------ | ----------: |
| Update production order status    | `PATCH /api/v1/production-orders/3/status` |         200 |
| Update production batch           | `PUT /api/v1/production-batches/3`         |         200 |
| Assign worker to production batch | `POST /api/v1/workers/2/batches/3`         |         201 |
| Create shift                      | `POST /api/v1/shifts`                      |         201 |
| Assign worker to shift            | `POST /api/v1/shifts/2/workers/2`          |         201 |
| Record shift production output    | `POST /api/v1/shifts/2/production-output`  |         201 |
| Record shift machine usage        | `POST /api/v1/shifts/2/machine-usage`      |         201 |
| Create quality inspection         | `POST /api/v1/quality-inspections`         |         201 |
| Create defect record              | `POST /api/v1/defects`                     |         201 |
| Create inventory movement         | `POST /api/v1/inventory-movements`         |         201 |
| Schedule machine maintenance      | `POST /api/v1/maintenance`                 |         201 |
| Generate dashboard                | `GET /api/v1/dashboard`                    |         200 |

**HTTP status codes:** `200 OK` indicates a successful request, while `201 Created` indicates a resource was created successfully.

## Verified Production Workflow

The manual workflow demonstrated these operations:

1. Authenticate as an authorized user.
2. Create and configure a plant.
3. Create a production line.
4. Register products and define a BOM.
5. Register raw materials and machines.
6. Create a production order.
7. Update the production order status.
8. Create and update a production batch.
9. Assign workers and shifts.
10. Record production output and machine usage.
11. Create a quality inspection and defect record.
12. Record material consumption.
13. Schedule preventive machine maintenance.
14. Generate the dashboard.
15. Continue with available reports and audit log verification.

## Verified Production Batch

| Field                 | Value            |
| --------------------- | ---------------- |
| Batch Number          | `BATCH-2026-001` |
| Production Order ID   | 3                |
| Planned Quantity      | 100              |
| Produced Quantity     | 20               |
| Rejected Quantity     | 1                |
| Completion Percentage | 20%              |
| Rejection Percentage  | 5%               |
| Production Line ID    | 2                |
| Machine ID            | 3                |

## Verified Inventory Transaction

| Field              | Value                |
| ------------------ | -------------------- |
| Transaction Number | `INV-8F4A8B78CF`     |
| Raw Material ID    | 1                    |
| Movement Type      | Material Consumption |
| Quantity Consumed  | 40 kg                |
| Stock Before       | 500 kg               |
| Stock After        | 460 kg               |
| Reference Number   | `BATCH-2026-001`     |

## Verified Maintenance Record

| Field              | Value            |
| ------------------ | ---------------- |
| Maintenance Number | `MNT-2026-001`   |
| Machine ID         | 3                |
| Maintenance Type   | Preventive       |
| Status             | Scheduled        |
| Scheduled Date     | October 10, 2026 |
| Next Due Date      | January 10, 2027 |
| Maintenance Cost   | 0.00             |

## Dashboard Verification

The dashboard endpoint returned HTTP 200 during manual verification.

| Metric                   | Reported Value |
| ------------------------ | -------------: |
| Total Production Orders  |              3 |
| Active Production Orders |              1 |
| Completed Orders         |              1 |
| Daily Production         |    1,020 units |
| Production Efficiency    |         64.67% |
| Machine Utilization      |         99.01% |
| Machine Downtime         |            120 |
| Rejection Rate           |          5.64% |
| Quality Pass Percentage  |             0% |
| Recorded Defect Types    |              1 |

These figures reflect the dashboard response during manual testing. They should be interpreted according to the application's aggregation logic.

## Error Handling and Validation

The API validates request data and rejects unsupported values.

For example, an invalid inventory movement type returned HTTP 422 with a validation message listing the permitted values:

* `Raw Material Receipt`
* `Material Consumption`
* `Finished Goods Production`
* `Rejected Goods`
* `Stock Adjustment`

After correcting the movement type to `Material Consumption`, the inventory movement was created successfully with HTTP 201.

## Security

* Store secrets in environment variables.
* Do not commit `.env` files or JWT tokens.
* Use secure password hashing.
* Enforce role-based authorization.
* Validate incoming request data.
* Use a separate test database for automated tests.

## Future Enhancements

* Additional end-to-end workflow tests
* Expanded production and quality analytics
* Automated low-stock alerts
* Maintenance notifications
* Docker deployment
* CI/CD integration
* Enhanced audit log reporting

## Conclusion

The Manufacturing Production & Quality Control Management System provides a FastAPI backend for manufacturing operations, including production planning, inventory consumption, workforce and shift management, quality control, defect tracking, preventive maintenance, and operational dashboards.

The project has a reported automated test result of **559 passed tests**, alongside manually verified API operations documented above.

## Author

**Srikanth Bethamcharla**

---

*Manufacturing Production & Quality Control Management System — FastAPI Backend Project*
