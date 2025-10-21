# Authentication Flow

## Current Implementation - FULLY WORKING ✅

### Token Management
- JWT tokens stored in localStorage as 'auth_token'
- Token validation prevents storing invalid tokens
- Invalid tokens
- Automatic token refresh on API requests

### Frontend Components
- **Axios Interceptors**: Configured in `utils/setupInterceptors.ts`
- **Auth State**: Managed by Pinia store with persistence
- **Guards**: Vue Router guards protect authenticated routes

### API Response Parsing
- Backend uses nested response format
- Frontend properly parses and extracts data
- Error handling for malformed responses

## Authentication Endpoints

### Registration
```bash
POST /api/auth/register
{
  "name": "User Name",
  "email": "user@example.com",
  "password": "Password123",
  "confirmPassword": "Password123"
}
```

### Login
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "Password123"
}
```

### Forgot Password
```bash
POST /api/auth/forgot-password
{
  "email": "user@example.com"
}
```

### Reset Password
```bash
POST /api/auth/reset-password
{
  "token": "jwt_reset_token",
  "password": "NewPassword123"
}
```

## Debugging Authentication Issues

### Token Not Attached
**Symptom**: 401 Unauthorized on authenticated endpoints
**Check**: `utils/setupInterceptors.ts` axios configuration
**Solution**: Verify interceptor is properly adding Authorization header

### CORS Errors
**Symptom**: Browser blocks requests due to CORS policy
**Check**: `FRONTEND_URL` environment variable in backend
**Solution**: Update to match deployment URL exactly

### Invalid Tokens
**Symptom**: Backend rejects valid-looking tokens
**Check**: JWT secret key consistency between requests
**Solution**: Verify `SECRET_KEY` environment variable is set correctly

### Response Parsing Errors
**Symptom**: Frontend receives data but can't extract it
**Check**: API response structure in network tab
**Solution**: Update parsing logic to match backend's nested format

## Security Considerations

### Password Requirements
- Minimum length enforced
- Must match confirmation on registration
- Hashed with bcrypt before storage

### JWT Tokens
- Short expiration time (configurable)
- Signed with SECRET_KEY
- Validated on every authenticated request

### Forgot Password Flow
- Secure token generation with 1-hour expiry
- Email delivery via Gmail SMTP
- One-time use tokens
