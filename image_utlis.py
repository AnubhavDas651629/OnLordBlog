from fileinput import filename
import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps
from pydantic import FilePath

PROFILE_PICS_DIR = Path("media/profile_pics")

def process_profile_image(content: bytes) -> str:
    with Image.open(BytesIO(content)) as original:  # opening the image that we recieved as bytes
        img = ImageOps.exif_transpose(original)  # transpose fixes the orientation issue, mobile taken pohots have orientation problems
        img = ImageOps.fit(img, (300, 300), method= Image.Resampling.LANCZOS) # 300,300 pixels for each image, LANCZOS gives high quality resampling

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg" # over here using uuid4 we are generating unqiue file name, important for security
        FilePath = PROFILE_PICS_DIR / filename

        PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True) #checking if the parent directory exists, and if it does not make it, and exists_ok = true means if it alr exists it does not shows any errors

        img.save(FilePath, "JPEG", quality=85, optimize=True)

    return filename