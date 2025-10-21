# Install Script Menu Structure

## Visual Flow Diagram

```
┌─────────────────────────────────────────┐
│   sudo bash install.sh                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────┴──────────────────────────┐
│  Check if Installation Exists?          │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
    [No]            [Yes]
       │               │
       ▼               ▼
┌──────────────┐  ┌────────────────────────────┐
│ Fresh        │  │ Management Menu:           │
│ Installation │  │ 1. Update                  │
│ Menu         │  │ 2. Reinstall               │
│              │  │ 3. Configure Settings ───┐ │
│ 1. Install   │  │ 4. Uninstall             │ │
│ 2. Cancel    │  │ 5. View Status           │ │
└──────────────┘  │ 6. Cancel                │ │
                  └────────────┬─────────────┘ │
                               │               │
                               │               │
                  ┌────────────┘               │
                  │                            │
                  ▼                            │
    ┌─────────────────────────┐               │
    │   Option Actions:       │               │
    │                         │               │
    │ 1. Update:              │               │
    │    - Stop service       │    ┌──────────┘
    │    - Backup database    │    │
    │    - Git pull           │    │
    │    - Update deps        │    ▼
    │    - Restart service    │  ┌───────────────────────────┐
    │                         │  │ Configure Settings Menu:  │
    │ 2. Reinstall:           │  │                           │
    │    - Backup data        │  │ 1. Change hostname        │
    │    - Remove install     │  │    for Nginx              │
    │    - Fresh install      │  │                           │
    │    - Restore data       │  │ 2. Install/Update         │
    │                         │  │    Nginx config           │
    │ 4. Uninstall:           │  │                           │
    │    - Optional backup    │  │ 3. Edit .env file         │
    │    - Stop service       │  │                           │
    │    - Remove all files   │  │ 4. Change SECRET_KEY      │
    │    - Clean system       │  │                           │
    │                         │  │ 5. Back to main menu      │
    │ 5. View Status:         │  └─────────┬─────────────────┘
    │    - Service status     │            │
    │    - Database info      │            │
    │    - Nginx config       │    ┌───────┴────────┐
    │    - Recent logs        │    │                │
    └─────────────────────────┘    ▼                ▼
                            ┌──────────────┐  ┌──────────────┐
                            │ Hostname     │  │ Nginx        │
                            │ Setup:       │  │ Install:     │
                            │              │  │              │
                            │ - Enter host │  │ - Install    │
                            │ - Create     │  │   nginx pkg  │
                            │   nginx conf │  │ - Create     │
                            │ - Test conf  │  │   config     │
                            │ - Reload     │  │ - Enable     │
                            │   nginx      │  │   site       │
                            └──────────────┘  │ - Reload     │
                                              │   nginx      │
                                              └──────────────┘
```

## Menu Options Detailed

### Main Menu (Existing Installation)

```
1) Update installation
   └─> Pulls latest code from git
   └─> Backs up database
   └─> Updates Python packages
   └─> Restarts service
   └─> Shows status

2) Reinstall
   └─> Backs up database and .env
   └─> Removes current installation
   └─> Performs fresh install
   └─> Restores backed up data
   └─> Starts service

3) Configure Settings
   └─> Opens Settings submenu (see below)

4) Complete removal
   └─> Prompts for confirmation
   └─> Optional database backup
   └─> Stops service
   └─> Removes all files
   └─> Removes nginx config
   └─> Cleans system

5) View status
   └─> Shows service status
   └─> Shows database info
   └─> Shows nginx config
   └─> Shows recent logs
   └─> Returns to menu

6) Cancel
   └─> Exits script
```

### Settings Configuration Submenu

```
1) Change hostname for Nginx
   └─> Prompts for hostname/domain
   └─> Offers to install nginx if missing
   └─> Creates nginx config from template
   └─> Replaces SERVER_NAME with hostname
   └─> Enables site in nginx
   └─> Tests configuration
   └─> Reloads nginx
   └─> Shows access URL

2) Install/Update Nginx configuration
   └─> Checks if nginx installed
   └─> Prompts to install if missing
   └─> Asks for hostname
   └─> Creates configuration
   └─> Enables site
   └─> Tests configuration
   └─> Reloads nginx
   └─> Shows configuration path

3) Edit .env file
   └─> Opens .env in editor (nano/vi)
   └─> Waits for user to save
   └─> Restarts service to apply changes
   └─> Confirms update

4) Change SECRET_KEY
   └─> Generates new random key
   └─> Shows preview of key
   └─> Prompts for confirmation
   └─> Updates .env file
   └─> Updates service file if needed
   └─> Restarts service
   └─> Confirms change

5) Back to main menu
   └─> Returns to main menu
```

## User Journey Examples

### Example 1: Fresh Installation
```
User: sudo bash install.sh
Script: Shows "Fresh Installation" menu
User: Selects option 1
Script: 
  - Installs dependencies
  - Creates virtual environment
  - Installs Python packages
  - Initializes database
  - Creates .env with SECRET_KEY
  - Installs systemd service
  - Starts application
  - Shows installation info
```

### Example 2: Update Existing Installation
```
User: sudo bash install.sh
Script: Detects existing installation, shows Management menu
User: Selects option 1 (Update)
Script:
  - Stops service
  - Backs up database
  - Backs up .env
  - Runs git pull
  - Restores .env
  - Updates Python packages
  - Restarts service
  - Shows status
```

### Example 3: Configure Nginx
```
User: sudo bash install.sh
Script: Shows Management menu
User: Selects option 3 (Configure Settings)
Script: Shows Settings menu
User: Selects option 1 (Change hostname)
Script: Prompts for hostname
User: Enters "photos.example.com"
Script:
  - Checks for nginx
  - Creates config with hostname
  - Enables site
  - Tests config
  - Reloads nginx
  - Shows success message
User: Returns to settings menu or main menu
```

### Example 4: Uninstall
```
User: sudo bash install.sh
Script: Shows Management menu
User: Selects option 4 (Complete removal)
Script: Shows warning, asks for confirmation
User: Types "yes"
Script: Asks about database backup
User: Selects "y"
Script:
  - Backs up database to ~/
  - Stops service
  - Disables service
  - Removes service file
  - Removes nginx config
  - Removes application directory
  - Removes log directory
  - Shows backup location
  - Exits
```

## Color Coding

The script uses color-coded output for better readability:

- 🔵 **BLUE (INFO)**: General information messages
- 🟢 **GREEN (SUCCESS)**: Successful operations
- 🟡 **YELLOW (WARNING)**: Warnings and important notices
- 🔴 **RED (ERROR)**: Errors and critical issues
- 🔷 **CYAN (HEADER)**: Section headers and menu titles

## Interactive Elements

1. **Numbered Menus**: Easy selection with number input
2. **Confirmation Prompts**: Safety checks for destructive operations
3. **Progress Messages**: Real-time feedback during operations
4. **Error Handling**: Graceful error messages with suggestions
5. **Status Display**: Comprehensive system status view
6. **Navigation**: Easy menu navigation with "Back" options

## Key Features

✅ **No Arguments Needed**: Interactive menu-driven interface
✅ **Context Aware**: Different menus for fresh vs existing installations
✅ **Safe Operations**: Confirmation prompts for destructive actions
✅ **Automatic Backups**: Database backed up during updates/uninstall
✅ **Self-Contained**: All operations in one script
✅ **User-Friendly**: Clear messages and helpful prompts
✅ **Idempotent**: Can run multiple times safely
✅ **Comprehensive**: Covers all lifecycle operations

---

**Last Updated**: October 21, 2025  
**Script Version**: 2.0 (Interactive Menu Edition)
