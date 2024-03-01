import os

from cognite.client import ClientConfig, global_config
from cognite.client.credentials import OAuthClientCredentials
from dotenv import load_dotenv

load_dotenv()

CDF_CLUSTER = os.environ["CDF_CLUSTER"]
CDF_TENANT_ID = os.environ["CDF_TENANT_ID"]
CDF_CLIENT_ID = os.environ["CDF_CLIENT_ID"]
CDF_CLIENT_SECRET = os.environ["CDF_CLIENT_SECRET"]
CDF_PROJECT = os.environ["CDF_PROJECT"]
CDF_CLIENT_NAME = os.environ["CDF_CLIENT_NAME"]

# This value will depend on the cluster your CDF project runs on
base_url = f"https://{CDF_CLUSTER}.cognitedata.com"

creds = OAuthClientCredentials(
    token_url=(
        f"https://login.microsoftonline.com/{CDF_TENANT_ID}/oauth2/v2.0/token"
    ),
    client_id=CDF_CLIENT_ID,
    client_secret=CDF_CLIENT_SECRET,
    scopes=[f"{base_url}/.default"],
)

cnf = ClientConfig(
    client_name=CDF_CLIENT_NAME,
    base_url=base_url,
    project=CDF_PROJECT,
    credentials=creds,
)

global_config.default_client_config = cnf
