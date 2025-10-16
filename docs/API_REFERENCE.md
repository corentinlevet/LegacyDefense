# API Documentation

## Overview

The GeneWeb REST API provides programmatic access to genealogical data, following modern API design principles with OpenAPI/Swagger documentation.

**Base URL**: `http://localhost:8000/api`

**API Version**: 1.0

---

## Authentication

### JWT Token Authentication

Most endpoints require authentication using JWT (JSON Web Tokens).

#### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Using the Token

Include the token in the `Authorization` header:

```http
GET /api/persons/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Persons API

### List All Persons

```http
GET /api/persons
```

**Query Parameters:**
- `limit` (integer): Number of results per page (default: 50, max: 100)
- `offset` (integer): Number of results to skip (default: 0)
- `search` (string): Search by name (partial match)
- `sex` (string): Filter by sex (male, female, neuter)

**Example Request:**
```http
GET /api/persons?limit=10&search=Smith&sex=male
```

**Response:**
```json
{
  "total": 42,
  "limit": 10,
  "offset": 0,
  "data": [
    {
      "id": 1,
      "first_name": "John",
      "surname": "Smith",
      "sex": "male",
      "birth_date": "1950-03-15",
      "death_date": null,
      "occupation": "Engineer",
      "consanguinity": 0.0
    },
    ...
  ]
}
```

### Get Person by ID

```http
GET /api/persons/{person_id}
```

**Response:**
```json
{
  "id": 1,
  "first_name": "John",
  "surname": "Smith",
  "occ": 0,
  "public_name": "",
  "sex": "male",
  "birth_event": {
    "event_type": "birth",
    "date": {
      "day": 15,
      "month": 3,
      "year": 1950,
      "precision": "sure"
    },
    "place": {
      "place": "Hospital",
      "town": "Springfield",
      "state": "Illinois",
      "country": "USA"
    }
  },
  "death_event": null,
  "occupation": "Engineer",
  "consanguinity": 0.0,
  "families_as_parent": [2, 5],
  "parent_family": 1
}
```

### Create Person

```http
POST /api/persons
Authorization: Bearer {token}
Content-Type: application/json

{
  "first_name": "Jane",
  "surname": "Doe",
  "sex": "female",
  "birth_date": "1985-07-20",
  "occupation": "Doctor"
}
```

**Response:**
```json
{
  "id": 123,
  "first_name": "Jane",
  "surname": "Doe",
  "sex": "female",
  "birth_date": "1985-07-20",
  "occupation": "Doctor",
  "consanguinity": 0.0,
  "created_at": "2025-10-16T08:00:00Z"
}
```

### Update Person

```http
PUT /api/persons/{person_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "first_name": "Jane",
  "surname": "Doe-Smith",
  "occupation": "Senior Doctor"
}
```

### Delete Person

```http
DELETE /api/persons/{person_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "message": "Person deleted successfully",
  "id": 123
}
```

---

## Families API

### List Families

```http
GET /api/families?limit=20&offset=0
```

**Response:**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "data": [
    {
      "id": 1,
      "father_id": 10,
      "mother_id": 11,
      "children_ids": [20, 21, 22],
      "marriage_date": "1970-06-15",
      "marriage_type": "married"
    },
    ...
  ]
}
```

### Get Family by ID

```http
GET /api/families/{family_id}
```

**Response:**
```json
{
  "id": 1,
  "father": {
    "id": 10,
    "first_name": "John",
    "surname": "Smith"
  },
  "mother": {
    "id": 11,
    "first_name": "Mary",
    "surname": "Jones"
  },
  "children": [
    {
      "id": 20,
      "first_name": "Alice",
      "surname": "Smith"
    },
    {
      "id": 21,
      "first_name": "Bob",
      "surname": "Smith"
    }
  ],
  "marriage_event": {
    "event_type": "marriage",
    "date": "1970-06-15",
    "place": {
      "town": "Springfield",
      "country": "USA"
    }
  }
}
```

### Create Family

