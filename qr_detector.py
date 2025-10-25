"""
QR Code Detection Module for Photo Registration System

This module handles QR code detection in uploaded photos. It uses OpenCV and pyzbar
to scan photos for QR codes containing registration data.

QR Code Format: first_name|last_name|email|registration_id|qr_token
Example: John|Doe|john@example.com|123|a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6

Dependencies:
- opencv-python: Image processing
- pyzbar: QR code decoding
"""

import cv2
import numpy as np
from pyzbar import pyzbar
import logging
from typing import Dict, Optional, Tuple, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QRDetectionResult:
    """Container for QR detection results"""
    
    def __init__(self, detected: bool = False, qr_data: Optional[str] = None, 
                 parsed_data: Optional[Dict] = None, error: Optional[str] = None):
        self.detected = detected
        self.qr_data = qr_data
        self.parsed_data = parsed_data
        self.error = error
    
    def to_dict(self):
        """Convert result to dictionary"""
        return {
            'detected': self.detected,
            'qr_data': self.qr_data,
            'parsed_data': self.parsed_data,
            'error': self.error
        }


def parse_qr_data(qr_string: str) -> Optional[Dict]:
    """
    Parse QR code data string into structured dictionary.
    
    Format: first_name|last_name|email|registration_id|qr_token
    
    Args:
        qr_string: Raw QR code string data
        
    Returns:
        Dictionary with parsed fields or None if parsing fails
        
    Example:
        >>> parse_qr_data("John|Doe|john@example.com|123|abc-123")
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'registration_id': '123',
            'qr_token': 'abc-123'
        }
    """
    try:
        if not qr_string or not isinstance(qr_string, str):
            logger.warning(f"Invalid QR string: {qr_string}")
            return None
        
        # Split by pipe separator
        parts = qr_string.split('|')
        
        if len(parts) != 5:
            logger.warning(f"QR string has {len(parts)} parts, expected 5: {qr_string}")
            return None
        
        # Parse into dictionary
        parsed = {
            'first_name': parts[0].strip(),
            'last_name': parts[1].strip(),
            'email': parts[2].strip().lower(),
            'registration_id': parts[3].strip(),
            'qr_token': parts[4].strip()
        }
        
        # Validate required fields are not empty
        if not all(parsed.values()):
            logger.warning(f"QR data contains empty fields: {parsed}")
            return None
        
        # Validate registration_id is numeric
        try:
            int(parsed['registration_id'])
        except ValueError:
            logger.warning(f"Invalid registration_id (not numeric): {parsed['registration_id']}")
            return None
        
        logger.info(f"Successfully parsed QR data for {parsed['first_name']} {parsed['last_name']}")
        return parsed
        
    except Exception as e:
        logger.error(f"Error parsing QR data '{qr_string}': {str(e)}")
        return None


def validate_qr_data_against_registration(parsed_data: Dict, registration: object) -> bool:
    """
    Validate parsed QR data against a Registration database object.
    
    Args:
        parsed_data: Parsed QR code data dictionary
        registration: Registration model object from database
        
    Returns:
        True if data matches, False otherwise
    """
    try:
        # Check if registration exists
        if not registration:
            logger.warning("No registration object provided for validation")
            return False
        
        # Check registration_id match (PRIMARY validation)
        if str(registration.id) != parsed_data['registration_id']:
            logger.warning(f"Registration ID mismatch: QR={parsed_data['registration_id']}, DB={registration.id}")
            return False
        
        # Check QR token match (PRIMARY validation - most secure)
        if registration.qr_token and registration.qr_token != parsed_data['qr_token']:
            logger.warning(f"QR token mismatch for registration {registration.id}")
            return False
        
        # If registration_id AND qr_token match, it's valid!
        # We don't check name/email because of potential Unicode encoding issues
        # (ü vs ü, ö vs ö, etc.) and the token is already cryptographically unique
        
        logger.info(f"QR data validated successfully for registration {registration.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error validating QR data: {str(e)}")
        return False


