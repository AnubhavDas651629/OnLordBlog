from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(  #basically loading sensitive data from a .env file
        env_file=".env",
        env_file_encoding="utf-8",
    )
    secret_key: SecretStr   # returns unrecognizable format of values
    # the secret_key maps to SECRET_KEY in the .env
    algorithm: str = "HS256"    #standard for json web tokens
    access_token_expire_minutes: int = 30

    max_upload_size_bytes: int = 5*1024*1024 #for pro pic purposees

    posts_per_page: int  = 10

    reset_token_expiration_minutes: int  = 60
    
    #email config

    mail_server:str = "localhost"
    mail_port: int = 587
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@example.com"
    mail_use_tls: bool = True

    frontend_url: str = "http://localhost:8000"

#loaded from .env file
#basically to use the sensitive values
settings = Settings() 



