import os

bind = f"0.0.0.0:{int(os.getenv('PORT', '8000'))}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
accesslog = "-"
errorlog = "-"
