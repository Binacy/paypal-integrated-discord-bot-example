owners = [] #<-- list of owner ids (of bot)
token = "" #<-- bot token
paypal_client_id = ""
paypal_client_secret = ""

tortoise_config = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "hostname", 
                "port": 5432,
                "user": "username",
                "password": "password",
                "database": "database",
            },
        },
    },
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "Asia/Kolkata",
}
