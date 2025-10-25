"""
Photo Processing Pipeline
Handles sequential photo processing with QR detection and grouping
"""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from PIL import Image

from qr_detector import detect_qr_in_image, parse_qr_data
# Import models and helpers from app.py where they are defined
from app import db, PhotoBatch, Photo, Registration, ProcessingLog, db_commit_with_retry
try:
    from drive_uploader import DriveUploader
except Exception:
    DriveUploader = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_thumbnail(image_path: Path, thumbnail_path: Path, max_width: int = 400) -> bool:
    """
    Create a thumbnail from an image, maintaining aspect ratio.
    
    Args:
        image_path: Path to original image
        thumbnail_path: Path where thumbnail will be saved
        max_width: Maximum width of thumbnail (height scaled proportionally)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure thumbnail directory exists
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open image
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if needed (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Calculate new dimensions maintaining aspect ratio
            width, height = img.size
            if width > max_width:
                new_width = max_width
                new_height = int(height * (max_width / width))
            else:
                new_width, new_height = width, height
            
            # Resize using high-quality LANCZOS resampling
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save thumbnail with optimization
            img_resized.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
        logger.debug(f"Created thumbnail: {thumbnail_path.name} ({new_width}x{new_height})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {image_path.name}: {str(e)}")
        return False


def db_commit_with_retry(max_attempts=5, delay=0.5):
    """
    Commit database changes with retry logic for locked database.
    Uses exponential backoff to handle concurrent access.
    """
    from sqlalchemy.exc import OperationalError
    
    for attempt in range(max_attempts):
        try:
            db.session.commit()
            return True
        except OperationalError as e:
            if 'database is locked' in str(e) and attempt < max_attempts - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Database locked, retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_attempts})")
                time.sleep(wait_time)
                db.session.rollback()  # Rollback failed transaction
            else:
                logger.error(f"Database commit failed after {max_attempts} attempts: {e}")
                db.session.rollback()
                raise
    return False


class PhotoProcessor:
    """
    Core photo processing logic:
    PHASE 1: Scan QR codes, create thumbnails, update database only
    PHASE 2: Create folders and copy files based on database, then upload to Drive
    """
    
    def __init__(self, batch_id: int):
        self.batch_id = batch_id
        self.batch = PhotoBatch.query.get(batch_id)
        if not self.batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        self.current_registration_id = None  # Track current person for grouping
        self.people_found = 0
        self.photos_processed = 0
        
        # Directories
        self.batch_dir = Path(f"uploads/batches/{batch_id}")
        self.thumbnails_dir = self.batch_dir / "thumbnails"
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
    def _log_action(self, action: str, details: str = "", level: str = "info"):
        """Log processing action to database and console"""
        log_entry = ProcessingLog(
            batch_id=self.batch_id,
            action=action,
            message=details,  # Field is 'message' not 'details'
            timestamp=datetime.utcnow(),
            level=level
        )
        db.session.add(log_entry)
        db_commit_with_retry()
        
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
        
        db_commit_with_retry()
        
    def _assign_to_current_person(self, photo: Photo):
        """Assign photo to current person (database only, no file operations)"""
        if not self.current_registration_id:
            # No person yet - photo is before first QR code
            # Leave registration_id as NULL
            self._log_action(
                "photo_unmatched",
                f"Photo {photo.filename} before first QR code",
                level="info"
            )
            return
        
        # Assign to current person in database only
        photo.registration_id = self.current_registration_id
        db_commit_with_retry()
        
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
        Main processing function - TWO PHASES:
        1. Process all photos locally (detect QR, sort into person folders)
        2. Upload all person folders to Drive and create share links
        
        Returns metrics dictionary
        """
        start_time = datetime.utcnow()
        
        try:
            self.batch.processing_started_at = start_time
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
            
            # ==============================================
            # PHASE 1: LOCAL PROCESSING ONLY (NO UPLOADS)
            # ==============================================
            self._log_action("phase1_started", "Phase 1: Processing photos locally (detecting QR, sorting into folders)")
            
            # Process each photo sequentially
            for idx, photo in enumerate(photos, 1):
                self.photos_processed = idx
                progress_pct = int((idx / total_photos) * 100)
                
                # Update status
                self._update_batch_status(
                    current_action=f"Phase 1: Processing {photo.filename} ({idx}/{total_photos})",
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
                
                # Create thumbnail for review page (do this early so it's available even if QR fails)
                thumbnail_path = self.thumbnails_dir / photo.filename
                if not thumbnail_path.exists():
                    create_thumbnail(photo_path, thumbnail_path, max_width=400)
                
                # Detect QR code
                # OPTIMIZATION: Always use fast mode (enhance=False)
                # 
                # Logic: Most photos DON'T have QR codes, so enhancement just slows them down
                # - Photos WITH QR codes: Detected on first attempt anyway (fast)
                # - Photos WITHOUT QR codes: No need to enhance (fast)
                # 
                # Edge case: Blurry/poorly lit QR codes might be missed
                # - Solution: These show up as "unmatched" photos for manual review
                # - Trade-off: 99% faster processing vs rare missed QR that needs manual fix
                
                self._update_batch_status(current_action=f"Scanning {photo.filename}...")
                
                qr_result = detect_qr_in_image(str(photo_path), enhance=False)
                
                # Only log if QR detected (reduces log spam)
                if qr_result.detected:
                    self._log_action(
                        "qr_detected",
                        f"QR code found in {photo.filename} ({idx}/{total_photos})"
                    )
                
                if qr_result.detected and qr_result.parsed_data:
                    # QR code detected - match to registration
                    self._update_batch_status(
                        current_action=f"QR detected in {photo.filename}, matching registration..."
                    )
                    
                    registration = self._match_registration(qr_result.parsed_data)
                    
                    if registration:
                        # Update current person for grouping
                        self.current_registration_id = registration.id
                        self.people_found += 1
                        
                        # Mark this photo as QR code in database
                        photo.is_qr_code = True
                        photo.qr_data = qr_result.qr_data  # Use qr_data, not raw_data
                        photo.registration_id = registration.id
                        db_commit_with_retry()
                        
                        self._log_action(
                            "person_started",
                            f"Started new person: {registration.first_name} {registration.last_name} (ID: {registration.id})"
                        )
                        self._update_batch_status(
                            current_action=f"Found QR for {registration.first_name} {registration.last_name}"
                        )
                    else:
                        # QR detected but no match
                        photo.is_qr_code = True
                        db_commit_with_retry()
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
            
            # Loop completed - log this clearly
            self._log_action(
                "phase1_loop_completed",
                f"All {total_photos} photos processed in Phase 1 loop"
            )
            
            # Count unmatched photos (no registration_id)
            unmatched_count = Photo.query.filter_by(
                batch_id=self.batch_id,
                registration_id=None
            ).count()
            
            self._log_action(
                "phase1_completed",
                f"Phase 1 complete: {self.people_found} people found, {unmatched_count} unmatched photos (database updated, no files copied yet)"
            )
            
            # Update batch to awaiting_review status - STOP HERE FOR MANUAL REVIEW
            self.batch.status = 'awaiting_review'
            self.batch.current_action = f'Phase 1 complete: {self.people_found} people found - Ready for manual review'
            self.batch.people_found = self.people_found
            self.batch.unmatched_photos = unmatched_count
            db_commit_with_retry()
            
            self._log_action(
                "awaiting_manual_review",
                f"Batch ready for manual review: {self.people_found} people, {unmatched_count} unmatched photos"
            )
            
            # Return Phase 1 metrics
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            metrics = {
                'phase': 1,
                'status': 'awaiting_review',
                'total_photos': total_photos,
                'people_found': self.people_found,
                'unmatched_photos': unmatched_count,
                'processing_time_seconds': processing_time
            }
            
            return metrics
            
        except Exception as e:
            self.batch.error_message = str(e)
            self._update_batch_status(
                status="error",
                current_action=f"Phase 1 failed: {str(e)}"
            )
            self._log_action(
                "phase1_error",
                f"Fatal error in Phase 1: {str(e)}",
                level="error"
            )
            
            return {
                'success': False,
                'error': str(e),
                'phase': 1
            }
    
    def process_phase2_drive_upload(self) -> Dict:
        """
        Phase 2: Create folders, copy files, and upload to Drive (called after manual review approval)
        """
        start_time = datetime.utcnow()
        
        try:
            self._log_action("phase2_starting", "Starting Phase 2: Creating folders and uploading to Drive")
            
            # Update status
            self.batch.status = 'processing'
            self.batch.current_action = 'Phase 2: Creating person folders...'
            db_commit_with_retry()
            
            # ==============================================
            # STEP 1: CREATE FOLDERS AND COPY FILES FROM BATCH FOLDER
            # ==============================================
            
            # Get all registrations that have photos assigned in database
            registrations_with_photos = db.session.query(Registration).join(Photo).filter(
                Photo.batch_id == self.batch_id,
                Photo.registration_id.isnot(None)
            ).distinct().all()
            
            self._log_action(
                "phase2_creating_folders",
                f"Creating folders for {len(registrations_with_photos)} people"
            )
            
            # Create processed directory
            processed_dir = Path("uploads/processed")
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy files for each person based on database assignments
            for idx, registration in enumerate(registrations_with_photos, 1):
                person_name = f"{registration.first_name} {registration.last_name}"
                
                self._update_batch_status(
                    current_action=f"Phase 2: Copying photos for {person_name} ({idx}/{len(registrations_with_photos)})..."
                )
                
                # Create person's folder
                person_dir = processed_dir / str(registration.id)
                person_dir.mkdir(parents=True, exist_ok=True)
                
                # Get all photos assigned to this person from database
                person_photos = Photo.query.filter_by(
                    batch_id=self.batch_id,
                    registration_id=registration.id
                ).all()
                
                # Copy photos from batch folder to person folder
                copied_count = 0
                for photo in person_photos:
                    src_path = self.batch_dir / photo.filename
                    dst_path = person_dir / photo.filename
                    
                    if src_path.exists() and not dst_path.exists():
                        try:
                            shutil.copy2(str(src_path), str(dst_path))
                            photo.processed = True
                            copied_count += 1
                        except Exception as e:
                            self._log_action(
                                "file_copy_error",
                                f"Failed to copy {photo.filename} for {person_name}: {str(e)}",
                                level="error"
                            )
                
                # Update registration photo count
                registration.photo_count = len(person_photos)
                db_commit_with_retry()
                
                self._log_action(
                    "person_folder_created",
                    f"{person_name}: Created folder with {copied_count} photos"
                )
            
            # ==============================================
            # STEP 2: UPLOAD TO DRIVE
            # ==============================================
            self._update_batch_status(
                current_action='Phase 2: Uploading to Google Drive...'
            )
            
            drive_upload_success = False
            drive_results = []
            
            if registrations_with_photos and DriveUploader is not None:
                try:
                    self._log_action("phase2_drive_upload_started", f"Uploading {len(registrations_with_photos)} person folders to Google Drive")
                    
                    # Use batch name as event folder name for organization
                    # Sanitize batch name for Drive folder
                    event_folder_name = self.batch.batch_name.replace('/', '-').replace('\\', '-')
                    
                    # Initialize Drive uploader once for all uploads
                    with DriveUploader() as drive_uploader:
                        for idx, registration in enumerate(registrations_with_photos, 1):
                            person_name = f"{registration.first_name} {registration.last_name}"
                            
                            self._update_batch_status(
                                current_action=f"Phase 2: Uploading {person_name}'s photos to Drive ({idx}/{len(registrations_with_photos)})..."
                            )
                            
                            # Get photo file paths from person's folder
                            person_dir = processed_dir / str(registration.id)
                            photo_paths = []
                            for photo_file in person_dir.glob('*'):
                                if photo_file.is_file():
                                    photo_paths.append(str(photo_file))
                            
                            if not photo_paths:
                                self._log_action(
                                    "drive_no_photos",
                                    f"{person_name}: No photo files found to upload",
                                    level="warning"
                                )
                                continue
                            
                            # Upload to Drive with progress callback
                            def upload_callback(action, details):
                                """Callback for Drive upload progress"""
                                self._update_batch_status(current_action=f"Phase 2: {details}")
                                self._log_action(f"drive_{action}", details)
                            
                            try:
                                result = drive_uploader.upload_person_photos(
                                    registration.first_name,
                                    registration.last_name,
                                    photo_paths,
                                    progress_callback=upload_callback,
                                    event_folder_name=event_folder_name
                                )
                                
                                if result['success']:
                                    # Store Drive info in database
                                    registration.drive_folder_id = result['folder_id']
                                    registration.drive_share_link = result['share_link']
                                    
                                    # Mark photos as uploaded to Drive
                                    for photo in person_photos:
                                        photo.uploaded_to_drive = True
                                    
                                    db_commit_with_retry()
                                    drive_results.append({'person': person_name, 'success': True, 'link': result['share_link']})
                                    
                                    self._log_action(
                                        "drive_upload_success",
                                        f"{person_name}: ✓ Uploaded {result['photos_uploaded']} photos, Share link: {result['share_link']}"
                                    )
                                else:
                                    drive_results.append({'person': person_name, 'success': False, 'error': result.get('error')})
                                    self._log_action(
                                        "drive_upload_failed",
                                        f"{person_name}: ✗ Upload failed - {result.get('error', 'Unknown error')}",
                                        level="error"
                                    )
                            
                            except Exception as e:
                                drive_results.append({'person': person_name, 'success': False, 'error': str(e)})
                                self._log_action(
                                    "drive_upload_error",
                                    f"{person_name}: ✗ Upload error - {str(e)}",
                                    level="error"
                                )
                    
                    drive_upload_success = all(r['success'] for r in drive_results)
                    successful_uploads = sum(1 for r in drive_results if r['success'])
                    
                    self._log_action(
                        "phase2_completed",
                        f"Phase 2 complete: {successful_uploads}/{len(drive_results)} person folders uploaded successfully"
                    )
                
                except Exception as e:
                    self._log_action(
                        "phase2_error",
                        f"Phase 2 failed to initialize Drive: {str(e)}",
                        level="error"
                    )
            else:
                self._log_action(
                    "phase2_skipped",
                    "Phase 2 skipped: No Drive configuration or no photos to upload",
                    level="info"
                )
            
            # Calculate final metrics
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Update batch status and metrics
            self.batch.people_found = self.people_found
            self.batch.unmatched_photos = len(self.unmatched_photos)
            self.batch.processing_completed_at = end_time
            self._update_batch_status(
                status="completed",
                current_action=f"Complete: {self.people_found} people, {len(self.unmatched_photos)} unmatched, {sum(1 for r in drive_results if r['success'])}/{len(drive_results)} uploaded to Drive"
            )
            
            self._log_action(
                "batch_processing_completed",
                f"✓ Batch completed in {processing_time:.1f}s - {self.people_found} people, {sum(1 for r in drive_results if r['success'])} uploaded to Drive"
            )
            
            metrics = {
                'phase': 2,
                'status': 'completed',
                'drive_uploads': len(drive_results),
                'drive_uploads_successful': sum(1 for r in drive_results if r['success']),
                'processing_time_seconds': processing_time,
                'success': True
            }
            
            return metrics
            
        except Exception as e:
            self.batch.error_message = str(e)
            self._update_batch_status(
                status="error",
                current_action=f"Phase 2 failed: {str(e)}"
            )
            self._log_action(
                "phase2_error",
                f"Fatal error in Phase 2: {str(e)}",
                level="error"
            )
            
            return {
                'success': False,
                'error': str(e),
                'phase': 2
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
