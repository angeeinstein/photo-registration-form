"""
Photo Processing Pipeline
Handles sequential photo processing with QR detection and grouping
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from qr_detector import detect_qr_in_image, parse_qr_data
from models import db, PhotoBatch, Photo, Registration, ProcessingLog
try:
    from drive_uploader import DriveUploader
except Exception:
    DriveUploader = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhotoProcessor:
    """
    Core photo processing logic:
    1. Sort photos by filename (camera order)
    2. Process sequentially
    3. Detect QR codes to start new person
    4. Group following photos to current person
    5. Track progress and metrics in real-time
    """
    
    def __init__(self, batch_id: int):
        self.batch_id = batch_id
        self.batch = PhotoBatch.query.get(batch_id)
        if not self.batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        # No need for QR detector instance - using functions directly
        self.current_person = None
        self.current_person_photos = []
        self.unmatched_photos = []
        self.people_found = 0
        self.photos_processed = 0
        
        # Directories
        self.batch_dir = Path(f"uploads/batches/{batch_id}")
        self.processed_dir = Path("uploads/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    def _log_action(self, action: str, details: str = "", level: str = "info"):
        """Log processing action to database and console"""
        log_entry = ProcessingLog(
            batch_id=self.batch_id,
            action=action,
            details=details,
            timestamp=datetime.utcnow(),
            level=level
        )
        db.session.add(log_entry)
        db.session.commit()
        
        log_func = getattr(logger, level, logger.info)
        log_func(f"[Batch {self.batch_id}] {action}: {details}")
        
    def _update_batch_status(self, status: str = None, current_action: str = None, 
                            processed_photos: int = None):
        """Update batch status in database"""
        if status:
            self.batch.status = status
        if current_action:
            self.batch.current_action = current_action
        if processed_photos is not None:
            self.batch.processed_photos = processed_photos
        
        db.session.commit()
        
    def _save_current_person(self, drive_uploader=None):
        """Save current person's photos to their folder and upload to Drive"""
        if not self.current_person or not self.current_person_photos:
            return
        
        person_name = f"{self.current_person.first_name} {self.current_person.last_name}"
        
        # Create person's directory
        person_dir = self.processed_dir / str(self.current_person.id)
        person_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy photos to person's folder
        photo_paths = []
        for photo in self.current_person_photos:
            src_path = self.batch_dir / photo.filename
            dst_path = person_dir / photo.filename
            
            try:
                shutil.copy2(src_path, dst_path)
                photo.processed = True
                photo_paths.append(str(dst_path))
                db.session.commit()
                
                self._log_action(
                    "photo_copied",
                    f"Copied {photo.filename} to {person_name}'s folder"
                )
            except Exception as e:
                self._log_action(
                    "photo_copy_error",
                    f"Failed to copy {photo.filename}: {str(e)}",
                    level="error"
                )
        
        # Update registration photo count
        self.current_person.photo_count = len(self.current_person_photos)
        db.session.commit()
        
        self._log_action(
            "person_photos_saved",
            f"{person_name}: {len(self.current_person_photos)} photos saved locally"
        )
        
        # Upload to Google Drive if configured
        if drive_uploader and photo_paths:
            try:
                self._update_batch_status(
                    current_action=f"Uploading {person_name}'s photos to Google Drive..."
                )
                
                def upload_callback(action, details):
                    """Callback for Drive upload progress"""
                    self._update_batch_status(current_action=details)
                    self._log_action(f"drive_{action}", details)
                
                # Upload photos to Drive
                result = drive_uploader.upload_person_photos(
                    self.current_person.first_name,
                    self.current_person.last_name,
                    photo_paths,
                    progress_callback=upload_callback
                )
                
                if result['success']:
                    # Store Drive info in database
                    self.current_person.drive_folder_id = result['folder_id']
                    self.current_person.drive_share_link = result['share_link']
                    
                    # Mark photos as uploaded to Drive
                    for photo in self.current_person_photos:
                        photo.drive_uploaded = True
                    
                    db.session.commit()
                    
                    self._log_action(
                        "drive_upload_success",
                        f"{person_name}: Uploaded to Drive - {result['photos_uploaded']} photos, "
                        f"Share link: {result['share_link']}"
                    )
                else:
                    self._log_action(
                        "drive_upload_failed",
                        f"{person_name}: Drive upload failed - {result.get('error', 'Unknown error')}",
                        level="error"
                    )
                    
            except Exception as e:
                self._log_action(
                    "drive_upload_error",
                    f"{person_name}: Drive upload error - {str(e)}",
                    level="error"
                )
        
        self._log_action(
            "person_completed",
            f"{person_name}: Processing complete"
        )
        
    def _start_new_person(self, registration: Registration, qr_photo: Photo, drive_uploader=None):
        """Start tracking a new person. Saves previous person (uploads to Drive if available)."""
        # Save previous person first
        self._save_current_person(drive_uploader=drive_uploader)
        
        # Start new person
        self.current_person = registration
        self.current_person_photos = [qr_photo]
        self.people_found += 1
        
        # Mark QR photo
        qr_photo.is_qr_code = True
        qr_photo.registration_id = registration.id
        db.session.commit()
        
        self._log_action(
            "person_started",
            f"Started new person: {registration.first_name} {registration.last_name} (ID: {registration.id})"
        )
        
    def _assign_to_current_person(self, photo: Photo):
        """Assign photo to current person"""
        if not self.current_person:
            # No person yet, add to unmatched
            self.unmatched_photos.append(photo)
            self._log_action(
                "photo_unmatched",
                f"Photo {photo.filename} has no associated person (before first QR)",
                level="warning"
            )
            return
        
        photo.registration_id = self.current_person.id
        self.current_person_photos.append(photo)
        db.session.commit()
        
    def _match_registration(self, qr_data: Dict) -> Optional[Registration]:
        """
        Match QR data to registration in database
        Try multiple strategies for robustness
        """
        # Strategy 1: Match by qr_token (most reliable)
        if 'qr_token' in qr_data and qr_data['qr_token']:
            reg = Registration.query.filter_by(qr_token=qr_data['qr_token']).first()
            if reg:
                self._log_action("qr_matched_token", f"Matched by token: {reg.first_name} {reg.last_name}")
                return reg
        
        # Strategy 2: Match by registration_id
        if 'registration_id' in qr_data and qr_data['registration_id']:
            try:
                reg_id = int(qr_data['registration_id'])
                reg = Registration.query.get(reg_id)
                if reg:
                    self._log_action("qr_matched_id", f"Matched by ID: {reg.first_name} {reg.last_name}")
                    return reg
            except (ValueError, TypeError):
                pass
        
        # Strategy 3: Match by name + email (fallback)
        if all(k in qr_data for k in ['first_name', 'last_name', 'email']):
            reg = Registration.query.filter_by(
                first_name=qr_data['first_name'],
                last_name=qr_data['last_name'],
                email=qr_data['email']
            ).first()
            if reg:
                self._log_action("qr_matched_manual", f"Matched by name+email: {reg.first_name} {reg.last_name}")
                return reg
        
        # No match found
        self._log_action(
            "qr_no_match",
            f"Could not match QR data: {qr_data}",
            level="warning"
        )
        return None
        
    def process_batch(self) -> Dict:
        """
        Main processing function
        Returns metrics dictionary
        """
        start_time = datetime.utcnow()
        
        try:
            self._update_batch_status(
                status="processing",
                current_action="Starting batch processing...",
                processed_photos=0
            )
            self._log_action("batch_processing_started", f"Batch '{self.batch.batch_name}' processing started")
            
            # Get all photos in batch, sorted by filename
            photos = Photo.query.filter_by(batch_id=self.batch_id).order_by(Photo.filename).all()
            total_photos = len(photos)
            
            if not photos:
                raise ValueError("No photos found in batch")
            
            self._log_action("photos_sorted", f"Processing {total_photos} photos in filename order")
            
            # Initialize Drive uploader if available
            drive_uploader = None
            if DriveUploader is not None:
                try:
                    drive_uploader = DriveUploader().__enter__()
                except Exception as e:
                    # Log but continue processing locally
                    self._log_action('drive_init_failed', f'Failed to initialize Drive uploader: {str(e)}', level='warning')

            # Process each photo sequentially
            for idx, photo in enumerate(photos, 1):
                self.photos_processed = idx
                progress_pct = int((idx / total_photos) * 100)
                
                # Update status
                self._update_batch_status(
                    current_action=f"Processing {photo.filename} ({idx}/{total_photos})",
                    processed_photos=idx
                )
                
                # Get full path to photo
                photo_path = self.batch_dir / photo.filename
                
                if not photo_path.exists():
                    self._log_action(
                        "photo_missing",
                        f"Photo file not found: {photo.filename}",
                        level="error"
                    )
                    continue
                
                # Detect QR code
                self._update_batch_status(current_action=f"Detecting QR code in {photo.filename}...")
                qr_result = detect_qr_in_image(str(photo_path), enhance=True)
                
                if qr_result.detected and qr_result.parsed_data:
                    # QR code detected - start new person
                    self._update_batch_status(
                        current_action=f"QR detected in {photo.filename}, matching registration..."
                    )
                    
                    registration = self._match_registration(qr_result.parsed_data)
                    
                    if registration:
                        self._start_new_person(registration, photo, drive_uploader=drive_uploader)
                        self._update_batch_status(
                            current_action=f"Started processing photos for {registration.first_name} {registration.last_name}"
                        )
                    else:
                        # QR detected but no match
                        photo.is_qr_code = True
                        self.unmatched_photos.append(photo)
                        db.session.commit()
                        self._log_action(
                            "qr_unmatched",
                            f"QR code in {photo.filename} could not be matched to registration",
                            level="warning"
                        )
                else:
                    # No QR code - assign to current person
                    self._assign_to_current_person(photo)
                
                # Periodic log for progress
                if idx % 50 == 0:
                    self._log_action(
                        "progress_update",
                        f"Processed {idx}/{total_photos} photos ({progress_pct}%) - {self.people_found} people found"
                    )
            
            # Save last person's photos (upload to Drive if configured)
            try:
                self._save_current_person(drive_uploader=drive_uploader)
            finally:
                # Cleanup Drive uploader context
                if drive_uploader and DriveUploader is not None:
                    try:
                        DriveUploader().__exit__(None, None, None)
                    except Exception:
                        pass
            
            # Calculate final metrics
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            metrics = {
                'total_photos': total_photos,
                'photos_processed': self.photos_processed,
                'people_found': self.people_found,
                'unmatched_photos': len(self.unmatched_photos),
                'processing_time_seconds': processing_time,
                'success': True
            }
            
            # Update batch status
            self._update_batch_status(
                status="completed",
                current_action=f"Processing complete: {self.people_found} people, {len(self.unmatched_photos)} unmatched photos"
            )
            
            self._log_action(
                "batch_processing_completed",
                f"Batch processed successfully in {processing_time:.1f}s - {self.people_found} people, {len(self.unmatched_photos)} unmatched"
            )
            
            return metrics
            
        except Exception as e:
            self._update_batch_status(
                status="error",
                current_action=f"Processing failed: {str(e)}"
            )
            self._log_action(
                "batch_processing_error",
                f"Fatal error: {str(e)}",
                level="error"
            )
            
            return {
                'success': False,
                'error': str(e),
                'photos_processed': self.photos_processed,
                'people_found': self.people_found
            }
    
    def get_progress(self) -> Dict:
        """Get current processing progress"""
        return {
            'batch_id': self.batch_id,
            'status': self.batch.status,
            'current_action': self.batch.current_action,
            'photos_processed': self.batch.processed_photos,
            'total_photos': self.batch.total_photos,
            'progress_percentage': int((self.batch.processed_photos / self.batch.total_photos * 100)) if self.batch.total_photos > 0 else 0,
            'people_found': self.people_found,
            'unmatched_photos': len(self.unmatched_photos)
        }
