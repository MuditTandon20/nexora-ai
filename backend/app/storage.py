import io
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
from pypdf import PdfReader
from .config import settings

MAX_PDF = 10 * 1024 * 1024


def s3_client():
    import boto3
    cfg = settings()
    return boto3.client('s3', endpoint_url=cfg.s3_endpoint_url, region_name=cfg.aws_region)


async def read_pdf(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith('.pdf') or file.content_type != 'application/pdf':
        raise HTTPException(422, 'Only PDF files are accepted')
    data = await file.read(MAX_PDF + 1)
    if len(data) > MAX_PDF:
        raise HTTPException(413, 'PDF must be smaller than 10 MB')
    if not data.startswith(b'%PDF-'):
        raise HTTPException(422, 'Invalid PDF signature')
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted or len(reader.pages) > 100:
            raise ValueError('Encrypted or too many pages')
        content = '\n'.join((page.extract_text() or '') for page in reader.pages)
        if len(content.strip()) < 30 or len(content) > 60000:
            raise ValueError('Need 30–60,000 characters of readable text; scanned PDFs need OCR first')
    except Exception as exc:
        raise HTTPException(422, 'Upload a readable, unencrypted PDF with at most 100 pages and 60,000 text characters') from exc
    return data, content


def store_pdf(school_id, data):
    key = f'{school_id}/{uuid.uuid4().hex}.pdf'
    if settings().storage_backend == 's3':
        s3_client().put_object(Bucket=settings().s3_bucket, Key=key, Body=data, ContentType='application/pdf', ServerSideEncryption='AES256')
    else:
        target = Path(settings().upload_dir) / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return key


def load_pdf(key):
    if settings().storage_backend == 's3':
        return s3_client().get_object(Bucket=settings().s3_bucket, Key=key)['Body'].read()
    return (Path(settings().upload_dir) / key).read_bytes()
