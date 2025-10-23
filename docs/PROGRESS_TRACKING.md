# Progress Tracking Improvements

## Problem
Previously, the progress bar would show 100% after scanning all photos, but Drive upload would still be running for several minutes, making it seem like the process was stuck.

## Solution: Two-Phase Progress Display

### Phase Breakdown:
```
0% ─────────────── 80% ──────── 100%
    Phase 1            Phase 2
 (Photo Scanning)  (Drive Upload)
```

### Phase 1: Photo Scanning & QR Detection (0-80%)
- Scanning each photo for QR codes
- Matching QR codes to registrations
- Grouping photos by person
- Saving photos to local folders
- **Progress:** Based on `processed_photos / total_photos × 80%`

### Phase 2: Google Drive Upload (80-100%)
- Creating Drive folders for each person
- Uploading photos to respective folders
- Generating share links
- Sending confirmation emails
- **Progress:** Based on `uploaded_people / total_people × 20%` + 80%

## Visual Improvements

### Progress Bar
```html
Before: [████████████████████] 100% (but still uploading...)

After:  [████████████────────] 65%
        🔍 Phase 1: Scanning Photos & Detecting QR Codes (0-80%)
        
        [████████████████████] 95%
        📤 Phase 2: Uploading to Google Drive (80-100%)
        
        [████████████████████] 100%
        ✓ Processing Complete
```

### Phase Indicators
- **Phase 1:** Purple icon 🔍 - "Scanning Photos & Detecting QR Codes (0-80%)"
- **Phase 2:** Blue icon 📤 - "Uploading to Google Drive (80-100%)"
- **Complete:** Green checkmark ✓ - "Processing Complete"

## Technical Implementation

### Backend (app.py)
```python
# Calculate progress with two phases
if 'Phase 2' in current_action or 'Drive' in current_action:
    # Phase 2: 80-100%
    uploaded_count = count_uploaded_to_drive()
    upload_progress = (uploaded_count / people_found) * 20
    progress_pct = 80 + upload_progress
else:
    # Phase 1: 0-80%
    progress_pct = (processed_photos / total_photos) * 80
```

### Frontend (JavaScript)
```javascript
// Show appropriate phase indicator
if (currentAction.includes('Phase 2') || currentAction.includes('Drive')) {
    phaseIndicator.innerHTML = '📤 Phase 2: Uploading to Google Drive (80-100%)';
} else if (status === 'processing') {
    phaseIndicator.innerHTML = '🔍 Phase 1: Scanning Photos & Detecting QR Codes (0-80%)';
}
```

## User Experience Improvements

### Before:
1. Progress: 0% → 50% → 100% ✓
2. User: "Great, it's done!"
3. *Wait 5 minutes while Drive uploads*
4. User: "Is it stuck? Did it crash?"
5. Finally completes

### After:
1. Progress: 0% → 40% → 80% 🔍
2. Phase changes: "📤 Phase 2: Uploading to Google Drive"
3. Progress: 80% → 85% → 90% → 95% → 100% ✓
4. User: "I can see it's uploading, almost done!"
5. Completes with clear feedback

## Example Timeline

**100 photos, 10 people:**

```
Time    Progress    Phase       Action
────────────────────────────────────────────────────
0:00    0%         Phase 1     Starting...
0:05    10%        Phase 1     Scanned 12 photos
0:10    20%        Phase 1     Scanned 25 photos
0:30    50%        Phase 1     Scanned 62 photos
0:50    80%        Phase 1     All photos scanned!
0:51    80%        Phase 2     Uploading Person 1
1:00    82%        Phase 2     Uploading Person 2
1:10    84%        Phase 2     Uploading Person 3
1:50    98%        Phase 2     Uploading Person 10
2:00    100%       Complete    ✓ Done!
```

**With fast QR detection (after optimization):**
```
Time    Progress    Phase       Action
────────────────────────────────────────────────────
0:00    0%         Phase 1     Starting...
0:02    20%        Phase 1     Scanned 25 photos (fast!)
0:05    50%        Phase 1     Scanned 62 photos
0:08    80%        Phase 1     All photos scanned!
0:09    80%        Phase 2     Uploading Person 1
0:18    82%        Phase 2     Uploading Person 2
...
1:00    100%       Complete    ✓ Done!
```

## Benefits

✅ **Clear Expectations** - Users know exactly what's happening  
✅ **Accurate Progress** - No more "stuck at 100%"  
✅ **Phase Visibility** - Can see transition between scanning and uploading  
✅ **Better UX** - Reduces anxiety and support requests  
✅ **Realistic Timing** - Progress matches actual work being done  

## Configuration

No configuration needed - automatic detection of phases based on:
- `current_action` text content
- `batch.status` value
- Drive upload completion tracking

The progress calculation adapts automatically to batch size and complexity.
