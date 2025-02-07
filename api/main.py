from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
import boto3
import os
import re
from io import BytesIO
from dotenv import load_dotenv
import logging

# Load Environment Variables
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

# Ensure AWS credentials are available
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "qr-code-project-bucket-aws")

if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
    raise RuntimeError("AWS credentials are missing. Check your .env file.")

# Initialize FastAPI app
app = FastAPI()

# Allowing CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow any frontend origin (change as needed)
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS S3 Configuration
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# Define a Pydantic model for request validation
class QRRequest(BaseModel):
    url: str

@app.post("/generate-qr/")
async def generate_qr(url: str = Query(None), request: QRRequest = None):
    """
    Generates a QR Code, uploads it to S3, and returns the public URL.
    Supports both Query Parameters and JSON Body.
    """
    url = url or (request.url if request else None)

    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http or https.")

    try:
        logging.debug(f"Generating QR Code for URL: {url}")

        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save QR Code to BytesIO object
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        # Generate file name for S3 (sanitize URL)
        safe_url = re.sub(r"[^\w\-]", "_", url)  # Replace special characters with underscores
        file_name = f"qr_codes/{safe_url}.png"

        logging.debug(f"Uploading QR Code to S3 with file name: {file_name}")

        # Upload to S3 (Removed ACL='public-read' since S3 bucket blocks ACLs)
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=img_byte_arr,
            ContentType="image/png",
        )

        # Generate the S3 URL
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_name}"
        logging.debug(f"Generated QR Code URL: {s3_url}")
        return {"qr_code_url": s3_url}

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating QR Code: {str(e)}")
