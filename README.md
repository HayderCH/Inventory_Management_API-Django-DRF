# User Management Authentication System

A secure, comprehensive JWT-based authentication and user management system built with Django REST Framework. This system provides enterprise-grade authentication with role-based access control, account security features, and a complete testing suite.

## Features

### Authentication
- JWT-based authentication with access and refresh tokens
- Token refresh mechanism to maintain sessions
- Token blacklisting for secure logout
- Rate limiting to prevent brute force attacks

### User Management
- User registration with email verification
- Role-based authorization (Admin, Manager, Employee, Auditor)
- User profile management
- Password management with reset flow

### Security
- Account lockout after multiple failed login attempts
- IP address tracking and login attempt logging
- CSRF protection
- Secure token generation and validation
- Strong password validation
