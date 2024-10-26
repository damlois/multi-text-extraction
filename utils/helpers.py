from io import BytesIO
import zipfile
import aioboto3

def create_zip(images):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for filename, image_stream in images:
            zipf.writestr(filename, image_stream.getbuffer())
    zip_buffer.seek(0)
    return zip_buffer

def parse_page_range(page_range_str, num_pages):
    try:
        if not page_range_str:
            return list(range(num_pages))
        pages = []
        ranges = page_range_str.split(',')
        for range_str in ranges:
            if '-' in range_str:
                start, end = map(int, range_str.split('-'))
                pages.extend(range(start - 1, end))
            else:
                pages.append(int(range_str) - 1)
        pages = [p for p in pages if 0 <= p < num_pages]
        return pages if pages else None
    except (ValueError, TypeError):
        return None  # Invalid input

async def upload_image_to_s3(image_bytes, bucket_name, object_name):
    session = aioboto3.Session()
    async with session.client('s3') as s3_client:
        try:
            await s3_client.put_object(Bucket=bucket_name, Key=object_name, Body=image_bytes)
            print(f"Uploaded {object_name} to S3 bucket {bucket_name}.")
        except Exception as e:
            print(f"Failed to upload {object_name}: {e}")


