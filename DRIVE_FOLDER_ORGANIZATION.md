# Google Drive Folder Organization

## Problem
Previously, all person folders were created directly in the root of Google Drive (or the configured parent folder), creating clutter and making it hard to organize photos from different events.

## Solution: Event-Based Folder Organization

### New Folder Structure
```
Google Drive (or configured parent folder)
└── PhotoRegistration_2025-10-23_1430/  ← Batch/Event folder
    ├── John_Doe/
    │   ├── photo1.jpg
    │   ├── photo2.jpg
    │   └── photo3.jpg
    ├── Jane_Smith/
    │   ├── photo1.jpg
    │   └── photo2.jpg
    └── Bob_Johnson/
        ├── photo1.jpg
        ├── photo2.jpg
        ├── photo3.jpg
        └── photo4.jpg
```

### Before (Cluttered)
```
Google Drive
├── John_Doe/
├── Jane_Smith/
├── Bob_Johnson/
├── Alice_Williams/
├── ... (hundreds of folders)
```

### After (Organized)
```
Google Drive
├── Wedding_2025-10-15/
│   ├── John_Doe/
│   ├── Jane_Smith/
│   └── ...
├── Birthday_Party_2025-10-20/
│   ├── Bob_Johnson/
│   ├── Alice_Williams/
│   └── ...
└── PhotoRegistration_2025-10-23_1430/
    └── ...
```

## Implementation Details

### Event Folder Naming

**Automatic naming (default):**
```python
# Uses batch name if available
event_folder_name = batch.batch_name
# Example: "Batch_20251023_143052"
```

**Fallback naming:**
```python
# If no batch name, auto-generates with timestamp
event_folder_name = f"PhotoRegistration_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
# Example: "PhotoRegistration_2025-10-23_1430"
```

### Folder Reuse
- If multiple people are processed in the same batch, they all go into the same event folder
- The event folder is created once and reused for all people in that batch
- Different batches create different event folders

### Parent Folder Support
You can still configure a parent folder in your Drive settings:

```
Your Configured Parent Folder/
└── PhotoRegistration_2025-10-23_1430/
    ├── John_Doe/
    └── Jane_Smith/
```

**How to set parent folder:**
1. Go to Admin Dashboard → Google Drive Settings
2. Enter the folder ID of your desired parent folder
3. All event folders will be created inside that folder

**Finding a folder ID:**
1. Open the folder in Google Drive
2. Look at the URL: `https://drive.google.com/drive/folders/ABC123XYZ`
3. The folder ID is `ABC123XYZ`

## Benefits

✅ **Better Organization** - Events/batches are clearly separated  
✅ **Easy Navigation** - Find photos by event date  
✅ **No Clutter** - Root Drive folder stays clean  
✅ **Automatic** - No manual setup required  
✅ **Compatible** - Works with both OAuth and Service Account  
✅ **Reusable** - Same batch = same event folder  

## Examples

### Wedding Photography
```
Wedding_Smith-Johnson_2025-10-15/
├── Guest_John_Doe/
├── Guest_Jane_Smith/
├── Bride_Sarah_Johnson/
└── Groom_Mike_Smith/
```

### Birthday Party
```
Birthday_Party_2025-10-20/
├── Birthday_Boy_Tommy/
├── Parent_Alice_Williams/
└── Guest_Bob_Johnson/
```

### Corporate Event
```
CompanyEvent_2025-11-01/
├── Employee_John_Doe/
├── Employee_Jane_Smith/
└── Guest_Client_Name/
```

## Technical Notes

### Folder Creation Process
1. Check if event folder exists (by name)
2. If exists: Reuse it (for same batch)
3. If not: Create new event folder
4. Create person folder inside event folder
5. Upload photos to person folder

### Sanitization
Batch names are sanitized for Drive compatibility:
```python
event_folder_name = batch_name.replace('/', '-').replace('\\', '-')
```

### Error Handling
- If event folder creation fails, falls back to root
- If person folder creation fails, entire upload fails with clear error
- All failures are logged for troubleshooting

## Configuration

### For OAuth Users (Most Common)
No configuration needed! Event folders are created automatically.

Optional: Set a parent folder in Admin Dashboard → Google Drive Settings

### For Service Account Users
Same behavior - event folders created automatically.

Parent folder can be configured in the service account credentials setup.

## Migration

### Existing Setups
- Existing person folders in root will remain
- New uploads will use the new event folder structure
- No automatic migration of old folders

### Clean Start
If you want to reorganize existing folders:
1. Manually create event folders in Drive
2. Move existing person folders into appropriate event folders
3. New uploads will automatically use the new structure

## Summary

All person folders are now automatically organized into event folders, preventing Drive clutter while maintaining easy access to photos. The batch/event name is used for the folder, making it easy to find photos by date or event name.
