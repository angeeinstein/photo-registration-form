# Photo Workflow Implementation Plan

## 📋 Overview

This document outlines the complete implementation plan for the automated photo processing workflow, from registration QR codes to Google Drive delivery.

## 🎯 Workflow Summary

1. **Registration** → User registers → Confirmation email includes QR code
2. **Event** → Customer holds smartphone (showing QR code) in first photo → Following photos (~20 max) are of that person
3. **Post-Event** → Photos are edited → Admin uploads all edited JPEGs to Flask server
4. **Processing** → Server detects QR codes → Groups photos by person (can complete overnight)
5. **Upload** → One Drive folder per event → Subfolders per person → Individual shareable links
6. **Delivery** → Email sent with personalized Google Drive link to person's folder

## 📊 Scale Expectations

- **Max Participants:** ~100 persons per event
- **Photos per Person:** ~20 photos maximum
- **Total Photos:** ~2,000 photos per event
- **Processing Time:** Next day is acceptable (overnight processing)
- **Photo Format:** Edited JPEGs ready for delivery

## 🏗️ Architecture Design

### Database Schema Changes

```python
# Updated Registration Model
class Registration(db.Model):
    # Existing fields...
    qr_token = db.Column(db.String(64), unique=True, nullable=True)
    photos_uploaded = db.Column(db.Boolean, default=False)
    photos_processed = db.Column(db.Boolean, default=False)
    photo_count = db.Column(db.Integer, default=0)
    drive_folder_id = db.Column(db.String(200), nullable=True)
    drive_link = db.Column(db.String(500), nullable=True)

# New PhotoBatch Model
class PhotoBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_name = db.Column(db.String(200), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    total_photos = db.Column(db.Integer, default=0)
    processed_photos = db.Column(db.Integer, default=0)
    uploaded_photos = db.Column(db.Integer, default=0)  # Track upload progress
    status = db.Column(db.String(50), default='uploading')  # uploading, uploaded, processing, completed, failed
    current_action = db.Column(db.String(500), nullable=True)  # Real-time status message
    current_file = db.Column(db.String(500), nullable=True)  # Currently processing file
    error_message = db.Column(db.Text, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

# New ProcessingLog Model (for detailed history)
class ProcessingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('photo_batch.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(100), nullable=False)  # qr_detected, photos_assigned, upload_started, etc.
    message = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), default='info')  # info, warning, error
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id'), nullable=True)

# New Photo Model
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('photo_batch.id'), nullable=False)
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id'), nullable=True)
    filename = db.Column(db.String(500), nullable=False)
    original_path = db.Column(db.String(500), nullable=False)
    is_qr_code = db.Column(db.Boolean, default=False)
    processed = db.Column(db.Boolean, default=False)
    uploaded_to_drive = db.Column(db.Boolean, default=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
```

### Directory Structure

```
photo-registration-form/
├── uploads/                    # Temporary photo storage
│   ├── batches/               # Uploaded batches
│   │   └── batch_123/         # Individual batch folder
│   │       ├── IMG_001.jpg
│   │       └── IMG_002.jpg
│   └── processed/             # Sorted by person
│       └── registration_456/  # Per-person folders
│           ├── photo1.jpg
│           └── photo2.jpg
├── qr_codes/                  # Generated QR code images (temp)
│   └── reg_123_token.png
├── photo_processor.py         # Main processing script
├── qr_generator.py           # QR code generation
├── qr_detector.py            # QR code detection
├── drive_uploader.py         # Google Drive integration
└── photo_worker.py           # Background processing worker
```

## 📦 Required Dependencies

Add to `requirements.txt`:
```
qrcode==7.4.2
Pillow==10.1.0
opencv-python==4.8.1.78
pyzbar==0.1.9
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
celery==5.3.4  # Optional: for background processing
redis==5.0.1   # Optional: for Celery broker
```

## 🔧 Implementation Phases

### Phase 1: QR Code System (Priority: High)

