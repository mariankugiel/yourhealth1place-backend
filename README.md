# YourHealth1Place FastAPI Backend

A secure, scalable YourHealth1Place API built with FastAPI, implementing a modern multi-service architecture for handling sensitive health data.

## 🏗️ Architecture Overview

This application follows a secure multi-service architecture:

### **Supabase** - Authentication & User Management
- **Authentication**: Email/password, OAuth providers
- **Personal Information**: Name, contact details, emergency contacts
- **Lightweight Metadata**: User settings, preferences, non-sensitive profile data

### **AWS** - Sensitive Health Data Storage
- **S3**: Encrypted storage for lab reports, wearable metrics, AI summaries
- **Athena**: Analytics and querying of health data access logs
- **Akeyless**: External encryption key management

### **Akeyless (AKS)** - Encryption Key Management
- **Centralized Key Storage**: All encryption keys for Supabase and AWS
- **Secure Access**: No hardcoded keys - each request fetches keys securely
- **Audit Logging**: Complete access logging for compliance

### **Internal Database** - Linkage & Metadata
- **User Linkage**: Internal `user_id` for secure cross-service mapping
- **Metadata Storage**: Non-sensitive operational data
- **Audit Trails**: Access logs and compliance tracking

## 🚀 Features

- **Secure Authentication** via Supabase
- **Encrypted Health Data Storage** in AWS S3
- **Centralized Key Management** with Akeyless
- **Analytics & Reporting** via AWS Athena
- **Role-based Access Control**
- **Comprehensive Audit Logging**
- **HIPAA Compliance Ready**
- **RESTful API Design**
- **Async Operations**
- **Comprehensive Error Handling**

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (for metadata and linkage)
- **Authentication**: Supabase Auth
- **Storage**: AWS S3 (encrypted)
- **Analytics**: AWS Athena
- **Key Management**: Akeyless
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Documentation**: OpenAPI/Swagger

## 📁 Project Structure

```
fastapi-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py          # Supabase authentication
│   │       │   ├── users.py         # User management
│   │       │   ├── patients.py      # Patient profiles
│   │       │   ├── health_records.py # Health data (AWS S3)
│   │       │   ├── medications.py   # Medication data (AWS S3)
│   │       │   └── messages.py      # Secure messaging
│   │       └── api.py
│   ├── core/
│   │   ├── config.py               # Configuration settings
│   │   ├── database.py             # Database connection
│   │   ├── supabase_client.py      # Supabase integration
│   │   ├── aws_service.py          # AWS S3/Athena integration
│   │   └── akeyless_service.py     # Akeyless key management
│   ├── crud/
│   │   ├── user.py                 # User CRUD operations
│   │   └── patient.py              # Patient CRUD operations
│   ├── models/
│   │   ├── user.py                 # User model (linkage only)
│   │   ├── patient.py              # Patient model (metadata only)
│   │   ├── health_record.py        # Health record metadata
│   │   ├── medication.py           # Medication metadata
│   │   └── message.py              # Message model
│   └── schemas/
│       ├── user.py                 # User Pydantic schemas
│       ├── patient.py              # Patient Pydantic schemas
│       ├── health_record.py        # Health record schemas
│       ├── medication.py           # Medication schemas
│       └── message.py              # Message schemas
├── requirements.txt
├── env.example
├── alembic.ini
└── run.py
```

## 🚀 Installation

### **Option 1: Local Development Setup**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fastapi-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual configuration values
   ```

5. **Set up services**

   **Supabase Setup:**
   - Create a Supabase project
   - Get your project URL and API keys
   - Create tables: `user_profiles`, `user_settings`

   **AWS Setup:**
   - Create S3 bucket for health data
   - Set up Athena database and workgroup
   - Configure IAM permissions
   - Enable Akeyless encryption

   **Akeyless Setup:**
   - Create Akeyless account
   - Set up access credentials
   - Create encryption keys for different data types

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the application**
   ```bash
   python run.py
   ```

### **Option 2: Terraform Cloud Deployment (Recommended)**

1. **Set up Terraform Cloud**
   - Create account at [https://app.terraform.io/](https://app.terraform.io/)
   - Create organization: "YourHealth1Place"
   - Create workspaces: `yourhealth1place-dev`, `yourhealth1place-stage`, `yourhealth1place-prod`

2. **Configure AWS credentials**
   - Add AWS credentials as environment variables in each workspace
   - Set up cost estimation and notifications

3. **Deploy infrastructure**
   ```bash
   # Using the deployment script
   ./terraform/deploy-cloud.sh dev    # Deploy development
   ./terraform/deploy-cloud.sh stage  # Deploy staging
   ./terraform/deploy-cloud.sh prod   # Deploy production
   
   # Or on Windows
   terraform\deploy-cloud.bat dev
   ```

4. **Access the application**
   - Get the EC2 public IP from Terraform Cloud outputs
   - Access the API at `http://<EC2_IP>/docs`

