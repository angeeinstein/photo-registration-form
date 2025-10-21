# Contributing to Photo Registration Form

Thank you for your interest in contributing to this project! This guide will help you understand how to make changes while maintaining compatibility with the automated installation system.

## 🔧 Install Script Compatibility

All changes to this repository **must** remain compatible with `install.sh`. The install script is designed to:

1. Handle fresh installations
2. Update existing installations
3. Preserve user data during updates
4. Manage system dependencies

### Critical Files

The following files are critical to the installation process:

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `gunicorn_config.py` - Gunicorn configuration
- `photo-registration.service` - systemd service template
- `templates/` - HTML templates directory
- `.env.example` - Environment variables template
- `install.sh` - Installation script

## 📋 Making Changes

### Adding New Python Dependencies

When adding new Python packages:

1. **Update `requirements.txt`**:
   ```bash
   pip freeze | grep package-name >> requirements.txt
   # Or manually add: package-name==version
   ```

2. **Test the installation**:
   ```bash
   python3 -m venv test_venv
   source test_venv/bin/activate
   pip install -r requirements.txt
   deactivate
   rm -rf test_venv
   ```

3. **The install script will automatically**:
   - Install new dependencies during fresh installation
   - Update dependencies when user chooses "Update installation"

### Adding System Dependencies

If you need system packages (e.g., PostgreSQL, Redis):

1. **Update `install.sh`** in the `install_dependencies()` function:
   ```bash
   # For Ubuntu/Debian
   ubuntu|debian)
       apt-get install -y \
           your-new-package \
           || { print_error "..."; exit 1; }
       ;;
   
   # For CentOS/RHEL/Fedora
   centos|rhel|fedora)
       yum install -y \
           your-new-package \
           || { print_error "..."; exit 1; }
       ;;
   ```

2. **Document the change** in `CHANGELOG.md`

### Adding New Configuration Options

When adding configuration to `.env`:

1. **Update `.env.example`** with the new variable and documentation:
   ```bash
   # New Feature Configuration
   NEW_FEATURE_ENABLED=false
   NEW_FEATURE_API_KEY=your-api-key-here
   ```

2. **Update `app.py`** to read the variable:
   ```python
   app.config['NEW_FEATURE_ENABLED'] = os.environ.get('NEW_FEATURE_ENABLED', 'false').lower() == 'true'
   ```

3. **Update `README.md`** with configuration instructions

4. The install script preserves `.env` during updates automatically

### Modifying the Database Schema

When changing the database structure:

1. **Add migration logic** to `app.py` or create a migration script

2. **Update the `init_db()` function** if needed

3. **Test with existing database**:
   ```bash
   # Backup test database
   cp registrations.db registrations.db.backup
   
   # Run migration
   python app.py
   
   # Verify data integrity
   sqlite3 registrations.db "SELECT * FROM registration;"
   ```

4. **Document migration steps** in `CHANGELOG.md` and `README.md`

5. The install script backs up the database during updates

### Adding New Routes/Endpoints

When adding new Flask routes:

1. **Add route to `app.py`**:
   ```python
   @app.route('/new-endpoint')
   def new_endpoint():
       return jsonify({'message': 'New feature'})
   ```

2. **Update `test-installation.sh`** to test the new endpoint:
   ```bash
   print_test "Testing new endpoint..."
   response=$(curl -s -o /dev/null -w "%{http_code}" ${APP_URL}/new-endpoint)
   if [[ "$response" == "200" ]]; then
       print_pass "New endpoint works"
   fi
   ```

3. **Document in `README.md`** under API Endpoints section

### Modifying systemd Service

When changing `photo-registration.service`:

1. **Test the service configuration**:
   ```bash
   # Validate syntax
   systemd-analyze verify photo-registration.service
   ```

2. **The install script will**:
   - Update service file during updates
   - Reload systemd daemon
   - Restart the service