**Tasks:**
1. Add `qr_token` field to Registration model
2. Generate unique token on registration (UUID)
3. Create QR code generator using `qrcode` library
4. Embed QR code in confirmation email (inline image or attachment)
5. QR format: `{registration_id}:{qr_token}` for easy parsing
6. High error correction level (customers will hold phone at distance)

**Files to Create/Modify:**
- `qr_generator.py` - QR code generation logic
- `app.py` - Add qr_token generation to registration route
- `send_email.py` - Add QR code to confirmation email
- `templates/email_templates/confirmation_email.html` - Include QR code with instructions

### Phase 2: Photo Upload Interface with Metrics (Priority: High)

**Tasks:**
1. Create admin photo upload page
2. Multi-file upload with drag & drop (support ~2000 files)
3. Show upload progress:
   - File counter: "Uploading 847/2,147"
   - Current filename: "Uploading IMG_0847.jpg"
   - Total size: "Uploaded 1.2 GB / 3.8 GB"
   - Progress bar
4. Create PhotoBatch on upload start
5. Store files temporarily in `uploads/batches/{batch_id}/`
6. Validate file types (JPEG/JPG only, max 10MB per file)
7. Add batch naming (e.g., "Event_2025-10-22")
8. **After upload complete:**
   - Display metrics summary:
     - ✅ **Upload Complete**
     - **Total Photos:** 2,147 files
     - **Total Size:** 3.8 GB
     - **Status:** Ready to process
   - Show **[Process]** button to start processing

**Files to Create/Modify:**
- `templates/admin_photo_upload.html` - Upload interface with metrics
- `static/css/photo_upload.css` - Upload styling
- `static/js/photo_upload.js` - Upload handling with real-time metrics
- `app.py` - Add upload routes + metrics endpoint
- Create `uploads/batches/` directory structure

### Phase 3: QR Detection (Priority: High)

**Tasks:**
1. Install OpenCV and pyzbar
2. Create QR code detection function
3. Read QR data from images
4. Match QR tokens to registrations
5. Handle detection errors
6. Mark photos as QR or regular photo

**Files to Create:**
- `qr_detector.py` - QR detection logic
- `photo_processor.py` - Main processing orchestrator

### Phase 4: Photo Processing Pipeline with Real-Time Metrics (Priority: High)

**Trigger:** Admin clicks **[Process]** button after upload complete

**Tasks:**
1. **FIRST:** Sort photos by filename (IMG_0001, IMG_0002, etc.) - ignore upload time
2. Process sorted batch sequentially, photo by photo
3. **Real-time metrics display:**
   - Photos processed: 847 / 2,147 (39%)
   - Progress bar
   - Current action: "Detecting QR code for Jane Smith..."
   - People found: 42
   - Unmatched photos: 3
   - Estimated time remaining: 8 minutes
4. **QR Detection Logic:**
   - When QR code detected → This is Person #1's first photo
   - Following photos (no QR) → Belong to Person #1
   - When next QR code detected → This is Person #2's first photo (Person #1 complete)
   - Following photos (no QR) → Belong to Person #2
   - Continue until all photos processed
5. **For each person found:**
   - Group photos into set
   - Copy to `uploads/processed/{registration_id}/`
   - **Immediately upload to Google Drive** (create folder + upload photos)
   - Generate shareable link
   - Store drive_link in database
   - Update metrics
6. Update Photo records in database
7. Handle edge cases (back-to-back QRs, photos before first QR)
8. Set batch status to 'completed'

**Processing Flow:**
```
[Photos sorted by filename first]
Photo 001 [QR: John|Doe|...] → Start Person #1 (John Doe)
Photo 002 [No QR]            → Assign to John Doe
Photo 003 [No QR]            → Assign to John Doe
...
Photo 018 [No QR]            → Assign to John Doe (last photo)
                            → Upload John's 18 photos to Drive
                            → Generate share link
Photo 019 [QR: Jane|Smith...] → Start Person #2 (Jane Smith)
Photo 020 [No QR]            → Assign to Jane Smith
...
```

