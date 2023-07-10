import urllib.parse as up

owners = [380697024120487939,]
token = "MTExOTY0OTI3MDUyMjQ2MjI2Mg.GZVdFv.S2qdirpg_2W6xNIBFNelBEbsXHggoM0F2nrfWc"
paypal_client_id = (
    "AeFiqh0QC0AqTXmflgxWUEEyx_DcoEm8jLmsUvVSbCRS7aX53B0ctnrNirGHbsPmHr20GWb2mLFWOUdU"
)
paypal_client_secret = (
    "EK7fyD38EFCRVcn7tw2NyqHzptBmK2Lrxxi3aOeR_eYngzCe2RAhc5fL1vQ9ukP4h3ea6vTrYcnItmvM"
)

db_url = "postgres://ydrxcjts:Bbtlk8Wbbtf9O-poKTuSoT0nMN5I6SfD@stampy.db.elephantsql.com/ydrxcjts"
up.uses_netloc.append("postgres")
url = up.urlparse(db_url)

tortoise_config = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": url.hostname,
                "port": 5432,
                "user": url.username,
                "password": url.password,
                "database": url.path[1:],
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
