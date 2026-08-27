import asyncio
import json

from app.services.prescription_ocr import extract_text_from_image


async def main():

    image_path = "1.webp"

    print("Starting OCR...")

    try:
        result = await extract_text_from_image(image_path)

        print("\n--- EXTRACTED JSON ---\n")

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

        print("\nOCR finished.")

    except Exception as e:

        print("\nOCR FAILED")
        print(type(e).__name__)
        print(str(e))


if __name__ == "__main__":
    asyncio.run(main())