**Files to Create/Modify:**
- `photo_processor.py` - Main processing logic with real-time status updates
- `drive_uploader.py` - Called inline during processing
- `app.py` - Add process route + status endpoint for real-time updates

### Phase 5: Google Drive Integration (Inline with Processing) (Priority: High)

**Integration Point:** Called during Phase 4 processing, after each person's photos are grouped

**Tasks:**
1. Set up Google Cloud project
2. Enable Drive API
3. Create service account credentials (recommended for server)
4. Implement Drive upload function (called per person)
5. Create folder structure: `Event_YYYYMMDD/{FirstName_LastName}/`
6. Upload all photos for person to their folder
7. Generate shareable link **per person folder** (not main folder)
8. Permission: "Anyone with link can view"
9. Store folder_id, share_link, and photo_count in database (Registration table)
10. Real-time status: "Uploading to Drive: John Doe (photo 5/18)..."

**Files to Create:**
- `drive_uploader.py` - Drive API integration
- `google_credentials.json` - Service account credentials (gitignored)
- Admin settings for Drive parent folder ID, event name/date
- Function to create event folder and person subfolders

### Phase 6: Photo Management Dashboard & Manual Email Sending (Priority: High)

**Purpose:** Review all processed results, verify Drive links, then send emails manually

**Dashboard Features:**

1. **Batch Summary:**
   - Batch name, processing date, status
   - Total people: 87
   - Total photos: 2,147
   - Unmatched photos: 3
   - Processing time: 18 minutes

2. **People Table:**
   ```
   Name         | Email              | Photos | Google Drive Link           | Status      | Actions
   John Doe     | john@email.com     | 18     | [View in Drive] (clickable) | Not sent    | [Send Email]
   Jane Smith   | jane@email.com     | 22     | [View in Drive] (clickable) | Not sent    | [Send Email]
   Bob Johnson  | bob@email.com      | 15     | [View in Drive] (clickable) | Sent ✓      | [Resend]
   ...
   ```

3. **Admin Actions:**
   - **[Send All]** button at top - sends to all unsent people
   - Individual **[Send Email]** buttons per person
   - **Clickable Drive links** - verify folders in Google Drive before sending
   - View unmatched photos section
   - Manual reassignment interface

4. **Email Tracking:**
   - Track email_sent status per person
   - Show sent timestamp
   - Prevent duplicate sends
   - Show real-time progress when bulk sending

**Tasks:**
1. Create photo management dashboard with table view
2. Display all processed people with Drive links
3. Make Drive links clickable (open in new tab)
4. Show email sent status per person
5. Implement [Send All] bulk email function
6. Implement individual [Send Email] buttons
7. Add confirmation dialog for bulk send
8. Update email_sent status in database
9. Show unmatched photos with manual assignment
10. Add photo preview modal
11. Manual photo reassignment (if QR detection failed)

**Files to Create:**
- `templates/admin_photo_dashboard.html` - Main dashboard with table
- `templates/admin_photo_preview.html` - Photo preview modal
- `static/css/admin_photos.css` - Dashboard styling
- `static/js/photo_dashboard.js` - Email sending logic
- `app.py` - Add dashboard routes + send email endpoints

### Phase 7: Photos Email Template for Drive Links (Priority: High)

**Triggered by:** Admin clicking [Send Email] or [Send All] in dashboard

**Email Content:**
```
Subject: 📸 Your Photos Are Ready!

Hi [First Name],

Great news! Your photos from [Event Name] are ready.

📁 Your Photos (18 photos)
[Click here to view and download your photos]
↳ Google Drive folder link

💾 How to Download:
1. Click the link above
2. Click "Download all" or select individual photos
3. Save to your device

Your photos will be available for [X] days.

Thank you for attending [Event Name]!

Best regards,
[Your Team]
```

**Tasks:**
1. Design photo delivery email template
2. Include personalized Google Drive link from database
3. Show photo count from database
4. Add download instructions
5. Personalize with recipient first name and event name
6. Add expiry notice (configurable retention period)
7. Make email visually appealing
8. Test with real Drive links before bulk send
9. Handle email sending errors gracefully

