from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from fastapi.responses import JSONResponse

document_router = APIRouter(prefix="/document")

@document_router.post("/learn", tags = ["document"], description = "문서 학습")
async def learn_file(
    files : list[UploadFile] = File(...),
    chat_bot_id : str = Form(...),
    db_name : str = Form(...),
    mb_id : str = Form(...),
    mb_name : str = Form(...),
):
    try:
        print(f"files : {files}")
        print(f"chat_bot_id : {chat_bot_id}")
        print(f"db_name : {db_name}")
        print(f"mb_id : {mb_id}")
        print(f"mb_name : {mb_name}")

        

        JSONResponse(content = {
            "message" : "File uploaded successfully",
            "status_code" : 200
        }, status_code = 200)

    except Exception as e:
        return JSONResponse(content = {
            "message" : f"Error : {e}",
            "status_code" : 500
        }, status_code = 500)



