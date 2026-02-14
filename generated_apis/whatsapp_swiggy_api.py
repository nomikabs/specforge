from fastapi import FastAPI, Header, HTTPException, Depends
from typing import Optional

app = FastAPI(title='Generated API for whatsapp_swiggy')

HARDCODED_API_KEY = 'WHA-0153-SWI'

def verify_api_key(api_key: Optional[str] = Header(None, alias='X-API-Key')):
    if not api_key or api_key != HARDCODED_API_KEY:
        raise HTTPException(status_code=401, detail='Invalid or missing X-API-Key header')
    return True

@app.get('/whatsapptoswiggy', dependencies=[Depends(verify_api_key)])
def get_data():
    return {'status':'success','data':{'name': 'sample_name'}}

@app.get('/swiggytowhatsapp', dependencies=[Depends(verify_api_key)])
def get_data():
    return {'status':'success','data':{'name': 'sample_name'}}