**Files to Create/Modify:**
- `templates/email_templates/photos_email.html` - Photo delivery email (already exists, modify)
- `send_email.py` - Add send_photos_email function
- `app.py` - Add email sending routes (single + bulk)

### Phase 8: Background Processing (Priority: Low)

**Tasks:**
1. Set up Celery for background tasks
2. Create worker for photo processing
3. Show progress in admin interface
4. Handle long-running operations
5. Retry logic for failures

**Files to Create:**
- `photo_worker.py` - Celery worker
- `celery_config.py` - Celery configuration

### Phase 9: Cleanup & Optimization (Priority: Low)

**Tasks:**
1. Auto-delete temp files after processing
2. Configurable retention period
3. Optimize image processing performance
4. Add compression options
5. Batch processing improvements

**Files to Create:**
- `cleanup_scheduler.py` - Cleanup tasks

### Phase 10: Testing & Documentation (Priority: Medium)

**Tasks:**
1. Unit tests for QR generation/detection
2. Integration tests for full workflow
3. Test with sample photo sets
4. Document admin workflow
5. User-facing QR code guide
6. Google Drive setup guide

## 🔐 Security Considerations

1. **File Upload Security:**
   - Validate file types (JPEG/JPG only)
   - Check file size limits
   - Scan for malicious content
   - Rate limit uploads

2. **Google Drive:**
   - Secure credential storage
   - Use service account (not user OAuth)
   - Set appropriate permissions on links
   - Consider time-limited access

3. **QR Code Security:**
   - Use cryptographically secure tokens
   - Prevent QR token guessing
   - Validate QR data before processing

4. **Privacy:**
   - Delete temp files after processing
   - Don't store face recognition data
   - GDPR compliance (data retention)

## 📊 Admin Workflow

1. **Before Event:**
   - Users register and receive confirmation email with embedded QR code
   - Users save email or take screenshot of QR code

2. **During Event:**
   - Customer opens email on smartphone showing QR code
   - **Photo 1:** Customer holds phone with QR code visible in frame
   - **Photos 2-20:** Regular photos of that customer (no QR needed)
   - **Next customer:** Shows their QR code for their first photo
   - Repeat for each person

3. **After Event:**
   - Edit all raw photos (color correction, cropping, etc.)
   - **CRITICAL:** Ensure filenames are sequential (IMG_0001.jpg, IMG_0002.jpg, etc.)
   - Upload all edited JPEGs to admin dashboard
   - **Can upload all ~2000 photos at once** - system will sort by filename
   - Upload time is ignored - only filename order matters

4. **Upload Complete - Metrics Displayed:**
   - **Total Photos Uploaded:** 2,147 files
   - **Total Size:** 3.8 GB
   - **Status:** Ready to process
   - **[Process] Button** - Click to start processing

5. **Processing (Manual Trigger):**
   - Admin clicks **[Process]** button
   - System sorts photos by filename (IMG_0001, IMG_0002, etc.)
   - Real-time metrics during processing:
     - Photos processed: 847 / 2,147
     - Current action: "Processing QR code for Jane Smith..."
     - People found: 42
     - Unmatched photos: 3
   - Scans in filename order, groups by QR detection
   - Uploads each person's folder to Google Drive
   - Generates shareable link per person

6. **Processing Complete - Dashboard Review:**
   - View all processed people in dashboard table:
     - Name | Email | Photo Count | Google Drive Link | [Send Email] button
   - Click Drive links to manually verify folders in Google Drive
   - Check photo counts match expectations
   - Review unmatched photos (if any)
   - Manually reassign photos if needed

7. **Send Emails (Manual Trigger):**
   - After verifying everything in Drive
   - Click **[Send All]** button to send all emails at once
   - OR click individual **[Send Email]** buttons for specific people
   - Each email contains their personal Google Drive link
   - Dashboard updates: "Email sent ✓" status per person