```http
POST /api/families
Authorization: Bearer {token}
Content-Type: application/json

{
  "father_id": 10,
  "mother_id": 11,
  "children_ids": [20, 21],
  "marriage_date": "1970-06-15"
}
```

---

## Genealogy Algorithms API

### Calculate Consanguinity

Calculate Wright's coefficient of consanguinity for a person.

```http
GET /api/persons/{person_id}/consanguinity
```

**Response:**
```json
{
  "person_id": 123,
  "consanguinity": 0.0625,
  "common_ancestors": [45, 46],
  "paths": [
    {
      "ancestor_id": 45,
      "generations_from_person": 3,
      "path_coefficient": 0.03125
    },
    {
      "ancestor_id": 46,
      "generations_from_person": 3,
      "path_coefficient": 0.03125
    }
  ]
}
```

### Get Ancestors

Retrieve all ancestors of a person.

```http
GET /api/persons/{person_id}/ancestors?generations=5
```

**Query Parameters:**
- `generations` (integer): Maximum number of generations (default: unlimited)

**Response:**
```json
{
  "person_id": 123,
  "total_ancestors": 30,
  "ancestors": [
    {
      "id": 100,
      "first_name": "Grandfather",
      "surname": "Smith",
      "generation": 2
    },
    {
      "id": 101,
      "first_name": "Grandmother",
      "surname": "Jones",
      "generation": 2
    },
    ...
  ]
}
```

### Get Descendants

Retrieve all descendants of a person.

```http
GET /api/persons/{person_id}/descendants?generations=3
```

**Response:**
```json
{
  "person_id": 100,
  "total_descendants": 25,
  "descendants": [
    {
      "id": 123,
      "first_name": "Child",
      "surname": "Smith",
      "generation": 1
    },
    ...
  ]
}
```

### Detect Relationship

Find the relationship between two persons.

```http
GET /api/persons/{person1_id}/relationship/{person2_id}
```

**Response:**
```json
{
  "person1_id": 100,
  "person2_id": 123,
  "relationship": "grandfather",
  "distance": 2,
  "common_ancestors": [],
  "description": "Person 100 is the grandfather of Person 123"
}
```

---

## GEDCOM Import/Export API

### Import GEDCOM File

```http
POST /api/import/gedcom
Authorization: Bearer {token}
Content-Type: multipart/form-data

file=@path/to/file.ged
```

**Response:**
```json
{
  "message": "GEDCOM imported successfully",
  "statistics": {
    "persons_imported": 1523,
    "families_imported": 456,
    "events_imported": 3045,
    "duration_seconds": 12.5
  }
}
```

### Export to GEDCOM

```http
GET /api/export/gedcom
Authorization: Bearer {token}
```

**Query Parameters:**
- `version` (string): GEDCOM version (default: "5.5.1")
- `encoding` (string): Character encoding (default: "UTF-8")

**Response:**
- Content-Type: `application/x-gedcom`
- File download with genealogical data in GEDCOM format

---

## Search API

### Full-Text Search

Search across all persons and families.

```http
GET /api/search?q=smith&type=person&limit=20
```

**Query Parameters:**
- `q` (string, required): Search query
- `type` (string): Entity type to search (person, family, all)
- `limit` (integer): Results per page
- `offset` (integer): Results to skip

**Response:**
```json
{
  "query": "smith",
  "total": 42,
  "results": [
    {
      "type": "person",
      "id": 123,
      "first_name": "John",
      "surname": "Smith",
      "score": 0.95
    },
    {
      "type": "person",
      "id": 124,
      "first_name": "Mary",
      "surname": "Smithson",
      "score": 0.87
    }
  ]
}
```

---

## Statistics API

### Database Statistics

Get overall statistics about the genealogical database.

```http
GET /api/statistics
```

**Response:**
```json
{
  "total_persons": 1523,
  "total_families": 456,
  "total_events": 3045,
  "males": 752,
  "females": 771,
  "unknown_sex": 0,
  "oldest_birth_year": 1650,
  "newest_birth_year": 2020,
  "average_consanguinity": 0.015,
  "database_size_mb": 45.2
}
```

### Person Statistics