## 🔧 Configuration

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET=yourhealth1place-sensitive-data
AWS_ATHENA_DATABASE=yourhealth1place_analytics
AWS_ATHENA_WORKGROUP=primary

# Akeyless Configuration
AKEYLESS_ACCESS_ID=your-akeyless-access-id
AKEYLESS_ACCESS_KEY=your-akeyless-access-key
AKEYLESS_URL=https://api.akeyless.io

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/yourhealth1place_db

# Security Configuration
SECRET_KEY=your-secret-key-here
```

## 📚 API Documentation

Once the application is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔐 Security Features

### Data Separation
- **Authentication data**: Stored in Supabase
- **Personal information**: Stored in Supabase
- **Sensitive health data**: Encrypted and stored in AWS S3
- **Encryption keys**: Managed by Akeyless

### Access Control
- **Role-based permissions**: Patient, Doctor, Admin
- **Token-based authentication**: JWT tokens via Supabase
- **Secure key retrieval**: No hardcoded keys
- **Audit logging**: All access attempts logged

### Encryption
- **Data at rest**: AES-256 encryption with Akeyless keys
- **Data in transit**: TLS/SSL encryption
- **Key management**: Centralized in Akeyless
- **Key rotation**: Automated key rotation support

## 🏥 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

### Users
- `GET /api/v1/users/` - List users (Admin only)
- `GET /api/v1/users/{user_id}` - Get user details
- `PUT /api/v1/users/{user_id}` - Update user info
- `DELETE /api/v1/users/{user_id}` - Delete user (Admin only)

### Patients
- `POST /api/v1/patients/` - Create patient profile
- `GET /api/v1/patients/` - List patients (Admin/Doctor)
- `GET /api/v1/patients/{patient_id}` - Get patient details
- `PUT /api/v1/patients/{patient_id}` - Update patient profile
- `DELETE /api/v1/patients/{patient_id}` - Delete patient (Admin only)

### Health Records
- `POST /api/v1/health-records/` - Create health record (AWS S3)
- `GET /api/v1/health-records/` - List health records
- `GET /api/v1/health-records/{record_id}` - Get health record with data
- `PUT /api/v1/health-records/{record_id}` - Update health record
- `DELETE /api/v1/health-records/{record_id}` - Delete health record

### Medications
- `POST /api/v1/medications/` - Create medication record (AWS S3)
- `GET /api/v1/medications/` - List medications
- `GET /api/v1/medications/{medication_id}` - Get medication details
- `PUT /api/v1/medications/{medication_id}` - Update medication
- `DELETE /api/v1/medications/{medication_id}` - Delete medication

## 🔄 Data Flow

1. **User Registration/Login**
   - User authenticates via Supabase
   - Internal user record created for linkage
   - Personal info stored in Supabase

2. **Health Data Storage**
   - Sensitive data encrypted with Akeyless keys
   - Stored in AWS S3 with metadata
   - Access logged for analytics

3. **Data Retrieval**
   - User authenticated via Supabase token
   - Internal user ID used for AWS access
   - Data decrypted and returned

4. **Analytics**
   - Access logs stored in S3
   - Queried via AWS Athena
   - Compliance reporting available

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t yourhealth1place-api .

# Run container
docker run -p 8000:8000 yourhealth1place-api
```

### Production Considerations
- Use production-grade database (RDS, etc.)
- Configure proper CORS origins
- Set up monitoring and logging
- Enable rate limiting
- Configure backup strategies
- Set up CI/CD pipelines

## 📊 Monitoring & Analytics

- **Health Data Access**: Logged via AWS S3/Athena
- **Key Access**: Logged via Akeyless
- **API Performance**: FastAPI built-in metrics
- **Error Tracking**: Comprehensive error logging

## 🔒 Compliance

This architecture is designed to support:
- **HIPAA Compliance**: Data separation and encryption
- **GDPR Compliance**: Data portability and deletion
- **SOC 2**: Security controls and audit trails
- **HITECH**: Health information technology standards

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

---

**Note**: This is a production-ready architecture designed for YourHealth1Place applications. Ensure all security configurations are properly set up before deployment. 