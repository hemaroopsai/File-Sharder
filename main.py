import os
import zipfile
import io
import logging # <-- Import the logging module
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from logic import split_and_encrypt, join_and_decrypt

# --- SETUP LOGGING ---
# This will help us see detailed errors in the Docker logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# ---------------------

app = FastAPI()

# Allow all origins for CORS, which is necessary for the browser
# to communicate with the server from a file:// URL or different domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW ENDPOINT TO SERVE THE FRONTEND ---
@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """
    This endpoint serves the main index.html file when a user visits the root URL.
    """
    return "index.html"
# -----------------------------------------


@app.post("/split")
async def http_split_file(pieces: int = Form(...), file: UploadFile = File(...)):
    """
    API endpoint to split a file. Receives a file and the number of pieces,
    returns a zip archive of the encrypted chunks, manifest, and key.
    """
    try:
        contents = await file.read()
        
        # This function returns a dictionary of filenames and their byte content
        split_files = split_and_encrypt(
            original_filename=file.filename,
            data=contents,
            pieces=pieces
        )

        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, file_bytes in split_files.items():
                zip_file.writestr(filename, file_bytes)
        
        # Go to the beginning of the buffer before sending the response
        zip_buffer.seek(0)

        # Use StreamingResponse to send the zip file
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={file.filename}.zip"}
        )
    except Exception as e:
        # --- ADDED DETAILED LOGGING ---
        # This will print the full error traceback to the console
        logger.error(f"An error occurred during file splitting: {e}", exc_info=True)
        # ------------------------------
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


@app.post("/join")
async def http_join_files(files: List[UploadFile] = File(...)):
    """
    API endpoint to join files. Receives a list of files (chunks, manifest, key)
    and returns the reconstructed, original file.
    """
    try:
        file_data = {file.filename: await file.read() for file in files}
        original_filename, decrypted_data = join_and_decrypt(file_data)

        return StreamingResponse(
            io.BytesIO(decrypted_data),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={original_filename}"}
        )
    except Exception as e:
        # --- ADDED DETAILED LOGGING ---
        logger.error(f"An error occurred during file joining: {e}", exc_info=True)
        # ------------------------------
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

