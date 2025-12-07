# Authentication Migration - Supabase to JWT

## ✅ Changes Made

### Backend
1. **New Auth Service** (`app/services/auth_service.py`)
   - JWT token creation/verification
   - Password hashing with bcrypt
   - User authentication

2. **Updated Auth Routes** (`app/api/routes/auth.py`)
   - `POST /api/auth/login` - Login with email/password
   - `POST /api/auth/register` - Register new user
   - `GET /api/auth/me` - Get current user profile

3. **Updated User Model** (`app/models/user.py`)
   - Added `password_hash` column (nullable for migration)
   - Made `supabase_user_id` nullable (for backward compatibility)

4. **Updated Dependencies** (`app/core/dependencies.py`)
   - Removed Supabase token verification
   - Added JWT token verification

### Frontend
1. **New Auth Context** (`lib/auth-context.tsx`)
   - Uses backend API instead of Supabase
   - Stores JWT token in localStorage
   - Handles login/logout/register

2. **Updated API Client** (`lib/api.ts`)
   - Added auth token interceptor
   - Added `login()`, `register()`, `getCurrentUser()` methods

3. **Removed Supabase Files**
   - Deleted `lib/supabase.ts`
   - Deleted `lib/supabase-server.ts`
   - Deleted `app/auth/callback/route.ts`

4. **Updated Auth Pages**
   - Removed Google OAuth buttons
   - Simplified to email/password only

## 🔄 Database Migration

Run this migration to add the `password_hash` column:

```bash
# Create migration (when DB is running)
alembic revision --autogenerate -m "add_password_hash_to_users"

# Or create manually:
alembic revision -m "add_password_hash_to_users"
```

Then edit the migration file to add:
```python
def upgrade():
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))
    op.alter_column('users', 'supabase_user_id', nullable=True)

def downgrade():
    op.alter_column('users', 'supabase_user_id', nullable=False)
    op.drop_column('users', 'password_hash')
```

## 🚀 Usage

### Register User
```bash
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "password123",
  "username": "optional"
}
```

### Login
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { "id": "...", "email": "..." }
}
```

### Get Current User
```bash
GET /api/auth/me
Headers: Authorization: Bearer <token>
```

## 📝 Environment Variables

No Supabase variables needed! Just ensure:
- `JWT_SECRET` is set in backend `.env` (or uses default)
- Frontend has `NEXT_PUBLIC_API_URL` pointing to backend

## ✅ Status

- ✅ Backend JWT auth implemented
- ✅ Frontend updated to use backend API
- ✅ Supabase removed
- ⏳ Database migration pending (run when DB is available)

