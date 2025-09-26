# User Management Setup

## Initial User Creation

To create the initial admin user, use environment variables for security:

```bash
# Set environment variables
export INITIAL_USER_EMAIL="admin@yourdomain.com"
export INITIAL_USER_PASSWORD="your_secure_password"
export INITIAL_USER_FIRST_NAME="Your"
export INITIAL_USER_LAST_NAME="Name"

# Run the script
python scripts/create_initial_user.py
```

### Security Notes

- **Never** hardcode credentials in source code
- Use strong passwords (minimum 8 characters, mixed case, numbers, symbols)
- Change default credentials immediately after first login
- Use environment variables or secure configuration management

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INITIAL_USER_EMAIL` | Yes | - | Admin user email address |
| `INITIAL_USER_PASSWORD` | Yes | - | Admin user password |
| `INITIAL_USER_FIRST_NAME` | No | "Admin" | User's first name |
| `INITIAL_USER_LAST_NAME` | No | "User" | User's last name |

### Example

```bash
# Create admin user
INITIAL_USER_EMAIL="admin@mycompany.com" \
INITIAL_USER_PASSWORD="MySecurePassword123!" \
INITIAL_USER_FIRST_NAME="System" \
INITIAL_USER_LAST_NAME="Administrator" \
python scripts/create_initial_user.py
```