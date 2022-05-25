from fastapi import FastAPI

app = FastAPI()
notesArray = []
@app.get('/get-notes')
async def root():
  return {"Message": "notesArray"}