\# Authentication \& Authorization Service



A Python and FastAPI service that validates OAuth2 access tokens and checks fine-grained user permissions stored in SQLite. The service returns an `ALLOW` or `DENY` decision for a requested HTTP method and resource path.



\## Features



\- OAuth2 JWT access-token validation.

\- User identity extraction from validated token claims.

\- SQLite-backed user permissions.

\- HTTP method-to-action mapping.

\- Resource matching with wildcard and nested-resource support.

\- Specificity-based permission resolution.

\- Deny precedence for conflicting rules of equal specificity.

\- Default-deny behavior when no permission matches.

\- Automated database, authorization, and API tests using pytest.



\## Technology Stack



\- Python 3.9+

\- FastAPI

\- Uvicorn

\- SQLite

\- Auth0 for OAuth2/JWT authentication

\- pytest



\## Project Structure



```text

openfabric-auth-service/

├── app/

│   ├── auth/

│   │   └── jwt\_verifier.py

│   ├── services/

│   │   └── authorization.py

│   ├── config.py

│   ├── database.py

│   └── main.py

├── data/

├── scripts/

│   ├── seed\_database.py

│   └── test\_permissions.py

├── tests/

│   ├── test\_api.py

│   ├── test\_authorization.py

│   └── test\_database.py

├── .env.example

├── .gitignore

├── requirements.txt

└── README.md

```



\## Prerequisites



\- Python 3.9 or later.

\- An OAuth2 identity provider account, such as Auth0.

\- An access token issued for the API audience configured in the environment.



\## Setup



\### 1. Open the project directory



In Windows PowerShell, navigate to the project directory:



```powershell

cd C:\\Users\\dhanu\\openfabric-auth-service

```



\### 2. Create and activate a virtual environment



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



If PowerShell blocks virtual-environment activation, use the environment's Python executable directly:



```powershell

.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt

```



\### 3. Install dependencies



With the virtual environment activated, run:



```powershell

python -m pip install -r requirements.txt

```



\### 4. Configure environment variables



Create a local environment file from the example:



```powershell

Copy-Item .env.example .env

notepad .env

```



Fill in the values required by `app/config.py` and the JWT verifier. For an Auth0 configuration, these commonly include:



\- Auth0 domain or issuer.

\- API audience.

\- Database path, if configurable.



Use the exact variable names defined in `.env.example` and `app/config.py`.



\*\*Security:\*\* Never commit `.env`, access tokens, client secrets, or other credentials to source control. The `.env.example` file should contain placeholders only.



\### 5. Initialize and seed the database



Run:



```powershell

python -m scripts.seed\_database

```



This initializes the SQLite database and inserts the sample permission records.



\## Run the Service



Start the development server:



```powershell

python -m uvicorn app.main:app --reload

```



The service will be available at:



\- Health check: `http://127.0.0.1:8000/health`

\- Interactive API documentation: `http://127.0.0.1:8000/docs`



Keep the terminal running while testing the API.



\## API Usage



\### `POST /authorize`



Checks whether a user can perform an action on a resource.



\#### Request body



The request must contain:



| Field | Type | Description |

|---|---|---|

| `access\_token` | String | OAuth2 access token to validate |

| `method` | String | HTTP method representing the requested action |

| `path` | String | Resource path to authorize |



Example:



```json

{

&#x20; "access\_token": "YOUR\_ACCESS\_TOKEN",

&#x20; "method": "GET",

&#x20; "path": "/wallets/wallet-789/transactions"

}

```



Replace `YOUR\_ACCESS\_TOKEN` with a valid access token issued for the configured API audience.



The user identity extracted from the token must match a `user\_id` in the permissions database for the seeded permission rules to grant access.



\#### Windows PowerShell example



```powershell

$body = @{

&#x20;   access\_token = "YOUR\_ACCESS\_TOKEN"

&#x20;   method = "GET"

&#x20;   path = "/wallets/wallet-789/transactions"

} | ConvertTo-Json



Invoke-RestMethod `

&#x20;   -Uri "http://127.0.0.1:8000/authorize" `

&#x20;   -Method Post `

&#x20;   -ContentType "application/json" `

&#x20;   -Body $body

```



\#### cURL example



In Windows PowerShell, use `curl.exe`:



```powershell

curl.exe -X POST "http://127.0.0.1:8000/authorize" `

&#x20; -H "Content-Type: application/json" `

&#x20; -d '{"access\_token":"YOUR\_ACCESS\_TOKEN","method":"GET","path":"/wallets/wallet-789/transactions"}'

```



Replace the placeholder with a valid access token. Do not save real tokens in this README or commit them to the repository.



\#### Example response



For a user with a matching read permission, the response has this shape:



```json

{

&#x20; "decision": "ALLOW",

&#x20; "user\_id": "user456",

&#x20; "reason": "User has read permission for wallets/wallet-789/transactions",

&#x20; "matched\_permissions": \[

&#x20;   {

&#x20;     "action": "read",

&#x20;     "resource": "wallets/wallet-789/transactions",

&#x20;     "effect": "allow"

&#x20;   }

&#x20; ]

}

