import asyncio

from app.services.prescription_ocr import extract_text_from_image


async def main():
    print("Starting OCR...")

    result = await extract_text_from_image("1.webp")

    print("\n--- EXTRACTED JSON ---\n")
    print(result)

    print("\nOCR finished.")


if __name__ == "__main__":
    asyncio.run(main())