6. **Manual Intervention (if needed):**
   - View photos that couldn't be assigned (before first QR code)
   - Read QR code content (name/email) from processing log
   - Manually link photos to correct registrations
   - Resend failed emails

## 🎨 User Experience Flow

### Confirmation Email
```
From: Photo Registration
To: customer@email.com
Subject: ✅ Registration Confirmed - Your QR Code

Hi [First Name],

Thank you for registering! We've received your information.

🎯 IMPORTANT: Your Personal QR Code
┌─────────────┐
│  [QR CODE]  │
│   EMBEDDED  │
│   IN EMAIL  │
└─────────────┘

📸 At the photo booth:
1. Open this email on your smartphone
2. Hold your phone with the QR code visible
3. Take your first photo with the QR code in view
4. Continue with regular photos

You'll receive your edited photos via email within 24-48 hours.

Questions? Reply to this email.
```

### Admin Photo Processing Page
```
┌─────────────────────────────────────┐
│  📸 Photo Processing                │
│                                     │
│  Upload New Batch                   │
│  ┌─────────────────────────────┐   │
│  │ Drag photos here or click   │   │
│  │ to browse                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  Recent Batches:                    │
│  ┌─────────────────────────────┐   │
│  │ Batch #123 - Oct 21         │   │
│  │ Status: Processing (45/100) │   │
│  │ [View Details] [Cancel]     │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Batch #122 - Oct 20         │   │
│  │ Status: ✅ Completed (89/89) │   │
│  │ [View Photos] [Resend All]  │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## 🚀 Deployment Considerations

1. **Storage:**
   - ~2,000 photos × 5MB avg = ~10GB per event
   - Ensure 20-30GB free space for temp storage
   - Auto-cleanup after 7 days (configurable)

2. **Performance:**
   - Processing can run overnight (not time-critical)
   - Sequential processing is fine for 2,000 photos
   - Estimated time: 1-2 hours for full batch
   - No need for complex background workers initially

3. **Google Drive:**
   - Service account for automated uploads
   - Create main event folder manually or via API
   - Organize as: `Event_Name/FirstName_LastName/`
   - Share links to individual person folders only

4. **Monitoring:**
   - Log all processing steps
   - Email admin on completion or errors
   - Track success rate (photos matched vs unmatched)

## 📝 Future Enhancements (Not Implementing Now)

### Phase 11: Face Recognition Validation (Future)

**Purpose:** Verify that all photos in a person's folder actually belong to the same person.

**Approach:**
1. **Library:** Use `face_recognition` or `DeepFace` (runs locally, no cloud)
2. **Process Flow:**
   - After QR-based grouping complete
   - For each person's photo set:
     - Detect faces in all photos
     - Compare face embeddings
     - Flag if different person detected
   - Admin reviews flagged sets
   - Manually reassign mismatched photos

3. **No Data Storage:**
   - Face embeddings computed in RAM only
   - Nothing saved to disk or database
   - Temporary processing only
   - All face data deleted after validation

4. **Integration Point:**
   - Add validation step after photo grouping
   - Before Drive upload
   - Optional toggle in admin settings

**Example Workflow:**
```
Person #5: Jane Smith (15 photos assigned)
  → Detecting faces...
  → Photo 1: Face detected ✓
  → Photo 2: Face detected ✓
  → Photo 3: Face detected ✓
  ...
  → Photo 12: Face detected ✓
  → Photo 13: Different face detected! ⚠️
  → Photo 14: Matches main face ✓
  → Photo 15: Matches main face ✓
  
  ⚠️ Warning: Photo 13 appears to be a different person
  Action required: Review and reassign
