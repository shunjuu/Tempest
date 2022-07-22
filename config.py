
from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    environments=False,
    envvar_prefix="YUKIKO",
    env_switcher="YUKIKO_ENV",
    fresh_vars=[
        'RABBITMQ_USERNAME',
        'RABBITMQ_PASSWORD',
        'RABBITMQ_HOST',
        'RABBITMQ_PORT',
        'RABBITMQ_VHOST',
        'RCLONE_CONFIG_FILE',
        'RCLONE_FLAGS',
        'TEMPEST_FFMPEG_ENCODE_FLAGS',
        'TEMPEST_RABBITMQ_QUEUE',
        'TEMPEST_PUBLISH_EXCHANGE',
        'TEMPEST_RCLONE_DOWNLOAD_SOURCES',
        'TEMPEST_RCLONE_UPLOAD_DESTS',
    ],
    load_dotenv=False,
    redis_enabled=False,
    settings_files=['settings.toml', '.secrets.toml'],
    vault_enabled=False,
    validators=[
        Validator('RABBITMQ_HOST', is_type_of=str, must_exist=True),
        Validator('RABBITMQ_PORT', is_type_of=int, must_exist=True),
        Validator('RABBITMQ_VHOST', is_type_of=str, must_exist=True),
        Validator('RABBITMQ_USERNAME', is_type_of=str, must_exist=True),
        Validator('RABBITMQ_PASSWORD', is_type_of=str, must_exist=True),
        Validator('RCLONE_CONFIG_FILE', is_type_of=str, must_exist=True),
        Validator('RCLONE_FLAGS', is_type_of=str),
        Validator('TEMPEST_FFMPEG_ENCODE_FLAGS', is_type_of=str),
        Validator('TEMPEST_RABBITMQ_QUEUE', is_type_of=str, must_exist=True),
        Validator('TEMPEST_PUBLISH_EXCHANGE', is_type_of=str, must_exist=True),
        Validator('TEMPEST_RCLONE_DOWNLOAD_SOURCES', is_type_of=list, must_exist=True),
        Validator('TEMPEST_RCLONE_UPLOAD_DESTS', is_type_of=list, must_exist=True),
    ]
)

# `envvar_prefix` = export envvars with `export YUKIKO_FOO=bar`.
# `settings_files` = Load this files in the order.