Get statistics for a specific person.

```http
GET /api/persons/{person_id}/statistics
```

**Response:**
```json
{
  "person_id": 123,
  "total_ancestors": 30,
  "total_descendants": 15,
  "total_siblings": 3,
  "generation_depth": 8,
  "consanguinity": 0.0625
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "PERSON_NOT_FOUND",
    "message": "Person with ID 999 not found",
    "details": {
      "person_id": 999
    }
  }
}
```

### HTTP Status Codes

- `200 OK` - Successful GET request
- `201 Created` - Successful POST request (resource created)
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request data failed validation |
| `PERSON_NOT_FOUND` | Person ID not found |
| `FAMILY_NOT_FOUND` | Family ID not found |
| `AUTHENTICATION_FAILED` | Invalid credentials |
| `UNAUTHORIZED` | Missing authentication token |
| `FORBIDDEN` | Insufficient permissions |
| `GEDCOM_PARSE_ERROR` | GEDCOM file parsing failed |
| `DATABASE_ERROR` | Database operation failed |

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Authenticated users**: 1000 requests per hour
- **Anonymous users**: 100 requests per hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1634309600
```

---

## Pagination

List endpoints support pagination using `limit` and `offset` parameters.

**Example:**
```http
GET /api/persons?limit=20&offset=40
```

This retrieves persons 41-60.

**Response includes pagination metadata:**
```json
{
  "total": 1523,
  "limit": 20,
  "offset": 40,
  "has_next": true,
  "has_previous": true,
  "data": [...]
}
```

---

## Filtering and Sorting

### Filtering

Filter results using query parameters:

```http
GET /api/persons?sex=male&birth_year_min=1950&birth_year_max=2000
```

### Sorting

Sort results using `sort` and `order` parameters:

```http
GET /api/persons?sort=surname&order=asc
```

**Sort fields:**
- `surname` - Sort by surname
- `first_name` - Sort by first name
- `birth_date` - Sort by birth date
- `created_at` - Sort by creation date

**Order:**
- `asc` - Ascending (default)
- `desc` - Descending

---

## Field Selection

Request specific fields using `fields` parameter:

```http
GET /api/persons/123?fields=id,first_name,surname,birth_date
```

**Response:**
```json
{
  "id": 123,
  "first_name": "John",
  "surname": "Smith",
  "birth_date": "1950-03-15"
}
```

---

## API Versioning

The API supports versioning through URL path:

- **Current**: `/api/v1/persons`
- **Latest**: `/api/persons` (redirects to current version)

---

## Interactive Documentation

### Swagger UI

Interactive API documentation is available at:

**URL**: `http://localhost:8000/docs`

Features:
- Try API endpoints directly from browser
- View request/response schemas
- Authentication testing

### ReDoc

Alternative API documentation:

**URL**: `http://localhost:8000/redoc`

Features:
- Clean, readable format
- Downloadable OpenAPI specification
- Code examples

---

## Client Libraries

### Python

```python
import requests

# Authentication
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "your_username", "password": "your_password"}
)
token = response.json()["access_token"]

# Get person
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/persons/123",
    headers=headers
)
person = response.json()
print(f"Person: {person['first_name']} {person['surname']}")
```

### JavaScript

```javascript
// Authentication
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'your_username', password: 'your_password'})
});
const {access_token} = await loginResponse.json();

// Get person
const personResponse = await fetch('http://localhost:8000/api/persons/123', {
  headers: {'Authorization': `Bearer ${access_token}`}
});
const person = await personResponse.json();
console.log(`Person: ${person.first_name} ${person.surname}`);
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}' \
  | jq -r '.access_token')

# Get person
curl http://localhost:8000/api/persons/123 \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

---

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (not in localStorage)
3. **Handle rate limits** gracefully
4. **Use field selection** to reduce payload size
5. **Implement proper error handling**
6. **Cache responses** when appropriate
7. **Use pagination** for large datasets

---

## Support

- **API Issues**: Create issue on GitHub
- **Documentation**: See `/docs/api/`
- **Interactive docs**: Visit `/docs`
