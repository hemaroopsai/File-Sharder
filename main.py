import zipfile
import io
import logging
import tempfile
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from logic import split_and_encrypt, join_and_decrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 Megabytes

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=FileResponse)
async def serve_frontend():
    return "index.html"

@app.post("/split")
async def http_split_file(pieces: int = Form(...), file: UploadFile = File(...)):
    # Create a secure temporary directory to work in
    temp_dir = tempfile.mkdtemp()
    try:
        file_contents = await file.read()
        
        if len(file_contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds the limit of {MAX_FILE_SIZE / 1024 / 1024} MB."
            )
            
        # The logic function now writes files to the temp dir instead of returning them
        split_and_encrypt(
            original_filename=file.filename,
            data=file_contents,
            pieces=pieces,
            temp_dir=Path(temp_dir)
        )
        
        # Create the zip archive from the files on disk
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for item in Path(temp_dir).iterdir():
                zip_file.write(item, item.name)
        
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={file.filename}.zip"}
        )
    except Exception as e:
        logger.error(f"Error during file splitting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # CRUCIAL: Clean up the temporary directory and all its contents
        shutil.rmtree(temp_dir)


@app.post("/join")
async def http_join_files(files: List[UploadFile] = File(...)):
    # Create a secure temporary directory to work in
    temp_dir = tempfile.mkdtemp()
    try:
        # Save all uploaded files to the temporary directory on disk
        for file in files:
            file_path = Path(temp_dir) / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        # The logic function now reads files from the temp dir
        original_filename, decrypted_data = join_and_decrypt(Path(temp_dir))
        
        return StreamingResponse(
            io.BytesIO(decrypted_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={original_filename}"}
        )
    except Exception as e:
        logger.error(f"Error during file joining: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # CRUCIAL: Clean up the temporary directory and all its contents
        shutil.rmtree(temp_dir)

