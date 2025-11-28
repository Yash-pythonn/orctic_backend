# API cURL Commands - User Authentication

All API endpoints with cURL examples for testing.

**Base URL:** `http://localhost:8000/api/users/`

---

## 1. Register User

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "confirm_password": "password123",
    "user_type": "customer",
    "mobile": "1234567890"
  }'
```

**Response:** Returns `access_token`, `refresh_token`, and user data.

---

## 2. Login

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

**Response:** Returns `access_token`, `refresh_token`, and user data.

**Save the token:**
```bash
# Save access token for subsequent requests
export ACCESS_TOKEN="your_access_token_here"
```

---

## 3. Get Profile (Protected - Requires Bearer Token)

```bash
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

**Example with saved token:**
```bash
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 4. Update Profile (Protected - Requires Bearer Token)

```bash
curl -X PUT http://localhost:8000/api/users/profile/update/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Updated",
    "user_type": "vendor",
    "mobile": "9876543210"
  }'
```

**Using PATCH method:**
```bash
curl -X PATCH http://localhost:8000/api/users/profile/update/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Updated Name"
  }'
```

---

## 5. Change Password (Protected - Requires Bearer Token)

```bash
curl -X POST http://localhost:8000/api/users/change-password/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "password123",
    "new_password": "newpassword456",
    "confirm_password": "newpassword456"
  }'
```

**Example with saved token:**
```bash
curl -X POST http://localhost:8000/api/users/change-password/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "password123",
    "new_password": "newpassword456",
    "confirm_password": "newpassword456"
  }'
```

---

## 6. Forgot Password

```bash
curl -X POST http://localhost:8000/api/users/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

**Note:** This generates a reset token (in production, it would be sent via email).

---

## 7. Reset Password

```bash
curl -X POST http://localhost:8000/api/users/reset-password/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "RESET_TOKEN_FROM_EMAIL",
    "new_password": "newpassword789",
    "confirm_password": "newpassword789"
  }'
```

**Note:** Replace `RESET_TOKEN_FROM_EMAIL` with the actual token from the forgot password email.

---

## 8. Verify Email

```bash
curl -X POST http://localhost:8000/api/users/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "VERIFICATION_TOKEN_FROM_EMAIL"
  }'
```

**Note:** Replace `VERIFICATION_TOKEN_FROM_EMAIL` with the actual verification token.

---

## 9. Refresh Token

```bash
curl -X POST http://localhost:8000/api/users/refresh-token/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

**Example with saved refresh token:**
```bash
export REFRESH_TOKEN="your_refresh_token_here"

curl -X POST http://localhost:8000/api/users/refresh-token/ \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }"
```

---

## Complete Testing Workflow

### Step 1: Register a new user
```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpass123",
    "confirm_password": "testpass123"
  }'
```

### Step 2: Login and save tokens
```bash
# Login
RESPONSE=$(curl -s -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }')

# Extract tokens (requires jq installed)
export ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access_token')
export REFRESH_TOKEN=$(echo $RESPONSE | jq -r '.refresh_token')

# Or manually set:
# export ACCESS_TOKEN="your_token_here"
# export REFRESH_TOKEN="your_refresh_token_here"
```

### Step 3: Get profile
```bash
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Step 4: Update profile
```bash
curl -X PATCH http://localhost:8000/api/users/profile/update/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "mobile": "1234567890"
  }'
```

### Step 5: Change password
```bash
curl -X POST http://localhost:8000/api/users/change-password/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "testpass123",
    "new_password": "newpass456",
    "confirm_password": "newpass456"
  }'
```

### Step 6: Refresh access token
```bash
curl -X POST http://localhost:8000/api/users/refresh-token/ \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }"
```

---

## Pretty Print JSON Response

To format the JSON response for better readability, pipe to `jq`:

```bash
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" | jq
```

Or use Python:
```bash
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" | python -m json.tool
```

---

## Error Handling

All endpoints return JSON error responses:

**401 Unauthorized:**
```json
{
  "error": "Invalid email or password."
}
```

**400 Bad Request:**
```json
{
  "error": "Email already registered."
}
```

**404 Not Found:**
```json
{
  "error": "User not found."
}
```

---

## Notes

1. **Access Token Lifetime:** 1 day
2. **Refresh Token Lifetime:** 7 days
3. **Bearer Token Format:** `Authorization: Bearer <token>`
4. **Base URL:** Adjust `localhost:8000` if your Django server runs on a different host/port
5. **MongoDB:** Ensure MongoDB is running on `localhost:27017`

