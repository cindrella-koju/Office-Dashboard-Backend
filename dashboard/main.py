import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_CONNECTION_STRING")
print(db_url)