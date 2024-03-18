from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    DEBUG: str
    APP_HOST: str
    APP_PORT: int
    DATA_FILE: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

config = Config()

    