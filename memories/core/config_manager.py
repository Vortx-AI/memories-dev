"""
Centralized configuration management for memories-dev.
Provides a unified interface for all configuration needs.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field
import logging
from memories.utils.patterns import Singleton
from memories.utils.validation import Validator, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class ConfigSection:
    """Base class for configuration sections."""
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self):
        """Override to implement section-specific validation."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

@dataclass
class DatabaseConfig(ConfigSection):
    """Database configuration section."""
    path: str = "./data/db"
    name: str = "memories.db"
    pool_size: int = 10
    timeout: int = 30
    
    def validate(self):
        """Validate database configuration."""
        self.path = Validator.validate_string(self.path, min_length=1, max_length=500)
        self.name = Validator.validate_string(self.name, min_length=1, max_length=255)
        self.pool_size = Validator.validate_number(self.pool_size, min_value=1, max_value=100, integer_only=True)
        self.timeout = Validator.validate_number(self.timeout, min_value=1, max_value=3600, integer_only=True)

@dataclass
class RedisConfig(ConfigSection):
    """Redis configuration section."""
    url: str = "redis://localhost:6379"
    db: int = 0
    max_connections: int = 50
    socket_timeout: int = 5
    
    def validate(self):
        """Validate Redis configuration."""
        if not self.url.startswith(('redis://', 'rediss://')):
            raise ValidationError("Redis URL must start with redis:// or rediss://")
        self.db = Validator.validate_number(self.db, min_value=0, max_value=15, integer_only=True)
        self.max_connections = Validator.validate_number(self.max_connections, min_value=1, max_value=1000, integer_only=True)

@dataclass
class MemoryTierConfig(ConfigSection):
    """Memory tier configuration."""
    path: str
    max_size: int
    threads: int = 4
    memory_limit: str = "2GB"
    
    def validate(self):
        """Validate memory tier configuration."""
        self.path = Validator.validate_string(self.path, min_length=1, max_length=500)
        self.max_size = Validator.validate_number(self.max_size, min_value=1)
        self.threads = Validator.validate_number(self.threads, min_value=1, max_value=32, integer_only=True)

@dataclass
class MemoryConfig(ConfigSection):
    """Memory system configuration."""
    base_path: str = "./data/memory"
    enabled_tiers: List[str] = field(default_factory=lambda: ['red_hot', 'hot', 'warm', 'cold', 'glacier'])
    vector_dim: int = 384
    red_hot: Optional[MemoryTierConfig] = None
    hot: Optional[MemoryTierConfig] = None
    warm: Optional[MemoryTierConfig] = None
    cold: Optional[MemoryTierConfig] = None
    glacier: Optional[MemoryTierConfig] = None
    
    def __post_init__(self):
        """Initialize tier configurations."""
        if self.red_hot is None:
            self.red_hot = MemoryTierConfig(
                path="red_hot",
                max_size=1000000,
                memory_limit="1GB"
            )
        
        if self.hot is None:
            self.hot = MemoryTierConfig(
                path="hot", 
                max_size=104857600,
                memory_limit="2GB"
            )
        
        if self.warm is None:
            self.warm = MemoryTierConfig(
                path="warm",
                max_size=1073741824,
                memory_limit="8GB"
            )
        
        if self.cold is None:
            self.cold = MemoryTierConfig(
                path="cold",
                max_size=10737418240,
                memory_limit="4GB"
            )
        
        if self.glacier is None:
            self.glacier = MemoryTierConfig(
                path="glacier",
                max_size=107374182400,
                memory_limit="1GB"
            )
        
        super().__post_init__()

@dataclass
class SecurityConfig(ConfigSection):
    """Security configuration."""
    master_key: Optional[str] = None
    encryption_algorithm: str = "AES-256-GCM"
    key_rotation_days: int = 90
    max_login_attempts: int = 5
    session_timeout: int = 3600
    
    def validate(self):
        """Validate security configuration."""
        if self.master_key and len(self.master_key) < 32:
            raise ValidationError("Master key must be at least 32 characters")
        
        if self.encryption_algorithm not in ["AES-256-GCM", "AES-128-GCM", "ChaCha20-Poly1305"]:
            raise ValidationError("Unsupported encryption algorithm")