```

**Benefits:**
- Catch photographer mistakes (wrong QR held up)
- Detect if someone moved during another person's shoot
- Quality assurance before sending to customers
- Reduce customer complaints about wrong photos

**Privacy & Performance:**
- ✅ 100% local processing (no cloud APIs)
- ✅ No face data stored permanently
- ✅ All in RAM, cleared after processing
- ✅ Optional feature (can disable if not needed)
- ⚠️ Adds processing time (~1-2 seconds per photo)
- ⚠️ Requires additional Python libraries

**Technical Notes:**
```python
# Pseudo-code for future implementation
def validate_person_photos(person_id, photo_paths):
    face_encodings = []
    
    # Get face from first photo (reference)
    reference_encoding = get_face_encoding(photo_paths[0])
    if not reference_encoding:
        return {"status": "no_face_in_qr_photo", "warnings": []}
    
    warnings = []
    
    # Compare all other photos
    for i, photo_path in enumerate(photo_paths[1:], start=2):
        encoding = get_face_encoding(photo_path)
        if not encoding:
            warnings.append(f"Photo {i}: No face detected")
            continue
        
        # Compare to reference face
        distance = face_distance(reference_encoding, encoding)
        if distance > THRESHOLD:  # Different person
            warnings.append(f"Photo {i}: Different person detected")
    
    # Clear all face data from memory
    del face_encodings, reference_encoding
    
    return {"status": "validated", "warnings": warnings}
```

**Implementation Plan (Future):**
1. Add dependency: `face-recognition` or `deepface`
2. Create `face_validator.py` module
3. Add admin setting: "Enable face validation" (default: off)
4. Add validation step in processing pipeline
5. Create admin UI to review flagged photos
6. Add manual reassignment interface
7. Performance optimization (parallel processing?)

**Decision Points:**
- Which library? `face_recognition` (simpler) vs `DeepFace` (more accurate)
- Validation threshold? (how strict should matching be?)
- Handle multiple faces in one photo? (group photos)
- Skip validation if only 1-2 photos per person?

---

## 📝 Current Implementation Scope

**Implementing Now:**
- ✅ QR code generation with personal data
- ✅ QR-based photo segmentation
- ✅ Google Drive integration
- ✅ Real-time status tracking
- ✅ Manual intervention interface

**Not Implementing Yet:**
- ⏸️ Face recognition validation (documented above for future)
- ⏸️ Automatic photo editing/filters
- ⏸️ Collage generation
- ⏸️ Print-ready formats
- ⏸️ Social media sharing

## 🚀 Deployment Considerations

- [ ] QR codes generated for all registrations
- [ ] Photos uploaded successfully
- [ ] QR detection accuracy > 95%
- [ ] All photos correctly grouped by person
- [ ] Drive folders created with correct permissions
- [ ] Emails delivered with valid links
- [ ] Temp files cleaned up automatically
- [ ] Admin can manually fix any issues
- [ ] System handles 1000+ photos per event
- [ ] Processing completes within reasonable time (< 1 hour for 1000 photos)

## � Status Tracking System

### Upload Progress
```
┌──────────────────────────────────────────┐
│  📤 Uploading Photos                     │
│  ━━━━━━━━━━━━━━━━━━━━━━░░░░ 1,234/2,000 │
│  Current: IMG_5678.jpg (3.2 MB)          │
│  Speed: 2.5 MB/s                         │
└──────────────────────────────────────────┘
```

### Processing Status Display
```
┌──────────────────────────────────────────┐
│  ⚙️ Processing Batch: Event_2025-10-22   │
│  ━━━━━━━━━━━━━━━━░░░░░░░░░░ 645/2,000   │
│                                          │
│  📸 Scanning: IMG_0645.jpg               │
│  ✅ Found QR Code: John Doe              │
│     john.doe@email.com                   │
│                                          │
│  Recent Actions:                         │
│  ✓ Assigned 18 photos to Jane Smith     │
│  ✓ Created Drive folder: Jane_Smith      │
│  ✓ Uploaded 18 photos to Drive          │
│  ⚙️ Processing Michael Johnson...        │
└──────────────────────────────────────────┘
```

### Status Messages Examples
- **Upload:** "Uploading 45/2000: IMG_0045.jpg (2.1 MB)"
- **Processing:** "Scanning photo 123/2000 for QR code..."
- **QR Detected:** "✓ Found QR: John|Doe|john@email.com|123|token"
- **Assigning:** "Assigning photos 124-138 to John Doe (john@email.com)"
- **Drive Upload:** "Creating Drive folder: John_Doe"
- **Drive Progress:** "Uploading photo 3/15 to Drive: IMG_0125.jpg"
- **Completed:** "✓ Processed 98 people, 1,856 photos, 2 unmatched"
- **Error:** "⚠️ Could not read QR from IMG_0999.jpg"

### API Endpoints for Status
```python
GET /admin/batch/<batch_id>/status
Returns: {
    "batch_id": 123,
    "status": "processing",
    "total_photos": 2000,
    "processed_photos": 645,
    "current_action": "Scanning photo 645/2000 for QR code...",
    "current_file": "IMG_0645.jpg",
    "recent_logs": [
        {"time": "14:32:15", "message": "Found QR: John Doe"},
        {"time": "14:32:10", "message": "Assigned 18 photos to Jane Smith"}
    ]
}

