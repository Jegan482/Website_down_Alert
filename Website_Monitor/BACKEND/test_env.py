from dotenv import load_dotenv
load_dotenv()

import os
print("MONGO_URI =", os.getenv("MONGO_URI"))
print("SMTP_USER =", os.getenv("SMTP_USER"))
