from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "sqlite+aiosqlite:///./slurmpp.db"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Auth backend
    auth_backend: Literal["local", "ldap"] = "local"
    ldap_url: str = ""
    ldap_base_dn: str = ""
    ldap_user_dn_template: str = "uid={username},ou=people,{base_dn}"
    ldap_admin_group_dn: str = ""

    # Slurm interface
    slurm_interface: Literal["auto", "rest", "cli", "mock"] = "auto"
    slurm_rest_url: str = "http://localhost:6820"
    slurm_rest_token: str = ""
    slurm_rest_version: str = "v0.0.43"

    # Poller intervals (seconds)
    poll_jobs_interval: int = 15
    poll_nodes_interval: int = 60
    poll_accounting_interval: int = 300

    # Analytics retention (days)
    analytics_retention_days: int = 90
    operational_retention_hours: int = 24

    # App
    app_title: str = "slurm++"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
