# Security Features

This document outlines the security features implemented in Command Center.

## Overview

Command Center implements multiple layers of security to protect sensitive data and prevent common vulnerabilities:

1. **JWT Authentication** - Token-based authentication for API access
2. **Encryption at Rest** - GitHub tokens encrypted in database using Fernet
3. **Rate Limiting** - Protection against brute-force and DoS attacks
4. **Security Headers** - HTTP headers to prevent XSS, clickjacking, and other attacks
5. **CORS Policy** - Strict allowlist-based CORS configuration
6. **Key Derivation** - PBKDF2-based key derivation for encryption keys

---

## 1. JWT Authentication

### Implementation
- **Location**: `backend/app/auth/`
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Token Types**: Access tokens (30 min) and Refresh tokens (7 days)

### Features
- Password hashing with bcrypt (via passlib)
- Separate access and refresh tokens
- User model with role-based access (active/inactive, superuser)
- Protected endpoints using dependency injection

### Usage
```python
from app.auth import require_auth

@router.get("/protected")
async def protected_route(user: User = Depends(require_auth)):
    return {"message": f"Hello {user.email}"}
```

### Endpoints
- `POST /api/v1/auth/register` - User registration (rate limited: 5/hour)
- `POST /api/v1/auth/login` - User login (rate limited: 10/minute)
- `POST /api/v1/auth/refresh` - Refresh access token (rate limited: 20/minute)
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - Logout (client-side token discard)

---

## 2. Encryption at Rest

### GitHub Token Encryption
- **Algorithm**: Fernet (symmetric encryption)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Implementation**: `backend/app/utils/crypto.py`

### How It Works
```python
# Tokens are automatically encrypted when saved
repository.access_token = "ghp_plain_token_here"
# Stored encrypted in database

# Tokens are automatically decrypted when accessed
plain_token = repository.access_token
# Returns decrypted token
```

### Configuration
Two environment variables are required:
- `SECRET_KEY` - Base secret for key derivation
- `ENCRYPTION_SALT` - Salt for PBKDF2 (must remain constant)

**⚠️ WARNING**: If `ENCRYPTION_SALT` changes, all encrypted tokens will become unrecoverable!

---

## 3. Rate Limiting

### Implementation
- **Library**: slowapi
- **Storage**: In-memory (consider Redis for production)
- **Strategy**: Fixed-window

### Default Limits
- Global: 100 requests/minute, 1000 requests/hour
- Auth endpoints have stricter limits (see JWT Authentication section)

### Custom Rate Limiting
```python
from app.middleware import limiter

@router.get("/endpoint")
@limiter.limit("50/minute")
async def rate_limited_endpoint(request: Request):
    return {"message": "Limited to 50 requests per minute"}
```

---

## 4. Security Headers

### Headers Applied
- **X-Content-Type-Options**: `nosniff` - Prevent MIME sniffing
- **X-Frame-Options**: `DENY` - Prevent clickjacking
- **X-XSS-Protection**: `1; mode=block` - Enable XSS protection
- **Strict-Transport-Security**: Force HTTPS with 1-year max-age
- **Content-Security-Policy**: Restrictive CSP to prevent injection attacks
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **Permissions-Policy**: Disable unnecessary browser features

### Implementation
Security headers are automatically added to all responses via middleware.

---

## 5. CORS Configuration

### Security Features
- **Allowlist-based**: Only specified origins are allowed
- **Explicit methods**: Only necessary HTTP methods enabled
- **Explicit headers**: Only required headers allowed
- **Credentials**: Controlled via environment variable

### Configuration
Environment variables:
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `CORS_ALLOW_CREDENTIALS` - Allow credentials (default: true)
- `CORS_MAX_AGE` - Preflight cache duration (default: 600s)

### Default Allowed Origins
```
http://localhost:3000
http://localhost:5173
```

---

## 6. Key Derivation

### PBKDF2 Parameters
- **Algorithm**: HMAC-SHA256
- **Iterations**: 100,000
- **Key Length**: 32 bytes (256 bits)
- **Salt**: Unique per installation (from `ENCRYPTION_SALT`)

### Security Benefits
- **Variable-length secret support**: Any length `SECRET_KEY` is secure
- **Brute-force resistance**: 100,000 iterations slow down attacks
- **Salt protection**: Prevents rainbow table attacks

---

## Environment Variables

### Required Security Variables
```bash
# Core security
SECRET_KEY=<generate with: openssl rand -hex 32>
ENCRYPTION_SALT=<generate with: openssl rand -hex 32>

# CORS configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=600

# JWT configuration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Feature flags
ENCRYPT_TOKENS=true
```

### Generation Commands
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate ENCRYPTION_SALT
openssl rand -hex 32
```

---

## Database Migration

### Migration: `001_add_security_features`

This migration adds:
1. **users** table for authentication
2. Expanded `access_token` column in repositories (512 → 1024 chars)

### Running Migration
```bash
cd backend
alembic upgrade head
```

---

## Testing

### Test Coverage
- Password hashing and verification
- JWT token creation and validation
- User registration and login
- Token refresh flow
- Token encryption/decryption
- Protected endpoint access

### Running Tests
```bash
cd backend
pytest tests/test_auth.py -v
```

---

## Production Recommendations

1. **Rate Limiting Storage**
   - Use Redis instead of in-memory storage
   - Update `storage_uri` in `middleware/rate_limit.py`

2. **Token Blacklisting**
   - Implement Redis-based token blacklist for logout
   - Track revoked tokens to prevent reuse

3. **HTTPS Only**
   - Ensure all traffic uses HTTPS in production
   - Configure reverse proxy (nginx/traefik) for SSL termination

4. **Environment Security**
   - Never commit `.env` files
   - Use secret management (AWS Secrets Manager, Vault, etc.)
   - Rotate `SECRET_KEY` and `ENCRYPTION_SALT` periodically (requires token re-encryption)

5. **Monitoring**
   - Log authentication failures
   - Monitor rate limit violations
   - Alert on suspicious activity

6. **Database Security**
   - Use strong PostgreSQL passwords
   - Enable SSL for database connections
   - Regular backups with encrypted storage

---

## Compliance

### OWASP Top 10 Coverage

- ✅ **A01: Broken Access Control** - JWT authentication with role-based access
- ✅ **A02: Cryptographic Failures** - PBKDF2 key derivation, Fernet encryption
- ✅ **A03: Injection** - SQLAlchemy ORM prevents SQL injection, CSP headers
- ✅ **A05: Security Misconfiguration** - Security headers, explicit CORS
- ✅ **A07: Identification and Authentication Failures** - Secure password hashing, JWT tokens

---

## Security Contacts

For security vulnerabilities, please contact:
- Email: security@example.com
- Create a private security advisory on GitHub

**DO NOT** open public issues for security vulnerabilities.
