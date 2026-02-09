"""
Authentication and Authorization Module

Provides basic access control for the vulnerability analysis application.
Since this is a desktop application, authentication is simplified compared
to web applications, focusing on session management and user access control.
"""

import hashlib
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import json


class SessionManager:
    """Manages user sessions and authentication state."""
    
    def __init__(self, session_timeout_minutes: int = 60):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: How long until session expires (in minutes)
        """
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: str, username: str) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: Unique identifier for the user
            username: Username for the session
            
        Returns:
            Session token string
        """
        session_token = secrets.token_urlsafe(32)
        
        self.active_sessions[session_token] = {
            'user_id': user_id,
            'username': username,
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
        
        return session_token
    
    def validate_session(self, session_token: str) -> bool:
        """
        Validate if a session is still active and not expired.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        if session_token not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_token]
        now = datetime.now()
        
        # Check if session has expired
        if now - session_data['last_activity'] > self.session_timeout:
            self.destroy_session(session_token)
            return False
        
        # Update last activity
        self.active_sessions[session_token]['last_activity'] = now
        return True
    
    def destroy_session(self, session_token: str) -> bool:
        """
        Destroy a session.
        
        Args:
            session_token: Session token to destroy
            
        Returns:
            True if session was destroyed, False if it didn't exist
        """
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
            return True
        return False
    
    def get_user_info(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from a session.
        
        Args:
            session_token: Session token to get user info for
            
        Returns:
            User info dictionary or None if session invalid
        """
        if not self.validate_session(session_token):
            return None
        
        return self.active_sessions[session_token].copy()


class UserManager:
    """Manages user accounts and credentials."""
    
    def __init__(self, users_file: str = "users.json"):
        """
        Initialize user manager.
        
        Args:
            users_file: Path to the users configuration file
        """
        self.users_file = Path(users_file)
        self.default_users = {
            "admin": {
                "password_hash": self._hash_password("admin123"),  # Default admin password
                "role": "administrator",
                "active": True,
                "created_at": datetime.now().isoformat()
            },
            "analyst": {
                "password_hash": self._hash_password("analyst123"),  # Default analyst password
                "role": "analyst",
                "active": True,
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Load users from file or create default users
        self.users = self._load_users()
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using salted SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Salted hash of the password
        """
        salt = secrets.token_hex(16)
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('ascii'), 
                                      100000)
        return salt + pwdhash.hex()
    
    def _verify_password(self, password: str, hashed_pwd: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            hashed_pwd: Stored hash to verify against
            
        Returns:
            True if password matches hash, False otherwise
        """
        salt = hashed_pwd[:32]
        stored_hash = hashed_pwd[32:]
        pwdhash = hashlib.pbkdf2_hmac('sha256',
                                      password.encode('utf-8'),
                                      salt.encode('ascii'),
                                      100000)
        return pwdhash.hex() == stored_hash
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """
        Load users from the configuration file.
        
        Returns:
            Dictionary of users
        """
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, return default users
                return self.default_users.copy()
        else:
            # Create users file with default users
            self._save_users(self.default_users)
            return self.default_users.copy()
    
    def _save_users(self, users: Dict[str, Dict[str, Any]]) -> bool:
        """
        Save users to the configuration file.
        
        Args:
            users: Dictionary of users to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            return True
        except IOError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username to authenticate
            password: Password to authenticate with
            
        Returns:
            True if authentication successful, False otherwise
        """
        if username not in self.users:
            return False
        
        user_data = self.users[username]
        
        if not user_data.get('active', False):
            return False
        
        return self._verify_password(password, user_data['password_hash'])
    
    def create_user(self, username: str, password: str, role: str = "analyst") -> bool:
        """
        Create a new user account.
        
        Args:
            username: New username
            password: New password
            role: User role (analyst, administrator)
            
        Returns:
            True if user created successfully, False otherwise
        """
        if username in self.users:
            return False  # User already exists
        
        self.users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
            "active": True,
            "created_at": datetime.now().isoformat()
        }
        
        return self._save_users(self.users)
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            username: Username to change password for
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully, False otherwise
        """
        if username not in self.users:
            return False
        
        user_data = self.users[username]
        
        if not self._verify_password(old_password, user_data['password_hash']):
            return False
        
        self.users[username]['password_hash'] = self._hash_password(new_password)
        
        return self._save_users(self.users)
    
    def get_user_role(self, username: str) -> Optional[str]:
        """
        Get the role of a user.
        
        Args:
            username: Username to get role for
            
        Returns:
            User role or None if user doesn't exist
        """
        if username not in self.users:
            return None
        
        return self.users[username].get('role')


class AccessControl:
    """Provides authorization controls for application features."""
    
    def __init__(self):
        """Initialize access control system."""
        self.permissions = {
            'analyst': [
                'analyze_files',
                'view_reports',
                'edit_reports',
                'export_reports',
                'chat_assistant'
            ],
            'administrator': [
                'analyze_files',
                'view_reports',
                'edit_reports',
                'export_reports',
                'chat_assistant',
                'manage_users',
                'view_system_logs',
                'configure_settings'
            ]
        }
    
    def has_permission(self, role: str, permission: str) -> bool:
        """
        Check if a role has a specific permission.
        
        Args:
            role: User role
            permission: Permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        if role not in self.permissions:
            return False
        
        return permission in self.permissions[role]
    
    def get_permissions_for_role(self, role: str) -> list:
        """
        Get all permissions for a role.
        
        Args:
            role: User role
            
        Returns:
            List of permissions for the role
        """
        return self.permissions.get(role, [])


# Global instances
session_manager = SessionManager()
user_manager = UserManager()
access_control = AccessControl()


def require_auth(func):
    """
    Decorator to require authentication for a function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Wrapper function that checks authentication
    """
    def wrapper(*args, **kwargs):
        # This is a simplified version - in practice, you'd extract the session
        # from the calling context
        session_token = kwargs.get('session_token')
        if not session_token or not session_manager.validate_session(session_token):
            raise PermissionError("Authentication required")
        
        return func(*args, **kwargs)
    return wrapper


def require_permission(permission: str):
    """
    Decorator to require a specific permission for a function.
    
    Args:
        permission: Required permission
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            session_token = kwargs.get('session_token')
            if not session_token or not session_manager.validate_session(session_token):
                raise PermissionError("Authentication required")
            
            user_info = session_manager.get_user_info(session_token)
            if not user_info:
                raise PermissionError("Session invalid")
            
            role = user_manager.get_user_role(user_info['username'])
            if not role or not access_control.has_permission(role, permission):
                raise PermissionError(f"Permission '{permission}' required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator