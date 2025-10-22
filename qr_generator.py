"""
QR Code Generator for Photo Registration System

Generates QR codes containing personal data for photo identification.
QR codes are embedded in confirmation emails and held by customers during photo sessions.
"""

import qrcode
from qrcode.image.pil import PilImage
import os
from io import BytesIO
import base64
from typing import Optional
from PIL import Image

# QR Code configuration
QR_VERSION = 1  # Controls size (1-40, None for auto)
QR_ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_H  # High error correction (30%)
QR_BOX_SIZE = 10  # Size of each box in pixels
QR_BORDER = 4  # Border size in boxes
QR_FILL_COLOR = "black"
QR_BACK_COLOR = "white"


def generate_qr_data(first_name: str, last_name: str, email: str, registration_id: int, qr_token: str) -> str:
    """
    Generate QR code data string with personal information.
    
    Format: first_name|last_name|email|registration_id|qr_token
    Using pipe (|) as separator for easy parsing and visual clarity.
    
    Args:
        first_name: Customer's first name
        last_name: Customer's last name
        email: Customer's email address
        registration_id: Database registration ID
        qr_token: Unique UUID token for this registration
    
    Returns:
        Formatted QR data string
    
    Example:
        "John|Doe|john@example.com|123|a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    """
    return f"{first_name}|{last_name}|{email}|{registration_id}|{qr_token}"


def parse_qr_data(qr_data: str) -> Optional[dict]:
    """
    Parse QR code data string into components.
    
    Args:
        qr_data: QR code data string
    
    Returns:
        Dictionary with parsed data or None if invalid format
        
    Example:
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'registration_id': 123,
            'qr_token': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        }
    """
    try:
        parts = qr_data.split('|')
        if len(parts) != 5:
            return None
        
        first_name, last_name, email, reg_id, qr_token = parts
        
        return {
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'email': email.strip(),
            'registration_id': int(reg_id.strip()),
            'qr_token': qr_token.strip()
        }
    except (ValueError, IndexError):
        return None


def create_qr_code(data: str, size: int = 300) -> PilImage:
    """
    Create a QR code image from data string.
    
    Args:
        data: Data to encode in QR code
        size: Desired size in pixels (will be adjusted to fit QR code)
    
    Returns:
        PIL Image object containing the QR code
    """
    qr = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=QR_ERROR_CORRECTION,
        box_size=QR_BOX_SIZE,
        border=QR_BORDER,
    )
    
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image with specified colors
    img = qr.make_image(fill_color=QR_FILL_COLOR, back_color=QR_BACK_COLOR)
    
    # Resize if needed (maintaining aspect ratio)
    if size:
        # Use Image.LANCZOS instead of PilImage.LANCZOS (Pillow 10+ compatibility)
        img = img.resize((size, size), resample=Image.LANCZOS)
    
    return img


def generate_qr_code_for_registration(
    first_name: str,
    last_name: str,
    email: str,
    registration_id: int,
    qr_token: str,
    size: int = 300
) -> PilImage:
    """
    Generate a QR code for a registration with personal data.
    
    This is the main function to use for generating QR codes.
    
    Args:
        first_name: Customer's first name
        last_name: Customer's last name
        email: Customer's email address
        registration_id: Database registration ID
        qr_token: Unique UUID token for this registration
        size: QR code size in pixels (default: 300x300)
    
    Returns:
        PIL Image object containing the QR code
    
    Usage:
        qr_img = generate_qr_code_for_registration(
            "John", "Doe", "john@example.com", 123, "uuid-token-here"
        )
        qr_img.save("qr_code.png")
    """
    qr_data = generate_qr_data(first_name, last_name, email, registration_id, qr_token)
    return create_qr_code(qr_data, size)


def qr_code_to_base64(qr_image: PilImage, format: str = 'PNG') -> str:
    """
    Convert QR code image to base64 string for embedding in HTML.
    
    Args:
        qr_image: PIL Image object
        format: Image format (PNG, JPEG, etc.)
    
    Returns:
        Base64 encoded string ready for data URI
        
    Usage:
        base64_str = qr_code_to_base64(qr_img)
        html = f'<img src="data:image/png;base64,{base64_str}">'
    """
    buffered = BytesIO()
    qr_image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def qr_code_to_bytes(qr_image: PilImage, format: str = 'PNG') -> bytes:
    """
    Convert QR code image to bytes for file serving.
    
    Args:
        qr_image: PIL Image object
        format: Image format (PNG, JPEG, etc.)
    
    Returns:
        Image bytes
        
    Usage:
        img_bytes = qr_code_to_bytes(qr_img)
        # Can be served via Flask's send_file
    """
    buffered = BytesIO()
    qr_image.save(buffered, format=format)
    return buffered.getvalue()


