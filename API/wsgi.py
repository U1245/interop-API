"""
Resume:
    InterOP API - Parsing & serving the InterOP data

Description:
      Run the flask API.

Author(s):
    Steeve Fourneaux
Date(s):
    2022
Credits:
    Steeve Fourneaux
"""

from .routes import app

if __name__ == "__main__":
    app.run()