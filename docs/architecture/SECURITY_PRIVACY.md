# Security & Privacy Guide

## Overview

This document describes security measures and privacy controls implemented in the GeneWeb Python modernization project, following industry best practices for handling sensitive genealogical data.

---

## Security Principles

### 1. Defense in Depth
Multiple layers of security controls to protect against various attack vectors.

### 2. Least Privilege
Users and processes have only the minimum permissions needed.

### 3. Fail Secure
System fails in a secure state when errors occur.

### 4. Privacy by Design
Privacy controls built into the system from the start.

---

## Security Measures

### SQL Injection Protection

#### ✅ Current Implementation

**Using SQLAlchemy ORM**
```python
# SAFE - Parameterized queries via ORM
person = db.query(PersonORM).filter(PersonORM.id == person_id).first()

# SAFE - Prepared statements
query = db.query(PersonORM).filter(PersonORM.surname.like(f"%{search_term}%"))
```

#### ⚠️ Security Audit Findings

**From Bandit Scan:**
- No SQL injection vulnerabilities detected ✅
- All database queries use ORM or parameterized statements ✅

**Best Practices:**
```python
# NEVER do this (vulnerable):
# query = f"SELECT * FROM persons WHERE id = {user_input}"  # DANGEROUS!

# ALWAYS use ORM or parameterized queries:
person = session.query(PersonORM).filter(PersonORM.id == user_input).first()
```

---

### XSS (Cross-Site Scripting) Prevention

#### ✅ Current Implementation

**Jinja2 Auto-escaping**
```python
# templates.py
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(['html', 'xml'])  # Auto-escape by default
)
```

**Template Usage:**
```html
<!-- SAFE - Auto-escaped -->
<div>{{ person.first_name }}</div>

<!-- When raw HTML needed (use cautiously) -->
<div>{{ person.notes | safe }}</div>  <!-- Only for trusted admin content -->
```

#### 🎯 Recommendations

1. **Content Security Policy (CSP)**
```python
# Add to FastAPI app
from fastapi import FastAPI, Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:;"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

2. **Sanitize User Input**
```python
from bleach import clean

def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML tags."""
    allowed_tags = ['p', 'br', 'strong', 'em', 'u']
    return clean(text, tags=allowed_tags, strip=True)
```

---

### Authentication & Authorization

#### ⚠️ Current Issues (from Bandit)

**Hardcoded Credentials** (HIGH PRIORITY FIX)
```python
# ❌ INSECURE - Found in api.py
SECRET_KEY = "your-secret-key-here"  # Hardcoded
if username == "admin" and password == "admin":  # Hardcoded
```

#### ✅ Secure Implementation

**1. Environment Variables for Secrets**
```python
import os
from typing import Optional

# config.py
class Settings:
    """Application settings from environment variables."""
    
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost/geneweb"
    )

settings = Settings()
```

**2. Password Hashing**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

**3. Secure Token Generation**
```python
from jose import JWTError, jwt
from datetime import datetime, timedelta
import secrets

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "jti": secrets.token_urlsafe(32)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

---

### Role-Based Access Control (RBAC)

#### 🎯 Proposed Implementation

**1. Define User Roles**
```python
from enum import Enum
from typing import List

class Role(Enum):
    """User roles with different permissions."""
    ADMIN = "admin"           # Full access
    EDITOR = "editor"         # Can edit all records
    VIEWER = "viewer"         # Read-only access
    FAMILY_MEMBER = "member"  # Can view and edit family branch

class Permission(Enum):
    """Granular permissions."""
    VIEW_ALL = "view:all"
    VIEW_PUBLIC = "view:public"
    EDIT_ALL = "edit:all"
    EDIT_OWN_BRANCH = "edit:own_branch"
    DELETE_ALL = "delete:all"
    EXPORT_DATA = "export:data"
    IMPORT_DATA = "import:data"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.VIEW_ALL,
        Permission.EDIT_ALL,
        Permission.DELETE_ALL,
        Permission.EXPORT_DATA,
        Permission.IMPORT_DATA,
    ],
    Role.EDITOR: [
        Permission.VIEW_ALL,
        Permission.EDIT_ALL,
        Permission.EXPORT_DATA,
    ],
    Role.VIEWER: [
        Permission.VIEW_PUBLIC,
    ],
    Role.FAMILY_MEMBER: [
        Permission.VIEW_ALL,
        Permission.EDIT_OWN_BRANCH,
    ],
}
```

**2. Permission Checking**
```python
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Extract and validate current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_from_db(username)
    if user is None:
        raise credentials_exception
    return user

def require_permission(permission: Permission):
    """Dependency to check if user has required permission."""
    async def permission_checker(user: User = Depends(get_current_user)):
        if permission not in ROLE_PERMISSIONS.get(user.role, []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {permission.value} required"
            )
        return user
    return permission_checker

# Usage in routes:
@app.delete("/api/persons/{person_id}")
async def delete_person(
    person_id: int,
    user: User = Depends(require_permission(Permission.DELETE_ALL))
):
    # Only users with DELETE_ALL permission can access
    pass
```

---

### Privacy Controls

#### Living Individuals Protection

**EU GDPR Compliance**
```python
from datetime import date, timedelta

class PrivacyLevel(Enum):
    """Privacy levels for persons."""
    PUBLIC = "public"           # Deceased, fully public
    PRIVATE = "private"         # Living, private data
    SEMI_PRIVATE = "semi"       # Living, some data public

def is_person_living(person: Person) -> bool:
    """Determine if person is likely still living."""
    if person.death_event:
        return False  # Has death record
    
    if not person.birth_event or not person.birth_event.date:
        return True  # Unknown, assume living
    
    # Consider living if born less than 120 years ago
    birth_year = person.birth_event.date.year
    current_year = date.today().year
    return (current_year - birth_year) < 120

def get_privacy_level(person: Person) -> PrivacyLevel:
    """Determine privacy level for person."""
    if not is_person_living(person):
        return PrivacyLevel.PUBLIC
    
    # Apply access control for living individuals
    if person.access == "public":
        return PrivacyLevel.SEMI_PRIVATE  # Some info public
    else:
        return PrivacyLevel.PRIVATE  # All info private

def filter_person_data(person: Person, user: Optional[User]) -> Person:
    """Filter person data based on privacy level and user permissions."""
    privacy_level = get_privacy_level(person)
    
    if privacy_level == PrivacyLevel.PUBLIC:
        return person  # All data visible
    
    # Check user permissions
    if not user or Permission.VIEW_ALL not in ROLE_PERMISSIONS.get(user.role, []):
        # Redact private information
        filtered = person.copy()
        if privacy_level == PrivacyLevel.PRIVATE:
            filtered.first_name = "[Private]"
            filtered.surname = "[Private]"
            filtered.birth_event = None
            filtered.occupation = ""
        else:  # SEMI_PRIVATE
            # Show name but hide dates/events
            filtered.birth_event = None
            filtered.occupation = ""
        return filtered
    
    return person  # User has permission, show all
```

---

### Data Encryption

#### 🎯 Recommendations

**1. Database Encryption at Rest**
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_INITDB_ARGS: "--data-checksums"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # Use encrypted volumes in production
```

**2. Application-Level Encryption for Sensitive Fields**
```python
from cryptography.fernet import Fernet
import os

class EncryptedField:
    """Encrypt sensitive database fields."""
    
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY must be set")
        self.fernet = Fernet(key.encode())
    
    def encrypt(self, value: str) -> str:
        """Encrypt a string value."""
        return self.fernet.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt an encrypted value."""
        return self.fernet.decrypt(encrypted_value.encode()).decode()