```



The `user\_id` and matched permission records depend on the validated token and the database contents.



\#### Response fields



| Field | Description |

|---|---|

| `decision` | `ALLOW` or `DENY` |

| `user\_id` | Identity extracted from the validated token |

| `reason` | Explanation for the authorization decision |

| `matched\_permissions` | Permission rules selected by the resolver |



Authentication failures are returned as HTTP 401 responses. Unsupported HTTP methods and invalid resource paths are rejected with HTTP 400 responses. Invalid request bodies are handled by FastAPI request validation.



\## HTTP Method Mapping



The service maps HTTP methods to permission actions:



| HTTP method | Permission action |

|---|---|

| `GET` | `read` |

| `POST` | `write` |

| `PUT` | `write` |

| `PATCH` | `write` |

| `DELETE` | `delete` |



Unsupported methods are rejected instead of being treated as an allowed action.



\## Permission Resolution Design



The service extracts the authenticated user's identity from the validated token, maps the HTTP method to a permission action, and evaluates matching resource patterns from SQLite.



The permission-resolution approach is:



1\. \*\*Action filtering:\*\* Consider permission records for the authenticated user and requested action.

2\. \*\*Resource matching:\*\* Compare the requested resource path with stored resource patterns.

3\. \*\*Specificity:\*\* More-specific matching patterns take precedence over more-general patterns.

4\. \*\*Conflicting rules:\*\* When selected rules have equal specificity and conflicting effects, deny takes precedence.

5\. \*\*Default deny:\*\* If no permission matches the request, access is denied.



The wildcard character `\*` can match path segments according to the resource-matching algorithm. Nested resource paths are evaluated against the stored pattern rather than automatically inheriting permission from every parent path.



The specificity and deny-precedence behavior should be covered by tests, particularly when general allow rules overlap with more-specific deny rules. The implemented resolver's precedence should be checked against the assignment's requirement that deny wins when both allow and deny permissions apply to the same resource.



\## Database Design



The service uses a SQLite table named `user\_permissions`.



| Column | Description |

|---|---|

| `id` | Primary key |

| `user\_id` | Identity associated with the permission |

| `action` | `read`, `write`, or `delete` |

| `resource` | Resource path or wildcard pattern |

| `effect` | `allow` or `deny` |



The database schema and connection handling are implemented in `app/database.py`. Sample permission records are created by `scripts/seed\_database.py`.



Database queries use parameterized SQL to avoid constructing queries by concatenating user-controlled values.



\## Running Tests



Run the automated test suite from the project directory:



```powershell

python -m pytest -v

```



The tests cover database initialization and seeding, HTTP method mapping, permission decisions, and API endpoint behavior.



Some API tests mock token verification to test endpoint behavior independently of Auth0. JWT verification should also be tested with valid and invalid tokens, including checks for signature, expiration, issuer, and audience.



Before submission, make sure tests cover:



\- Allowed and denied requests.

\- Unknown users and missing permissions.

\- Wildcard and nested-resource matching.

\- Overlapping allow and deny rules.

\- More-specific versus more-general resource patterns.

\- Invalid or expired access tokens.

\- Unsupported HTTP methods and invalid request bodies.



\## Design Decisions and Trade-offs



\### SQLite



SQLite provides a lightweight database without requiring a separate database server. It is convenient for local development and a take-home assignment. A server-based database may be more suitable for deployments with higher concurrency or distributed workloads.



\### FastAPI



FastAPI provides request validation, structured API responses, and interactive documentation through `/docs`.



\### OAuth2 and JWT validation



The service delegates token issuance to an external identity provider. It validates the access token before trusting identity claims, keeping authentication separate from permission evaluation.



\### Database-backed permissions



Storing permissions in SQLite allows the service to evaluate user-specific rules without hardcoding every permission in the API. Indexes help reduce the cost of looking up permissions.



\### Default deny



Requests without a matching permission are denied. This avoids granting access simply because no rule was found.



\### Resource matching



Wildcard and specificity rules support flexible resource policies, but overlapping patterns can create ambiguity. Automated tests are important to ensure that changes to matching logic do not unintentionally grant access.



\## Security Considerations



\- Validate JWT signatures, expiration, issuer, and audience before trusting token claims.

\- Keep secrets in environment variables or a secret manager.

\- Never commit `.env`, access tokens, or client secrets.

\- Do not log access tokens or sensitive authentication details.

\- Use HTTPS in deployed environments.

\- Consider rate limiting and request-size limits for production.

\- Review permission precedence carefully to avoid unintended access grants.



\## Areas for Improvement



\- Add integration tests using an isolated test database and controlled test tokens.

\- Add comprehensive tests for specificity, deny precedence, and wildcard edge cases.

\- Add structured audit logging for authorization decisions without recording tokens or secrets.

\- Add rate limiting and request-size limits.

\- Consider permission caching with a clear invalidation strategy.

\- Add continuous integration to run tests automatically.

\- Add production deployment configuration, monitoring, and health checks.



\## Submission Checklist



\- \[ ] Source code is organized and documented.

\- \[ ] Dependencies are listed in `requirements.txt`.

\- \[ ] `.env.example` contains placeholders only.

\- \[ ] `.env` and local database files are excluded from Git.

\- \[ ] Automated tests pass.

\- \[ ] Permission-matching and deny-precedence edge cases are tested.

\- \[ ] README includes setup instructions and API examples.

\- \[ ] A 2–3 minute demonstration video is recorded.

\- \[ ] Repository link and submission notes are prepared.