GET /admin/batch/<batch_id>/logs
Returns: Full processing log with all actions
```

## 🔍 QR Code Format Details

### Processing Algorithm

```python
# Pseudo-code for photo processing
current_person = None
current_person_photos = []
unmatched_photos = []

# CRITICAL: Sort photos by filename, NOT upload time
# Bulk uploads can arrive in any order, filename is sequential and reliable
sorted_photos = sorted(uploaded_photos, key=lambda p: p.filename)

for photo in sorted_photos:  # Process in FILENAME order
    qr_data = detect_qr_code(photo)
    
    if qr_data:  # QR code detected
        # Save previous person's photos
        if current_person:
            save_person_photos(current_person, current_person_photos)
            send_to_drive(current_person, current_person_photos)
        
        # Start new person
        current_person = parse_qr_data(qr_data)  # Extract name, email, ID
        current_person_photos = [photo]  # First photo includes QR
        
        log(f"✓ Found QR: {current_person.name} ({current_person.email})")
        
    else:  # Regular photo (no QR)
        if current_person:
            # Assign to current person
            current_person_photos.append(photo)
            log(f"  → Assigned to {current_person.name} ({len(current_person_photos)} photos)")
        else:
            # Photo before first QR code
            unmatched_photos.append(photo)
            log(f"⚠️ Unmatched photo (before first QR): {photo.filename}")

# Save last person's photos
if current_person:
    save_person_photos(current_person, current_person_photos)
    send_to_drive(current_person, current_person_photos)

# Report unmatched photos for manual review
if unmatched_photos:
    log(f"⚠️ {len(unmatched_photos)} unmatched photos need manual assignment")
```

### Example Processing Sequence

```
Upload Order: IMG_0001.jpg through IMG_2000.jpg

Processing:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[IMG_0001.jpg] 📸 Scanning...
               ✓ QR Detected: John|Doe|john@email.com|123|token-abc
               → Started Person #1: John Doe

[IMG_0002.jpg] 📸 Scanning...
               → No QR, assigned to John Doe (2 photos)

[IMG_0003.jpg] 📸 Scanning...
               → No QR, assigned to John Doe (3 photos)

...

[IMG_0018.jpg] 📸 Scanning...
               → No QR, assigned to John Doe (18 photos)

[IMG_0019.jpg] 📸 Scanning...
               ✓ QR Detected: Jane|Smith|jane@email.com|124|token-def
               ✅ Completed Person #1: John Doe (18 photos)
               → Started Person #2: Jane Smith

[IMG_0020.jpg] 📸 Scanning...
               → No QR, assigned to Jane Smith (2 photos)

...

[IMG_2000.jpg] 📸 Scanning...
               → No QR, assigned to Michael Johnson (15 photos)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Completed Person #100: Michael Johnson (15 photos)

