# Fleet Reporting and Analytics System (fras) - Backend

A robust FastAPI backend for managing fleet data with file upload, authentication, and analytics capabilities.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control (Admin/User)
- **Fleet Data Management**: CRUD operations for fleet records
- **File Upload**: Bulk import via CSV/Excel files with data validation and cleaning
- **Excel Export**: Generate formatted summary reports
- **RESTful API**: Well-documented API endpoints with OpenAPI/Swagger documentation
- **Database**: PostgreSQL with SQLAlchemy ORM
- **CORS Support**: Configured for frontend integration

## Project Structure

```
backend/
├── app/
│   ├── routers/          # API route handlers
│   │   ├── auth_routes.py
│   │   ├── fleet_routes.py
│   │   └── file_routes.py
│   ├── auth.py           # Authentication utilities
│   ├── config.py         # Configuration management
│   ├── crud.py           # Database operations
│   ├── database.py       # Database connection
│   ├── dependencies.py   # FastAPI dependencies
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   └── utils.py          # Utility functions
├── create_admin.py       # Script to create admin user
├── create_tables.py      # Script to initialize database
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Virtual environment tool (venv, virtualenv, or conda)

### Setup Steps

1. **Clone the repository** (if applicable)
   ```bash
   cd c:\Projects\FRAS\backend
   ```

2. **Create and activate virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Update the values according to your setup:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/fleetdb
   SECRET_KEY=your-super-secret-key-change-this
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

5. **Create database tables**
   ```powershell
   python create_tables.py
   ```

6. **Create admin user**
   ```powershell
   python create_admin.py
   ```

## Running the Application

### Development Mode

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/token` - Login and get access token

### Fleet Records
- `POST /fleet/` - Create a new fleet record (authenticated)
- `GET /fleet/` - Get all fleet records with pagination (authenticated)
- `DELETE /fleet/{record_id}` - Delete a fleet record (admin only)

### File Upload
- `POST /files/upload-summary` - Upload CSV/Excel files and get summary (admin only)

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Getting a Token

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

## File Upload Format

CSV/Excel files must contain the following columns:
- **Date**: Date in any parseable format
- **Fleet**: Fleet identifier (string)
- **Amount**: Numeric value

Example CSV:
```csv
Date,Fleet,Amount
2024-01-15,Fleet A,15000
2024-01-16,Fleet B,22000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 60 |

## Security Considerations

1. **Change default credentials**: Update the admin password after first login
2. **Use strong SECRET_KEY**: Generate a secure random key for production
3. **HTTPS in production**: Always use HTTPS in production environments
4. **Database security**: Use strong database passwords and restrict access
5. **Environment variables**: Never commit `.env` file to version control

## Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique)
- `hashed_password`
- `role` (admin/user)

### Fleet Records Table
- `id` (Primary Key)
- `date`
- `fleet`
- `amount`

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Add docstrings to all functions and classes

### Adding New Endpoints
1. Create route handler in appropriate file under `app/routers/`
2. Add Pydantic schemas in `app/schemas.py`
3. Add CRUD operations in `app/crud.py` if needed
4. Update this README with new endpoint documentation

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Verify `DATABASE_URL` in `.env` file
- Check database credentials and permissions

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Activate virtual environment

### Authentication Fails
- Verify admin user exists: run `python create_admin.py`
- Check JWT secret key is set in `.env`

## License

This project is proprietary. All rights reserved.

## Support

For issues and questions, please contact the development team.
