from fastapi import FastAPI, Header, HTTPException, Depends
from typing import Optional

app = FastAPI(title='Generated API for instagram_swiggy')

HARDCODED_API_KEY = 'INS-6282-SWI'

@app.get('/instagramtoswiggy')
def get_data():
    return {'status':'success','data':{'name': 'sample_name'}}

@app.get('/swiggytoinstagram')
def get_data():
    return {'status':'success','data':{'name': 'sample_name'}}