Summary:
✓ Processed 100 people
✓ Matched 2,000 photos
⚠️ 0 unmatched photos
```

### Edge Cases Handled

1. **Photos Before First QR:**
   ```
   IMG_0001.jpg [No QR] → Unmatched (flag for manual review)
   IMG_0002.jpg [No QR] → Unmatched (flag for manual review)
   IMG_0003.jpg [QR: John] → Start Person #1
   ```

2. **Back-to-Back QR Codes:**
   ```
   IMG_0010.jpg [QR: John] → Person #1 with 1 photo (only QR)
   IMG_0011.jpg [QR: Jane] → Person #2 started, Person #1 complete
   ```

3. **Last Person:**
   ```
   IMG_1999.jpg [No QR] → Assigned to Person #100
   IMG_2000.jpg [No QR] → Assigned to Person #100 (last photo)
   [End of batch] → Person #100 automatically saved
   ```

4. **Corrupted/Unreadable QR:**
   ```
   IMG_0050.jpg [QR corrupted] → Treated as no QR, assigned to current person
                                  ⚠️ Log warning for review
   ```

### QR Content Structure
```
Format: first_name|last_name|email|registration_id|qr_token
Example: John|Doe|john.doe@email.com|123|a1b2c3d4-5678-90ef-ghij-klmnopqrstuv

Parsing:
parts = qr_data.split('|')
first_name = parts[0]
last_name = parts[1]
email = parts[2]
registration_id = parts[3]
qr_token = parts[4]
```

### Benefits of Personal Data in QR
1. **Database Loss Recovery:** Can manually match photos to people using name/email
2. **Visual Confirmation:** Admin can see who each photo set belongs to during processing
3. **Manual Intervention:** If QR detection fails, admin can read the QR data and assign manually
4. **Debugging:** Easy to verify correct person assignment
5. **Backup Matching:** Can match by email if registration_id is corrupted

### Privacy Considerations
- ⚠️ QR code contains personal information (name, email)
- ✅ Only stored temporarily in images during event
- ✅ Not exposed in public URLs or logs
- ✅ Images deleted after processing
- ✅ QR codes are in photos that customers took themselves
- ⚠️ Consider informing users in registration terms

## �📅 Estimated Timeline

- **Phase 1-2 (QR with Data & Upload with Progress):** 2-3 days
- **Phase 3-4 (Detection & Processing with Status):** 3-4 days
- **Phase 5 (Drive Integration with Progress):** 2-3 days
- **Phase 6-7 (UI & Email):** 2-3 days
- **Phase 8-9 (Status Dashboard & Cleanup):** 2-3 days
- **Phase 10 (Testing & Docs):** 2-3 days

**Total:** ~2-3 weeks for full implementation

## ✅ Requirements Clarified

1. **QR Code Delivery:** ✅ Included in confirmation email automatically
2. **Photos per Person:** ✅ Maximum ~20 photos
3. **Participants per Event:** ✅ Maximum ~100 persons
4. **Total Photos:** ✅ ~2,000 photos per event
5. **Google Drive Structure:** ✅ `Event_Folder/{FirstName_LastName}/` with individual share links
6. **Processing Speed:** ✅ Next day is sufficient (overnight processing acceptable)
7. **Photo Format:** ✅ Edited JPEGs uploaded by admin
8. **Customer Workflow:** ✅ Hold smartphone (with QR code email open) in first photo

## 🔧 Technical Decisions

- **QR Format:** `{first_name}|{last_name}|{email}|{registration_id}|{qr_token}`
  - Pipe-separated for easy parsing
  - Includes personal data for manual identification if database is lost
  - Still has unique token for validation
  - Example: `John|Doe|john@email.com|123|a1b2c3d4-uuid`
- **QR Size:** 300×300px (readable from smartphone screen at 1-2m distance)
- **Error Correction:** Level H (30% - highest, accounts for screen glare/movement)
- **Upload Method:** Drag & drop with real-time progress (file-by-file counter)
- **Processing:** Sequential with live status updates to admin interface
- **Status Tracking:** Database + live updates via polling/Server-Sent Events
- **Cleanup:** Auto-delete local files 7 days after Drive upload
- **Drive Permissions:** "Anyone with link can view" per person folder