def save_qr_code(qr_image: PilImage, filepath: str) -> None:
    """
    Save QR code image to file.
    
    Args:
        qr_image: PIL Image object
        filepath: Path where to save the image
    
    Usage:
        save_qr_code(qr_img, "qr_codes/registration_123.png")
    """
    # Ensure directory exists
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    qr_image.save(filepath)


def generate_qr_code_inline(
    first_name: str,
    last_name: str,
    email: str,
    registration_id: int,
    qr_token: str,
    size: int = 300
) -> str:
    """
    Generate QR code and return as base64 data URI for inline embedding.
    
    This is a convenience function that combines generation and encoding.
    Perfect for embedding in emails.
    
    Args:
        first_name: Customer's first name
        last_name: Customer's last name
        email: Customer's email address
        registration_id: Database registration ID
        qr_token: Unique UUID token
        size: QR code size in pixels (default: 300x300)
    
    Returns:
        Complete data URI string ready for <img src="...">
        
    Usage:
        data_uri = generate_qr_code_inline("John", "Doe", "john@email.com", 123, "token")
        html = f'<img src="{data_uri}" alt="QR Code">'
    """
    qr_img = generate_qr_code_for_registration(
        first_name, last_name, email, registration_id, qr_token, size
    )
    base64_str = qr_code_to_base64(qr_img)
    return f"data:image/png;base64,{base64_str}"


def generate_qr_code(person_data: dict, output_format: str = 'data_uri', size: int = 300):
    """
    Generate QR code from person data dictionary with flexible output format.
    
    This function handles the format used in send_email.py where person data
    includes first_name, last_name, email, and registration_id.
    
    Args:
        person_data: Dictionary with person information
            Required keys: first_name, last_name, email, registration_id
            Optional keys: qr_token
        output_format: Output format - 'data_uri', 'bytes', or 'image'
        size: QR code size in pixels (default: 300x300)
    
    Returns:
        - 'data_uri': Complete data URI string for inline HTML
        - 'bytes': Raw image bytes for file serving
        - 'image': PIL Image object
    
    Usage:
        # For email embedding
        data_uri = generate_qr_code(person_data, output_format='data_uri')
        
        # For HTTP response
        img_bytes = generate_qr_code(person_data, output_format='bytes')
    """
    # Extract data from dictionary
    first_name = person_data.get('first_name', '')
    last_name = person_data.get('last_name', '')
    email = person_data.get('email', '')
    registration_id = person_data.get('registration_id', 0)
    qr_token = person_data.get('qr_token', '')
    
    # Generate QR data string
    qr_data = generate_qr_data(first_name, last_name, email, registration_id, qr_token)
    
    # Create QR code image
    qr_img = create_qr_code(qr_data, size)
    
    # Return in requested format
    if output_format == 'data_uri':
        base64_str = qr_code_to_base64(qr_img)
        return f"data:image/png;base64,{base64_str}"
    elif output_format == 'bytes':
        return qr_code_to_bytes(qr_img)
    elif output_format == 'image':
        return qr_img
    else:
        raise ValueError(f"Unknown output format: {output_format}")


# Example usage and testing
if __name__ == '__main__':
    # Test QR code generation
    print("=" * 60)
    print("Testing QR Code Generator")
    print("=" * 60)
    print()
    
    # Test data
    test_data = generate_qr_data(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        registration_id=123,
        qr_token="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    )
    print(f"✓ QR Data Generated:")
    print(f"  {test_data}")
    print()
    
    # Test parsing
    parsed = parse_qr_data(test_data)
    print(f"✓ QR Data Parsed:")
    for key, value in parsed.items():
        print(f"  {key}: {value}")
    print()
    
    # Generate QR code
    qr_img = create_qr_code(test_data, size=300)
    print(f"✓ QR Code Image Generated:")
    print(f"  Size: {qr_img.size[0]}x{qr_img.size[1]} pixels")
    print()
    
    # Test base64 encoding
    base64_str = qr_code_to_base64(qr_img)
    data_uri = f"data:image/png;base64,{base64_str}"
    print(f"✓ Base64 Encoding:")
    print(f"  Base64 length: {len(base64_str)} characters")
    print(f"  Data URI length: {len(data_uri)} characters")
    print()
    
    # Save test QR code
    test_file = "test_qr_code.png"
    save_qr_code(qr_img, test_file)
    print(f"✓ Test QR Code Saved:")
    print(f"  File: {test_file}")
    print()
    
    print("=" * 60)
    print("✅ QR Code Generator is working correctly!")
    print("=" * 60)
    print()
    print("You can now:")
    print("  1. Scan test_qr_code.png with a QR scanner")
    print("  2. Verify the data matches the input")
    print(f"  3. Expected data: {test_data}")