def detect_qr_in_image(image_path: str, enhance: bool = True) -> QRDetectionResult:
    """
    Detect and decode QR code in an image file.
    
    This function attempts multiple detection strategies:
    1. Direct detection on original image (downscaled for speed)
    2. Detection on grayscale image (only if enhance=True)
    3. Detection on enhanced contrast image (only if enhance=True)
    
    Args:
        image_path: Path to the image file
        enhance: Whether to try enhanced processing for difficult QR codes
        
    Returns:
        QRDetectionResult object with detection results
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return QRDetectionResult(detected=False, error="File not found")
        
        # Read image
        image = cv2.imread(image_path)
        
        if image is None:
            logger.error(f"Failed to read image: {image_path}")
            return QRDetectionResult(detected=False, error="Failed to read image")
        
        # Keep original image for small QR code detection
        original_image = image.copy()
        height, width = image.shape[:2]
        
        # OPTIMIZATION: Downscale large images for faster QR detection (fast mode only)
        # In enhance mode, we'll also try full resolution for small QR codes
        max_dimension = 1200  # Sufficient for most QR detection
        downscaled = False
        
        if width > max_dimension or height > max_dimension:
            scale = max_dimension / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            downscaled = True
            logger.debug(f"Downscaled image from {width}x{height} to {new_width}x{new_height}")
        
        # Strategy 1: Try detecting on downscaled image (FAST)
        logger.debug(f"Attempting QR detection on image: {image_path}")
        result = _try_decode_qr(image)
        if result.detected:
            return result
        
        # If no QR found and enhance=False, stop here (FAST PATH for photos without QR)
        if not enhance:
            logger.debug(f"No QR code detected in image (fast mode): {image_path}")
            return QRDetectionResult(detected=False, error="No QR code found")
        
        # Strategy 2: Try grayscale conversion (only if enhance=True)
        logger.debug("Trying grayscale conversion...")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        result = _try_decode_qr(gray)
        if result.detected:
            return result
        
        # Strategy 3: Try enhanced processing (only if enhance=True and still not found)
        logger.debug("Trying enhanced processing...")
        
        # Increase contrast
        enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        result = _try_decode_qr(enhanced)
        if result.detected:
            return result
        
        # Try adaptive thresholding (last resort)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        result = _try_decode_qr(thresh)
        if result.detected:
            return result
        
        # Strategy 4: Multiple preprocessing techniques for difficult cases (phone screens, glare)
        logger.debug("Trying advanced preprocessing for phone screens...")
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization) - great for uneven lighting
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        clahe_enhanced = clahe.apply(gray)
        result = _try_decode_qr(clahe_enhanced)
        if result.detected:
            return result
        
        # Bilateral filter to reduce noise while preserving edges
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        result = _try_decode_qr(bilateral)
        if result.detected:
            return result
        
        # Sharpen the image (helps with slightly blurry QR codes)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        result = _try_decode_qr(sharpened)
        if result.detected:
            return result
        
        # Gamma correction for screen glare
        gamma = 1.5
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        gamma_corrected = cv2.LUT(gray, table)
        result = _try_decode_qr(gamma_corrected)
        if result.detected:
            return result
        
        # Strategy 5: Try full resolution if image was downscaled (for SMALL QR codes)
        if downscaled:
            logger.debug("Trying full resolution for small QR codes...")
            
            # Convert original image to grayscale at full resolution
            gray_full = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
            
            # Try original full resolution
            result = _try_decode_qr(gray_full)
            if result.detected:
                return result
            
            # Try CLAHE on full resolution (best for small QR codes)
            clahe_full = clahe.apply(gray_full)
            result = _try_decode_qr(clahe_full)
            if result.detected:
                return result
            
            # Try sharpening on full resolution
            sharpened_full = cv2.filter2D(gray_full, -1, kernel)
            result = _try_decode_qr(sharpened_full)
            if result.detected:
                return result
        
        # Strategy 6: Advanced thresholding techniques (for tilted QR codes, phone screens)
        logger.debug("Trying advanced thresholding techniques...")
        
        # Otsu's thresholding (automatic threshold selection)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        result = _try_decode_qr(otsu)
        if result.detected:
            return result
        
        # Try inverse Otsu (sometimes QR is inverted on screen)
        _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        result = _try_decode_qr(otsu_inv)
        if result.detected:
            return result
        
        # Median blur + Otsu (reduces noise before thresholding)
        median_blur = cv2.medianBlur(gray, 5)
        _, otsu_median = cv2.threshold(median_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        result = _try_decode_qr(otsu_median)
        if result.detected:
            return result
        
        # Morphological operations to clean up the image
        kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        morph = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel_morph)
        result = _try_decode_qr(morph)
        if result.detected:
            return result
        
        # No QR code detected after all strategies
        logger.info(f"No QR code detected in image: {image_path}")
        return QRDetectionResult(detected=False, error="No QR code found")
        
    except Exception as e:
        logger.error(f"Error detecting QR code in {image_path}: {str(e)}")
        return QRDetectionResult(detected=False, error=str(e))


def _try_decode_qr(image: np.ndarray) -> QRDetectionResult:
    """
    Internal helper to attempt QR code decoding on an image.
    Uses multiple decoders for best compatibility.
    
    Args:
        image: OpenCV image (numpy array)
        
    Returns:
        QRDetectionResult object
    """
    try:
        # Method 1: Try pyzbar (generally more robust)
        qr_codes = pyzbar.decode(image)
        
        if qr_codes:
            # Process first QR code found (we expect only one per photo)
            qr_code = qr_codes[0]
            
            # Decode data
            qr_data = qr_code.data.decode('utf-8')
            
            # Parse QR data
            parsed_data = parse_qr_data(qr_data)
            
            if parsed_data:
                logger.info("QR code successfully decoded and parsed")
                return QRDetectionResult(
                    detected=True,
                    qr_data=qr_data,
                    parsed_data=parsed_data
                )
        
        # Method 2: Try OpenCV's QRCodeDetector (sometimes better with tilted/distorted codes)
        qr_detector = cv2.QRCodeDetector()
        qr_data, points, _ = qr_detector.detectAndDecode(image)
        
        if qr_data:
            logger.info("QR code detected using OpenCV QRCodeDetector")
            parsed_data = parse_qr_data(qr_data)
            
            if parsed_data:
                logger.info("QR code successfully decoded and parsed with OpenCV detector")
                return QRDetectionResult(
                    detected=True,
                    qr_data=qr_data,
                    parsed_data=parsed_data
                )
        
        # No QR code detected with any method
        return QRDetectionResult(detected=False)
        
    except Exception as e:
        logger.debug(f"Error in _try_decode_qr: {str(e)}")
        return QRDetectionResult(detected=False, error=str(e))


def detect_qr_batch(image_paths: List[str], enhance: bool = True) -> Dict[str, QRDetectionResult]:
    """
    Detect QR codes in multiple images (batch processing).
    
    Args:
        image_paths: List of image file paths
        enhance: Whether to use enhanced detection
        
    Returns:
        Dictionary mapping image paths to QRDetectionResult objects
    """
    results = {}
    
    logger.info(f"Starting batch QR detection for {len(image_paths)} images")
    
    for idx, image_path in enumerate(image_paths, 1):
        logger.info(f"Processing image {idx}/{len(image_paths)}: {image_path}")
        results[image_path] = detect_qr_in_image(image_path, enhance=enhance)
    
    # Summary
    detected_count = sum(1 for r in results.values() if r.detected)
    logger.info(f"Batch detection complete: {detected_count}/{len(image_paths)} QR codes detected")
    
    return results


def get_qr_detection_summary(result: QRDetectionResult) -> str:
    """
    Get a human-readable summary of a QR detection result.
    
    Args:
        result: QRDetectionResult object
        
    Returns:
        Formatted summary string
    """
    if not result.detected:
        return f"No QR code detected. {result.error or ''}"
    
    if result.parsed_data:
        data = result.parsed_data
        return (f"QR Code Detected - "
                f"Name: {data['first_name']} {data['last_name']}, "
                f"Email: {data['email']}, "
                f"ID: {data['registration_id']}")
    else:
        return f"QR code detected but parsing failed: {result.qr_data}"


# ============================================
# Testing and Debugging Functions
# ============================================

def test_qr_detection(image_path: str = None):
    """
    Test QR detection functionality with a sample image.
    
    Args:
        image_path: Optional path to test image. If None, prompts for path.
    """
    if not image_path:
        print("QR Code Detection Test")
        print("=" * 50)
        image_path = input("Enter path to test image: ").strip()
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return
    
    print(f"\nTesting QR detection on: {image_path}")
    print("-" * 50)
    
    result = detect_qr_in_image(image_path, enhance=True)
    
    print(f"\nDetected: {result.detected}")
    if result.detected:
        print(f"Raw QR Data: {result.qr_data}")
        if result.parsed_data:
            print(f"\nParsed Data:")
            for key, value in result.parsed_data.items():
                print(f"  {key}: {value}")
        else:
            print(f"Parsing Error: {result.error}")
    else:
        print(f"Error: {result.error}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    """Run test when module is executed directly"""
    import sys
    
    if len(sys.argv) > 1:
        test_qr_detection(sys.argv[1])
    else:
        test_qr_detection()
