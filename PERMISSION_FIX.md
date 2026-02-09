# Permission Denied Fix

## Issue
Error message: `[ERROR] Permission denied: analyze_files required`

## Root Cause
The MainWindow initialization created a session for "local_analyst" user, but this user didn't exist in the users.json file. When permission checks ran:
1. `user_manager.get_user_role("local_analyst")` returned `None` (user doesn't exist)
2. `access_control.has_permission(None, "analyze_files")` returned `False`
3. File upload was blocked with permission denied error

## Solution
Modified `MainWindow._initialize_auth()` to ensure the `local_analyst` user exists with `analyst` role before creating a session.

**File Changed:** [app/main_window.py](app/main_window.py#L309-L322)

**Changes Made:**
1. Added check for `local_analyst` user in `user_manager.users`
2. If missing, create user with:
   - Role: `analyst`
   - Password: hashed "local_analyst"
   - Active: `True`
3. Save updated users to users.json

**Added Import:**
- Added `from datetime import datetime` for user creation timestamp

## Result
✓ Permission check now passes
✓ File upload works without errors
✓ User has `analyze_files` permission
✓ Application initializes without permission errors

## Verification
Tested with simulated permission check - confirmed:
- local_analyst user created with analyst role
- Session created and valid
- User has analyze_files permission
- Smoke tests all passing