# Usage:
encryptor = EncryptedField()
person.ssn = encryptor.encrypt(ssn)  # Store encrypted
actual_ssn = encryptor.decrypt(person.ssn)  # Retrieve decrypted
```

---

### File Upload Security

#### ⚠️ Current Issues (from Bandit)

**Insecure Temp Files** (MEDIUM PRIORITY FIX)
```python
# ❌ INSECURE - Found in api.py and webapp.py
temp_path = f"/tmp/{file.filename}"  # Predictable path, race conditions
```

#### ✅ Secure Implementation

```python
import tempfile
import os
from pathlib import Path

def handle_file_upload(file: UploadFile) -> Path:
    """Securely handle uploaded file."""
    # Validate file type
    allowed_extensions = {'.ged', '.gedcom'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise ValueError(f"File type {file_ext} not allowed")
    
    # Validate file size (e.g., max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > max_size:
        raise ValueError(f"File size {file_size} exceeds limit {max_size}")
    
    # Use secure temporary file
    with tempfile.NamedTemporaryFile(
        mode='wb',
        delete=False,
        suffix=file_ext,
        dir=tempfile.gettempdir()
    ) as tmp:
        # Read and write in chunks to avoid memory issues
        while chunk := file.file.read(8192):
            tmp.write(chunk)
        temp_path = Path(tmp.name)
    
    return temp_path
```

---

### Network Security

#### 🎯 Recommendations

**1. HTTPS Only in Production**
```python
# main.py
import uvicorn

if __name__ == "__main__":
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    ssl_certfile = os.getenv("SSL_CERTFILE")
    
    uvicorn.run(
        "core.webapp:app",
        host="0.0.0.0",
        port=443 if ssl_keyfile else 8000,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        ssl_version=ssl.PROTOCOL_TLS_SERVER,
    )
```

**2. Rate Limiting**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/persons")
@limiter.limit("100/minute")
async def get_persons(request: Request):
    # Limited to 100 requests per minute per IP
    pass
```

**3. CORS Configuration**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## Security Checklist

### Development
- [ ] No hardcoded secrets in code
- [ ] All secrets in environment variables
- [ ] Password hashing with bcrypt
- [ ] SQL injection protection via ORM
- [ ] XSS protection with auto-escaping
- [ ] CSRF tokens for state-changing operations
- [ ] Input validation on all endpoints

### Deployment
- [ ] HTTPS/TLS enabled
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Database encryption at rest
- [ ] Regular security updates
- [ ] Audit logging enabled
- [ ] Backup encryption

### Privacy
- [ ] Living individuals protected
- [ ] GDPR compliance for EU users
- [ ] Data retention policies
- [ ] Right to be forgotten mechanism
- [ ] Privacy policy published
- [ ] User consent management

---

## Security Incident Response

### Process
1. **Detect** - Monitor logs, alerts
2. **Contain** - Isolate affected systems
3. **Investigate** - Determine scope and impact
4. **Remediate** - Fix vulnerability, restore service
5. **Document** - Record incident and lessons learned

### Contacts
- Security Lead: [Contact Info]
- Infrastructure Team: [Contact Info]
- Legal/Compliance: [Contact Info]

---

## Regular Security Audits

### Automated Tools
```bash
# Run security checks
bandit -r core/

# Check dependencies for vulnerabilities
pip-audit

# Check for secrets in code
detect-secrets scan
```

### Manual Reviews
- Code review for security issues
- Penetration testing (annual)
- Security architecture review (quarterly)
- Compliance audit (annual)

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GDPR Compliance](https://gdpr.eu/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
