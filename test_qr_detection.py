#!/usr/bin/env python3
"""
Test QR Code Detection and Processing

This script tests the QR code detection functionality by:
1. Generating a test QR code
2. Detecting it in the generated image
3. Parsing and validating the data

Usage:
    python3 test_qr_detection.py
"""

import os
import sys
from datetime import datetime

def test_qr_generation():
    """Test QR code generation"""
    print("=" * 60)
    print("TEST 1: QR Code Generation")
    print("=" * 60)
    
    try:
        from qr_generator import generate_qr_data, create_qr_code, save_qr_code
        
        # Test data
        test_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'registration_id': '123',
            'qr_token': 'test-token-abc-123'
        }
        
        print(f"\nTest data:")
        for key, value in test_data.items():
            print(f"  {key}: {value}")
        
        # Generate QR data string
        qr_string = generate_qr_data(
            test_data['first_name'],
            test_data['last_name'],
            test_data['email'],
            test_data['registration_id'],
            test_data['qr_token']
        )
        print(f"\nGenerated QR string: {qr_string}")
        
        # Create QR code image
        qr_image = create_qr_code(qr_string)
        print(f"✓ QR code image created (size: {qr_image.size})")
        
        # Save to file
        test_file = 'test_qr_code.png'
        save_qr_code(qr_image, test_file)
        print(f"✓ QR code saved to: {test_file}")
        
        return test_file, qr_string, test_data
        
    except ImportError as e:
        print(f"✗ FAILED: Missing module - {e}")
        print("  Make sure qr_generator.py exists and dependencies are installed")
        return None, None, None
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return None, None, None


def test_qr_detection(test_file):
    """Test QR code detection"""
    print("\n" + "=" * 60)
    print("TEST 2: QR Code Detection")
    print("=" * 60)
    
    try:
        from qr_detector import detect_qr_in_image, get_qr_detection_summary
        
        if not test_file or not os.path.exists(test_file):
            print(f"✗ FAILED: Test file not found: {test_file}")
            return None
        
        print(f"\nDetecting QR code in: {test_file}")
        
        # Detect QR code
        result = detect_qr_in_image(test_file, enhance=True)
        
        if result.detected:
            print(f"✓ QR code detected!")
            print(f"\nRaw QR data: {result.qr_data}")
            
            if result.parsed_data:
                print(f"\n✓ Data parsed successfully:")
                for key, value in result.parsed_data.items():
                    print(f"  {key}: {value}")
                return result.parsed_data
            else:
                print(f"✗ Failed to parse QR data: {result.error}")
                return None
        else:
            print(f"✗ QR code not detected: {result.error}")
            return None
            
    except ImportError as e:
        print(f"✗ FAILED: Missing module - {e}")
        print("  Make sure qr_detector.py exists and dependencies are installed")
        print("  Required: opencv-python, pyzbar")
        return None
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_data_validation(original_data, detected_data):
    """Test that detected data matches original"""
    print("\n" + "=" * 60)
    print("TEST 3: Data Validation")
    print("=" * 60)
    
    if not original_data or not detected_data:
        print("✗ FAILED: Missing data for comparison")
        return False
    
    print("\nComparing original vs detected data:")
    all_match = True
    
    for key in original_data.keys():
        original = str(original_data[key])
        detected = str(detected_data.get(key, ''))
        
        # Normalize for comparison (case-insensitive for email)
        if key == 'email':
            original = original.lower()
            detected = detected.lower()
        
        match = original == detected
        status = "✓" if match else "✗"
        print(f"  {status} {key}: '{original}' == '{detected}' : {match}")
        
        if not match:
            all_match = False
    
    if all_match:
        print("\n✓ All data matches!")
        return True
    else:
        print("\n✗ Some data doesn't match!")
        return False


def cleanup_test_files():
    """Remove test files"""
    test_file = 'test_qr_code.png'
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\nCleaned up test file: {test_file}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("QR CODE DETECTION TEST SUITE")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Generate QR code
    test_file, qr_string, original_data = test_qr_generation()
    
    if not test_file:
        print("\n" + "=" * 60)
        print("OVERALL RESULT: FAILED (Generation)")
        print("=" * 60)
        return 1
    
    # Test 2: Detect QR code
    detected_data = test_qr_detection(test_file)
    
    if not detected_data:
        cleanup_test_files()
        print("\n" + "=" * 60)
        print("OVERALL RESULT: FAILED (Detection)")
        print("=" * 60)
        return 1
    
    # Test 3: Validate data
    validation_passed = test_data_validation(original_data, detected_data)
    
    # Cleanup
    cleanup_test_files()
    
    # Final result
    print("\n" + "=" * 60)
    if validation_passed:
        print("OVERALL RESULT: ✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nQR code generation and detection are working correctly!")
        return 0
    else:
        print("OVERALL RESULT: ✗ TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