@dataclass
class LoggingConfig(ConfigSection):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    
    def validate(self):
        """Validate logging configuration."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValidationError(f"Invalid log level. Must be one of: {valid_levels}")

class ConfigManager(Singleton):
    """Centralized configuration manager.
    
    Provides a unified interface for loading, validating, and accessing
    configuration from multiple sources (files, environment variables, etc.).
    """
    
    def initialize(self):
        """Initialize the configuration manager."""
        self._config_cache: Dict[str, Any] = {}
        self._config_sources: List[str] = []
        self._environment_prefix = "MEMORIES_"
        
        # Configuration sections
        self.database: Optional[DatabaseConfig] = None
        self.redis: Optional[RedisConfig] = None
        self.memory: Optional[MemoryConfig] = None
        self.security: Optional[SecurityConfig] = None
        self.logging: Optional[LoggingConfig] = None
        
        # Load default configuration
        self.load_default_config()
        
        logger.info("Configuration manager initialized")
    
    def load_default_config(self):
        """Load default configuration values."""
        self.database = DatabaseConfig()
        self.redis = RedisConfig(
            url=os.getenv(f"{self._environment_prefix}REDIS_URL", "redis://localhost:6379"),
            db=int(os.getenv(f"{self._environment_prefix}REDIS_DB", "0"))
        )
        self.memory = MemoryConfig()
        self.security = SecurityConfig(
            master_key=os.getenv(f"{self._environment_prefix}MASTER_KEY")
        )
        self.logging = LoggingConfig(
            level=os.getenv(f"{self._environment_prefix}LOG_LEVEL", "INFO")
        )
    
    def load_from_file(self, config_path: Union[str, Path]) -> None:
        """Load configuration from a file.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    config_data = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {config_path.suffix}")
            
            self._merge_config(config_data)
            self._config_sources.append(str(config_path))
            
            logger.info(f"Loaded configuration from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    def load_from_environment(self, prefix: Optional[str] = None) -> None:
        """Load configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (default: MEMORIES_)
        """
        if prefix:
            self._environment_prefix = prefix
        
        env_config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self._environment_prefix):
                config_key = key[len(self._environment_prefix):].lower()
                
                # Handle nested configuration (e.g., MEMORIES_DATABASE_PATH)
                if '_' in config_key:
                    section, field = config_key.split('_', 1)
                    if section not in env_config:
                        env_config[section] = {}
                    env_config[section][field] = value
                else:
                    env_config[config_key] = value
        
        if env_config:
            self._merge_config(env_config)
            logger.info(f"Loaded configuration from environment variables with prefix {self._environment_prefix}")
    
    def _merge_config(self, config_data: Dict[str, Any]) -> None:
        """Merge configuration data into existing configuration.
        
        Args:
            config_data: Configuration data to merge
        """
        # Update database configuration
        if 'database' in config_data:
            db_config = config_data['database']
            if self.database:
                for key, value in db_config.items():
                    if hasattr(self.database, key):
                        setattr(self.database, key, value)
            else:
                self.database = DatabaseConfig(**db_config)
        
        # Update Redis configuration
        if 'redis' in config_data:
            redis_config = config_data['redis']
            if self.redis:
                for key, value in redis_config.items():
                    if hasattr(self.redis, key):
                        setattr(self.redis, key, value)
            else:
                self.redis = RedisConfig(**redis_config)
        
        # Update memory configuration
        if 'memory' in config_data:
            memory_config = config_data['memory']
            if self.memory:
                for key, value in memory_config.items():
                    if hasattr(self.memory, key) and not key.endswith('_config'):
                        setattr(self.memory, key, value)
            else:
                self.memory = MemoryConfig(**memory_config)
        
        # Update security configuration
        if 'security' in config_data:
            security_config = config_data['security']
            if self.security:
                for key, value in security_config.items():
                    if hasattr(self.security, key):
                        setattr(self.security, key, value)
            else:
                self.security = SecurityConfig(**security_config)
        
        # Update logging configuration
        if 'logging' in config_data:
            logging_config = config_data['logging']
            if self.logging:
                for key, value in logging_config.items():
                    if hasattr(self.logging, key):
                        setattr(self.logging, key, value)
            else:
                self.logging = LoggingConfig(**logging_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'database.path', 'redis.url')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key.split('.')
            value = self
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'database.path')
            value: Value to set
        """
        keys = key.split('.')
        obj = self
        
        for k in keys[:-1]:
            if hasattr(obj, k):
                obj = getattr(obj, k)
            else:
                raise ValueError(f"Configuration section '{k}' not found")
        
        final_key = keys[-1]
        if hasattr(obj, final_key):
            setattr(obj, final_key, value)
        else:
            raise ValueError(f"Configuration key '{final_key}' not found")
    
    def validate_all(self) -> List[str]:
        """Validate all configuration sections.
        
        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []
        
        sections = [
            ('database', self.database),
            ('redis', self.redis),
            ('memory', self.memory),
            ('security', self.security),
            ('logging', self.logging)
        ]
        
        for section_name, section in sections:
            if section:
                try:
                    section.validate()
                except ValidationError as e:
                    errors.append(f"{section_name}: {e}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        config_dict = {}
        
        if self.database:
            config_dict['database'] = self.database.to_dict()
        if self.redis:
            config_dict['redis'] = self.redis.to_dict()
        if self.memory:
            config_dict['memory'] = self.memory.to_dict()
        if self.security:
            # Don't export sensitive data
            security_dict = self.security.to_dict()
            security_dict.pop('master_key', None)
            config_dict['security'] = security_dict
        if self.logging:
            config_dict['logging'] = self.logging.to_dict()
        
        return config_dict
    
    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """Save configuration to file.
        
        Args:
            config_path: Path to save configuration file
        """
        config_path = Path(config_path)
        config_dict = self.to_dict()
        
        with open(config_path, 'w') as f:
            if config_path.suffix.lower() in ['.yml', '.yaml']:
                yaml.dump(config_dict, f, default_flow_style=False)
            elif config_path.suffix.lower() == '.json':
                json.dump(config_dict, f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {config_path.suffix}")
        
        logger.info(f"Saved configuration to {config_path}")
    
    def cleanup(self):
        """Clean up configuration manager resources."""
        self._config_cache.clear()
        logger.debug("Configuration manager cleaned up")

# Global configuration manager instance
def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    return ConfigManager()

# Convenience functions for backward compatibility
def load_config(config_path: Union[str, Path]) -> ConfigManager:
    """Load configuration from file and return manager."""
    manager = get_config()
    manager.load_from_file(config_path)
    return manager