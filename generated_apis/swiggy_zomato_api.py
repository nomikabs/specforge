from fastapi import FastAPI, Header, HTTPException, Depends
from typing import Optional

app = FastAPI(title='Generated API for swiggy_zomato')

HARDCODED_API_KEY = 'SWI-4054-ZOM'

def verify_api_key(api_key: Optional[str] = Header(None, alias='X-API-Key')):
    if not api_key or api_key != HARDCODED_API_KEY:
        raise HTTPException(status_code=401, detail='Invalid or missing X-API-Key header')
    return True

@app.get('/swiggytozomato', dependencies=[Depends(verify_api_key)])
def get_data():
    return {'status':'success','data':{'id': 'sample_id'}}

@app.get('/zomatotoswiggy', dependencies=[Depends(verify_api_key)])
def get_data():
    return {'status':'success','data':{'id': 'sample_id'}}

