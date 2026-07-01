import sys
import logging
from app import app
with app.test_client() as client:
    response = client.get('/dashboard')
    print("Status code:", response.status_code)
    if response.status_code == 200:
        print("Success! Dashboard rendered.")
    else:
        print("Error!")
        print(response.data.decode('utf-8'))
