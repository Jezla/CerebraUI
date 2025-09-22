# Email Verification and Password Reset Feature

## Feature Overview

This PR implements a complete email verification and password reset functionality, including OTP (One-Time Password) generation, email sending, verification, and password reset flow.

## New Features

### 1. Email Sending Function
- **Endpoint**: `POST /api/v1/auths/send_reset_email`
- **Function**: Send password reset email with OTP to user's email address
- **Security Features**:
  - Email format validation
  - User existence check
  - Attempt limit (maximum 3 attempts per email)
  - Prevent sending emails to non-existent users

### 2. OTP Verification Function
- **Endpoint**: `POST /api/v1/auths/verify_otp`
- **Function**: Verify user-input OTP code
- **Security Features**:
  - OTP format validation
  - Attempt count check
  - Token verification
  - Prevent brute force attacks

### 3. Token Verification Function
- **Endpoint**: `POST /api/v1/auths/verify_otp_token`
- **Function**: Verify token generated after OTP verification
- **Purpose**: Ensure legitimacy of password reset requests

### 4. Password Reset Function
- **Endpoint**: `POST /api/v1/auths/reset_password`
- **Function**: Reset user password using verified token
- **Security Features**:
  - Token verification
  - Password strength check
  - User identity confirmation

## Technical Implementation

### Database Models
- **OtpModel**: Store OTP related data
  - `id`: Unique identifier
  - `email`: User email address
  - `otp`: Encrypted OTP code
  - `attempts`: Number of attempts
  - `is_used`: Whether it has been used
  - `token`: Verification token

### Core Functions
- `send_email()`: Send OTP email
- `generate_otp()`: Generate OTP and token
- `verify_otp()`: Verify OTP
- `verify_otp_token()`: Verify token
- `update_user_password_by_email()`: Update password
- `check_email_attempts()`: Check attempt count

### Security Measures
1. **Attempt Limit**: Maximum 3 attempts per email
2. **OTP Encrypted Storage**: Use SHA256 hash to store OTP
3. **Token Expiration**: Both OTP and token have 10-minute validity
4. **User Verification**: Ensure only existing users can receive emails
5. **Input Validation**: All inputs are validated for format

## Configuration Requirements
1. **Resend API Key**: Register an account on www.resend.com and get your own API key 
https://resend.com/docs/introduction
2. **Set Up your domain**: Resend needs a domain name otherwise you cannot send the email. Please follow the link blow to set up your domain.
https://resend.com/docs/dashboard/domains/introduction


### Environment Variables
```bash
# Email service configuration
RESEND_API_KEY=your_resend_api_key
```

## File Changes

### Modified Files
- `open_webui/routers/auths.py`: Added new API endpoints
- `open_webui/utils/auth.py`: Added core functionality functions
- `open_webui/models/otp.py`: Added OTP related models
- `open_webui/models/auths.py`: Added request/response models

## Compatibility

- Fully compatible with existing authentication system
- Does not affect existing user login flow
- Supports all existing user roles and permissions

---

**Developer**: SharkXiXi
**Date**: 2025-09-21 
