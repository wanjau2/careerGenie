# Career Genie Backend API

A Flask-based REST API for the Career Genie job matching application with swipe functionality, user authentication, and subscription management.

## Features

- **User Authentication** - JWT-based auth with register/login
- **Profile Management** - User profiles with preferences and skills
- **Job Matching** - Smart job recommendations based on user preferences
- **Swipe Tracking** - Tinder-style swipe functionality with limits
- **Subscription System** - Free, Premium, and Enterprise plans
- **File Uploads** - Profile pictures and resume management
- **Application Tracking** - Track job applications and status
- **Rate Limiting** - Protect against abuse
- **CORS Support** - Ready for frontend integration

## Tech Stack

- **Framework**: Flask 3.0
- **Database**: MongoDB (via PyMongo)
- **Authentication**: JWT (Flask-JWT-Extended)
- **File Processing**: Pillow (image optimization)
- **Rate Limiting**: Flask-Limiter
- **CORS**: Flask-CORS
- **Production Server**: Gunicorn

## Prerequisites

- Python 3.9+
- MongoDB Atlas account (or local MongoDB)
- pip package manager

## Quick Start

### 1. Clone and Setup

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

**Important environment variables:**

```env
# MongoDB Connection
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/career_genie

# JWT Secret (change this!)
JWT_SECRET_KEY=your-super-secret-key-here

# Flask Configuration
FLASK_ENV=development
DEBUG=True
PORT=8000
```

### 3. Initialize Database

The database will be automatically initialized on first run, including:
- Collection creation
- Index setup for performance
- Unique constraints

### 4. Run Development Server

```bash
python app.py
```

Server will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/api/docs`

## API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login user | No |
| POST | `/api/auth/refresh` | Refresh access token | Refresh Token |
| GET | `/api/auth/me` | Get current user | Yes |
| POST | `/api/auth/logout` | Logout user | Yes |

### User Profile

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/user/profile` | Get user profile | Yes |
| PUT | `/api/user/profile` | Update profile | Yes |
| PUT | `/api/user/preferences` | Update job preferences | Yes |
| GET | `/api/user/subscription/status` | Get subscription info | Yes |
| POST | `/api/user/subscription/upgrade` | Upgrade plan | Yes |
| DELETE | `/api/user/account` | Deactivate account | Yes |

### Jobs

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/jobs` | Get recommended jobs | Yes |
| GET | `/api/jobs/<id>` | Get job details | Yes |
| POST | `/api/jobs/<id>/swipe` | Swipe on job | Yes |
| GET | `/api/jobs/liked` | Get liked jobs | Yes |
| GET | `/api/jobs/history` | Get swipe history | Yes |
| POST | `/api/jobs/<id>/apply` | Apply to job | Yes |
| GET | `/api/jobs/applications` | Get applications | Yes |
| GET | `/api/jobs/search` | Search jobs | Yes |

### Files

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/files/upload-avatar` | Upload profile picture | Yes |
| POST | `/api/files/upload-resume` | Upload resume | Yes |
| POST | `/api/files/upload-document` | Upload document | Yes |
| DELETE | `/api/files/delete` | Delete file | Yes |

## Example API Calls

### Register User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123",
    "firstName": "John",
    "lastName": "Doe"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123"
  }'
```

### Get Jobs (with auth)

```bash
curl -X GET http://localhost:8000/api/jobs \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Swipe on Job

```bash
curl -X POST http://localhost:8000/api/jobs/<JOB_ID>/swipe \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "like", "matchScore": 0.85}'
```

### Upload Profile Picture

```bash
curl -X POST http://localhost:8000/api/files/upload-avatar \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

## Subscription Plans

| Plan | Swipes/Day | Price |
|------|-----------|-------|
| Free | 50 | $0 |
| Premium | 500 | TBD |
| Enterprise | Unlimited | TBD |

Swipes reset daily at midnight UTC.

## Database Schema

### Users Collection
```javascript
{
  email: String (unique),
  password_hash: String,
  profile: {
    firstName: String,
    lastName: String,
    phone: String,
    location: {city, state, coordinates},
    profilePicture: String,
    resume: String,
    skills: [String],
    experience: String,
    expectedSalary: {min, max}
  },
  preferences: {
    jobTypes: [String],
    industries: [String],
    roleLevels: [String],
    remoteOnly: Boolean
  },
  subscription: {
    plan: String,
    swipesUsed: Number,
    swipeLimit: Number,
    resetDate: Date
  }
}
```

### Jobs Collection
```javascript
{
  title: String,
  company: {name, logo, website, industry},
  description: String,
  requirements: [String],
  salary: {min, max, currency},
  location: {city, state, remote, coordinates},
  employment: {type, level, department},
  benefits: [String],
  isActive: Boolean
}
```

### Swipes Collection
```javascript
{
  userId: ObjectId,
  jobId: ObjectId,
  action: String (like/dislike/superlike),
  timestamp: Date,
  matchScore: Number
}
```

## Development

### Project Structure

```
backend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Railway/Heroku config
├── railway.toml          # Railway-specific config
├── config/
│   ├── database.py       # MongoDB connection
│   └── settings.py       # App configuration
├── models/
│   ├── user.py          # User model
│   ├── job.py           # Job model
│   └── swipe.py         # Swipe/Application models
├── routes/
│   ├── auth.py          # Auth endpoints
│   ├── users.py         # User endpoints
│   ├── jobs.py          # Job endpoints
│   └── files.py         # File upload endpoints
├── services/
│   ├── auth_service.py  # Auth business logic
│   └── file_service.py  # File handling
├── utils/
│   ├── validators.py    # Input validation
│   └── helpers.py       # Utility functions
└── uploads/             # File storage
    ├── profiles/
    ├── resumes/
    └── documents/
```

### Adding New Features

1. Create model in `models/`
2. Create service in `services/` (business logic)
3. Create routes in `routes/`
4. Register blueprint in `app.py`
5. Update this README

### Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

## Deployment

### Railway Deployment

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and link project:
```bash
railway login
railway link
```

3. Set environment variables:
```bash
railway variables set MONGODB_URI=your_mongodb_uri
railway variables set JWT_SECRET_KEY=your_secret_key
railway variables set FLASK_ENV=production
```

4. Deploy:
```bash
railway up
```

### Environment Variables for Production

```env
MONGODB_URI=<your_mongodb_atlas_connection_string>
JWT_SECRET_KEY=<strong_random_secret>
FLASK_ENV=production
DEBUG=False
PORT=8000
MAX_CONTENT_LENGTH=16777216
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

## Security Best Practices

- ✅ JWT authentication with expiring tokens
- ✅ Password hashing with bcrypt
- ✅ Rate limiting on sensitive endpoints
- ✅ Input validation on all endpoints
- ✅ File upload validation and size limits
- ✅ CORS configuration for specific origins
- ✅ Environment-based configuration

## Monitoring & Logs

Logs are stored in `logs/career_genie.log` with automatic rotation (10MB max, 10 backups).

Monitor health at: `/health`

## Troubleshooting

### Database Connection Issues

- Verify `MONGODB_URI` in `.env`
- Check MongoDB Atlas IP whitelist
- Ensure network connectivity

### JWT Token Errors

- Verify `JWT_SECRET_KEY` matches between deployments
- Check token expiration time
- Ensure Bearer token format: `Bearer <token>`

### File Upload Issues

- Check `MAX_CONTENT_LENGTH` setting
- Verify `uploads/` directory permissions
- Ensure supported file types

## Support

For issues, questions, or contributions, please open an issue or contact the development team.

## License

Proprietary - Career Genie © 2024
