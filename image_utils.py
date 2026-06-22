import boto3
from fileinput import filename
import uuid
from io import BytesIO
from PIL import Image, ImageOps
from pydantic import FilePath
import boto3
from starlette.concurrency import run_in_threadpool

from config import settings

def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id=(
            settings.s3_access_key_id.get_secret_value()
            if settings.s3_access_key_id
            else None
        ),
        aws_secret_access_key = (
            settings.s3_secret_access_key.get_secret_value()
            if settings.s3_secret_access_key
            else None
        ),
        endpoint_url=settings.s3_endpoint_url,
    )

def process_profile_image(content: bytes) -> tuple[bytes, str]:
    with Image.open(BytesIO(content)) as original:  # opening the image that we recieved as bytes
        img = ImageOps.exif_transpose(original)  # transpose fixes the orientation issue, mobile taken pohots have orientation problems
        img = ImageOps.fit(img, (300, 300), method= Image.Resampling.LANCZOS) # 300,300 pixels for each image, LANCZOS gives high quality resampling

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg" # over here using uuid4 we are generating unqiue file name, important for security

        output = BytesIO()
        img.save(output, "JPEG", quality=85, optimize=True)
        
        output.seek(0) # moving to the begining of the file

    return output.read(), filename

