"""
Auto-configuring settings module
===============================

This module automatically loads configuration from .env files or environment variables
and provides easy access to configuration values.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any


class Config:
    """Simple configuration loader that auto-loads on import."""
    
    def __init__(self):
        self._config = self._load_config()
    
    def _load_env_file(self) -> Dict[str, str]:
        """Load .env file if it exists. Handles both script and executable locations."""
        env_vars = {}
        
        # Determine .env file location
        if getattr(sys, 'frozen', False):
            # Running as compiled executable - .env should be next to .exe
            env_file = Path(sys.executable).parent / ".env"
        else:
            # Running as Python script - look in current directory
            env_file = Path(".env")
        
        if env_file.exists():
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            env_vars[key] = value
                            
                # Log successful load (only if we have values)
                if env_vars:
                    print(f"[CONFIG] Loaded {len(env_vars)} variables from: {env_file}")
                    
            except Exception as e:
                print(f"[CONFIG] Warning: Could not read .env file {env_file}: {e}")
        else:
            print(f"[CONFIG] No .env file found at: {env_file}, using defaults and environment variables")
        
        return env_vars
    
    def _get_value(self, key: str, default: Any, env_vars: Dict[str, str]) -> Any:
        """Get value with type conversion."""
        value = env_vars.get(key, os.getenv(key, default))
        
        # Convert types
        if isinstance(default, bool):
            return str(value).lower() in ('true', '1', 'yes', 'on') if isinstance(value, str) else bool(value)
        elif isinstance(default, int):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        return value
    
    def _load_config(self) -> Dict[str, Any]:
        """Load all configuration."""
        env_vars = self._load_env_file()
        
        config = {
            # Server settings
            'host': self._get_value('SERVER_HOST', '0.0.0.0', env_vars),
            'port': self._get_value('SERVER_PORT', 5003, env_vars),
            'reload': self._get_value('RELOAD', True, env_vars),
            'log_level': self._get_value('LOG_LEVEL', 'info', env_vars),
            'workers': self._get_value('WORKERS', 1, env_vars),
            'access_log': self._get_value('ACCESS_LOG', False, env_vars),
            
            # Middleware settings  
            'session_timeout': self._get_value('SESSION_TIMEOUT', 600, env_vars),
            'cleanup_interval': self._get_value('CLEANUP_INTERVAL', 300, env_vars),
        }
        
        # Debug info
        print(f"[CONFIG] SESSION_TIMEOUT: {config['session_timeout']} (source: {'env' if 'SESSION_TIMEOUT' in env_vars else 'default'})")
        print(f"[CONFIG] CLEANUP_INTERVAL: {config['cleanup_interval']} (source: {'env' if 'CLEANUP_INTERVAL' in env_vars else 'default'})")
        
        return config
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self._config.get(key, default)
    
    @property
    def server_config(self) -> Dict[str, Any]:
        """Server configuration for uvicorn."""
        config = {
            'host': self.get('host'),
            'port': self.get('port'),
            'log_level': self.get('log_level'),
            'reload': self.get('reload'),
            'access_log': self.get('access_log')
        }
        
        # Only add workers if not in reload mode
        if not self.get('reload'):
            config['workers'] = self.get('workers')
            
        return config
    
    @property 
    def middleware_config(self) -> Dict[str, Any]:
        """Middleware configuration."""
        return {
            'session_timeout': self.get('session_timeout'),
            'cleanup_interval': self.get('cleanup_interval')
        }


# Auto-load configuration on import
config = Config()