# Authentication & Authorization Service

A Python and FastAPI service that validates OAuth2 JWT access tokens and evaluates fine-grained user permissions stored in SQLite. The service returns an `ALLOW` or `DENY` decision for a requested HTTP method and resource path.

## Features

- JWT access-token verification using Auth0 and JSON Web Key Sets (JWKS).
- Validation of token signature, expiration, issuer, and audience.
- Extraction of the authenticated user identity from validated token claims.
- SQLite-backed permission storage.
- HTTP method-to-action mapping.
- Wildcard resource matching, including nested resource paths.
- Specificity-based permission resolution.
- Deny precedence when conflicting permissions have equal specificity.
- Default-deny behavior when no permission matches.
- Automated database, authorization, and API tests using pytest.

## Technology Stack

- Python 3.9+
- FastAPI
- Uvicorn
- SQLite
- PyJWT
- Auth0
- pytest

## Project Structure

```text
openfabric-auth-service/
├── app/
│   ├── auth/
│   │   └── jwt_verifier.py
│   ├── services/
│   │   └── authorization.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── data/
├── scripts/
│   ├── seed_database.py
│   └── test_permissions.py
├── tests/
│   ├── test_api.py
│   ├── test_authorization.py
│   └── test_database.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.9 or later.
- Git.
- An Auth0 tenant and an API configured with an audience.
- An access token issued for that API.

## Setup

### 1. Open the project directory

In Windows PowerShell:

```powershell
cd C:\Users\dhanu\openfabric-auth-service
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, use the virtual environment's Python executable directly.

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
notepad .env
```

Configure the following values using your Auth0 API settings:

| Variable | Purpose |
|---|---|
| `AUTH0_DOMAIN` | Auth0 tenant domain |
| `AUTH0_AUDIENCE` | Identifier of the API for which the token was issued |
| `AUTH0_ALGORITHMS` | Permitted JWT signing algorithms; defaults to `RS256` |
| `DATABASE_PATH` | SQLite database location; defaults to `./data/permissions.db` |

Use the exact values for your Auth0 tenant and API. The example values are placeholders and will not authenticate real tokens.

**Security:** Never commit `.env`, access tokens, client secrets, or other credentials to source control. Only placeholder values should be stored in `.env.example`.

### 5. Initialize and seed the database

Run the project's database seeding script:

```powershell
python -m scripts.seed_database
```

This script initializes the SQLite database and inserts the sample permission records defined by the project.

If you modify the seed data, verify the resulting records before using them in a demonstration.

## Run the Service

Start the development server:

```powershell
python -m uvicorn app.main:app --reload
```

The service is available at:

- Health check: `http://127.0.0.1:8000/health`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

Keep the server running while testing requests.

## API Usage

### `POST /authorize`

Checks whether the authenticated user is permitted to perform an action on a resource.

#### Request body

| Field | Type | Description |
|---|---|---|
| `access_token` | String | OAuth2 access token to validate |
| `method` | String | HTTP method representing the requested action |
| `path` | String | Resource path to authorize |

Example request:

```json
{
  "access_token": "YOUR_ACCESS_TOKEN",
  "method": "GET",
  "path": "/wallets/wallet-789/transactions"
}
```

Replace `YOUR_ACCESS_TOKEN` with a valid access token issued for the configured API audience.

The user identity extracted from the validated token must correspond to a user with applicable permission records in the database.

#### Windows PowerShell example

```powershell
$body = @{
    access_token = "YOUR_ACCESS_TOKEN"
    method = "GET"
    path = "/wallets/wallet-789/transactions"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/authorize" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

#### cURL example

In Windows PowerShell, use `curl.exe`:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/authorize" `
  -H "Content-Type: application/json" `
  -d '{"access_token":"YOUR_ACCESS_TOKEN","method":"GET","path":"/wallets/wallet-789/transactions"}'
```

Do not save real access tokens in this README or commit them to the repository.

#### Example response

For a user whose validated identity is `user456` and whose matching read permission allows the requested resource, the response has this shape:

```json
{
  "decision": "ALLOW",
  "user_id": "user456",
  "reason": "User has read permission for wallets/wallet-789/transactions",
  "matched_permissions": [
    {
      "action": "read",
      "resource": "wallets/wallet-789/transactions",
      "effect": "allow"
    }
  ]
}
```

The actual identity, decision, reason, and matched permissions depend on the validated token and database contents.

#### Response fields

| Field | Description |
|---|---|
| `decision` | `ALLOW` or `DENY` |
| `user_id` | Identity extracted from the validated token |
| `reason` | Explanation for the authorization decision |
| `matched_permissions` | Permission records selected by the resolver |

Authentication failures return HTTP 401 responses. Unsupported HTTP methods and invalid resource paths are rejected with HTTP 400 responses. Invalid request bodies are handled by FastAPI request validation.

## HTTP Method Mapping

The service maps HTTP methods to permission actions:

| HTTP method | Permission action |
|---|---|
| `GET` | `read` |
| `POST` | `write` |
| `PUT` | `write` |
| `PATCH` | `write` |
| `DELETE` | `delete` |

Unsupported methods are rejected instead of being treated as authorized actions.

## Permission Resolution Design

The service validates the access token, extracts the authenticated user's identity, maps the HTTP method to an action, and evaluates matching permission patterns stored in SQLite.

The resolver follows these rules:

1. **Action filtering:** Consider permission records for the authenticated user and requested action.
2. **Resource matching:** Compare the requested resource path with stored resource patterns.
3. **Specificity:** Prefer the most-specific matching pattern. Specificity is determined by the number of literal path segments, the total number of segments, and the number of literal characters.
4. **Equal-specificity conflict:** If matching rules of equal specificity conflict, deny takes precedence.
5. **Default deny:** If no permission matches the request, deny access.

The wildcard character `*` can match zero or more path segments according to the resource-matching algorithm. For example, `wallets/*` can match nested wallet resource paths, and `wallets/*/transactions/*` can match transaction paths with or without a trailing transaction identifier.

A more-specific rule can take precedence over a more-general rule. Deny precedence applies to conflicting rules of equal specificity; it does not mean every deny rule overrides every allow rule regardless of specificity.

The automated authorization tests cover resource matching, wildcard edge cases, specificity, conflicting rules, and default-deny behavior.

## Database Design

The service uses a SQLite table named `user_permissions`.

| Column | Description |
|---|---|
| `id` | Primary key |
| `user_id` | Identity associated with the permission |
| `action` | `read`, `write`, or `delete` |
| `resource` | Resource path or wildcard pattern |
| `effect` | `allow` or `deny` |

Database schema initialization, constraints, and connection handling are implemented in `app/database.py`. Sample permission records are created by `scripts/seed_database.py`.

Database queries use parameterized SQL to avoid constructing queries by concatenating user-controlled values.

## Running Tests

Run the automated test suite from the project directory:

```powershell
python -m pytest -v
```

The current automated test suite has **32 passing tests** in the verified local run. The tests cover database behavior, authorization decisions, resource matching, permission precedence, and API endpoint behavior.

Some API tests mock token verification so endpoint behavior can be tested independently of an external identity provider. A passing mocked test suite does not, by itself, prove that token verification works against a live Auth0 tenant.

Before deployment or submission, verify JWT handling with valid and invalid tokens, including signature, expiration, issuer, and audience validation, using a controlled Auth0 configuration or appropriate isolated test tokens.

## Design Decisions and Trade-offs

### SQLite

SQLite provides lightweight persistence without requiring a separate database server. It is suitable for local development and a take-home assignment. A server-based database may be more appropriate for distributed deployments or workloads with higher concurrency requirements.

### FastAPI

FastAPI provides request validation, structured responses, and interactive API documentation through `/docs`.

### JWT-based authentication

The service relies on an external identity provider to issue access tokens. The verifier checks token validity before the application trusts identity claims, separating authentication from permission evaluation.

### Database-backed permissions

Storing permissions in SQLite allows user-specific rules to be evaluated without hardcoding individual permissions into the API. Database indexes help support permission lookups.

### Default deny

Requests without a matching permission are denied. This avoids granting access merely because a rule is absent.

### Specificity and deny precedence

Specificity supports general and resource-specific policies. Deny precedence for equally specific conflicting rules provides a predictable resolution strategy. Tests are important because changes to matching or precedence logic can unintentionally grant access.

## Security Considerations

- Validate JWT signatures, expiration, issuer, and audience before trusting token claims.
- Restrict accepted signing algorithms to the configured set.
- Keep secrets in environment variables or a secret manager.
- Never commit `.env`, access tokens, or client secrets.
- Avoid logging access tokens or sensitive authentication details.
- Use HTTPS in deployed environments.
- Consider rate limiting and request-size limits for production.
- Review permission patterns and precedence carefully to avoid unintended access grants.

## Areas for Improvement

- Add integration tests using controlled JWTs and an isolated test database.
- Expand end-to-end coverage against a configured identity provider.
- Add structured audit logging for authorization decisions without recording tokens or secrets.
- Add rate limiting and request-size limits.
- Consider permission caching with an explicit invalidation strategy.
- Add continuous integration to run tests automatically.
- Add production deployment configuration, monitoring, and operational health checks.

## Submission Checklist

- [ ] Source code is organized and documented.
- [ ] Dependencies are listed in `requirements.txt`.
- [ ] `.env.example` contains placeholders only.
- [ ] `.env` and local database files are excluded from Git.
- [ ] Automated tests pass.
- [ ] Wildcard matching and permission precedence are covered by tests.
- [ ] README contains setup instructions and API examples.
- [ ] The application has been checked with a configured Auth0 tenant.
- [ ] A 2–3 minute demonstration video is recorded, if required by the assignment.
- [ ] Repository link and submission notes are prepared.
