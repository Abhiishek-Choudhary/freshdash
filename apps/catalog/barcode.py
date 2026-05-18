def decode_barcode_from_image(image_file) -> str | None:
    """Decode barcode from uploaded image when pyzbar is installed."""
    try:
        from PIL import Image
        from pyzbar.pyzbar import decode as pyzbar_decode
    except ImportError:
        return None

    image = Image.open(image_file)
    codes = pyzbar_decode(image)
    for code in codes:
        value = code.data.decode("utf-8", errors="ignore").strip()
        if value:
            return value
    return None