3. **Document changes** in `CHANGELOG.md`

### Changing Directory Structure

If you need to change where files are located:

1. **Update paths in multiple files**:
   - `install.sh` (INSTALL_DIR, LOG_DIR, etc.)
   - `gunicorn_config.py` (log paths, pidfile)
   - `photo-registration.service` (WorkingDirectory, ExecStart)
   - `README.md` (documentation)

2. **Test fresh installation** and **update installation** scenarios

## 🧪 Testing Your Changes

### Before Committing

1. **Test fresh installation**:
   ```bash
   # On a test VM or container
   git clone <your-fork>
   cd photo-registration-form
   sudo bash install.sh
   sudo bash test-installation.sh
   ```

2. **Test update process**:
   ```bash
   # Install old version first
   git checkout <previous-release>
   sudo bash install.sh
   
   # Test registration works
   curl -X POST http://127.0.0.1:5000/register \
     -d "first_name=Test&last_name=User&email=test@example.com"
   
   # Update to new version
   git checkout <your-branch>
   sudo bash install.sh
   # Choose option 1 (Update)
   
   # Verify service still works
   sudo bash test-installation.sh
   
   # Verify data preserved
   curl http://127.0.0.1:5000/registrations
   ```

3. **Test uninstall**:
   ```bash
   sudo bash uninstall.sh
   # Verify all files removed
   ```

### Test Checklist

- [ ] Fresh installation works
- [ ] Update preserves database
- [ ] Update preserves .env file
- [ ] Service starts and runs
- [ ] All endpoints respond correctly
- [ ] Logs are created properly
- [ ] Uninstall removes everything
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated

## 📝 Commit Guidelines

### Commit Message Format

```
<type>: <short summary>

<detailed description>

Install Script: <compatibility notes>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example**:
```
feat: Add PostgreSQL database support

- Add PostgreSQL connection option via DATABASE_URI
- Update requirements.txt with psycopg2
- Add PostgreSQL installation to install.sh
- Update documentation with PostgreSQL setup

Install Script: Compatible - install.sh updated to install 
PostgreSQL packages. Users need to configure DATABASE_URI 
in .env for PostgreSQL support.
```

## 🔄 Update Workflow

When you make changes that affect deployment:

1. **Update `CHANGELOG.md`**:
   ```markdown
   ## [1.1.0] - 2025-10-XX
   
   ### Added
   - New feature description
   
   ### Changed
   - What changed
   
   ### Installation Notes
   - Special steps needed for update
   ```

2. **Update `README.md`** with new features/configuration

3. **Test installation script** with your changes

4. **Tag release** after merge:
   ```bash
   git tag -a v1.1.0 -m "Version 1.1.0"
   git push origin v1.1.0
   ```

## 🐛 Common Issues and Solutions

### Issue: New dependency not installing

**Solution**: Check if the package is in `requirements.txt` and test:
```bash
pip install -r requirements.txt --dry-run
```

### Issue: Service fails to start after update

**Solution**: 
1. Check logs: `sudo journalctl -u photo-registration -n 100`
2. Verify permissions: `ls -la /opt/photo-registration-form`
3. Test app manually: `source venv/bin/activate && python app.py`

### Issue: Database migration fails

**Solution**: 
1. The install script backs up database during update
2. Find backup: `/opt/photo-registration-form/registrations.db.backup.*`
3. Restore if needed: `cp backup.db registrations.db`

## 🤝 Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes following this guide
4. Test installation script compatibility
5. Update documentation and CHANGELOG
6. Commit with clear messages
7. Push to your fork
8. Create Pull Request with:
   - Description of changes
   - Testing performed
   - Install script compatibility notes
   - Screenshots if applicable

## 📧 Questions?

If you're unsure about install script compatibility, please:
1. Open an issue describing your planned changes
2. Ask for guidance before implementing
3. We're happy to help!

---

Thank you for contributing! 🎉
