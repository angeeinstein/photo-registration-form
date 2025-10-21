# Static Assets Directory

This directory contains all static assets (CSS, JavaScript, images) for the Photo Registration application.

## 📁 Directory Structure

```
static/
├── css/                    # Stylesheets
│   ├── style.css          # Main registration form styles
│   ├── admin.css          # Admin dashboard & settings styles
│   ├── login.css          # Admin login page styles
│   └── email-accounts.css # Email accounts management styles
├── img/                    # Images and logos
│   └── (add your images here)
└── js/                     # JavaScript files
    └── (future JavaScript files)
```

## 📄 CSS Files Overview

### style.css
- **Used by:** `index.html` (public registration form)
- **Features:** Gradient background, animated form, photo preview, responsive design
- **Color scheme:** Purple gradient (#667eea to #764ba2)
- **Customization:** Form inputs, buttons, photo upload area

### admin.css
- **Used by:** `admin_dashboard.html`, `admin_settings.html`
- **Features:** Stats cards, data tables, badges, buttons, responsive grid layout
- **Color scheme:** Purple accents (#667eea) on white background
- **Customization:** Dashboard cards, table styles, button variants

### login.css
- **Used by:** `admin_login.html`
- **Features:** Centered login form, gradient background, lock icon, animations
- **Color scheme:** Purple gradient matching main theme
- **Customization:** Login form, background gradient

### email-accounts.css
- **Used by:** `email_accounts.html`, `email_account_form.html`
- **Features:** Card grid layout, account badges, test email forms, responsive design
- **Color scheme:** Purple gradient with card-based UI
- **Customization:** Account cards, form layouts, badges

## 🎨 Adding Your Logo

To add your company/event logo to the application:

### 1. Add Logo File

Place your logo file in the `static/img/` directory. Recommended formats:
- PNG (with transparent background)
- SVG (scalable vector graphics)
- JPG/JPEG

Example: `static/img/logo.png`

### 2. Update Templates

The logo placeholders are already in the templates. Just uncomment and update the path:

#### Registration Form (`templates/index.html`):
```html
<!-- Uncomment and update this section -->
<div class="logo-container">
    <img src="{{ url_for('static', filename='img/logo.png') }}" alt="Your Company Logo">
</div>
```

#### Admin Login (`templates/admin_login.html`):
```html
<!-- Uncomment and update this section -->
<div class="logo-container">
    <img src="{{ url_for('static', filename='img/logo.png') }}" alt="Your Company Logo">
</div>
```

#### Admin Dashboard (add to `templates/admin_dashboard.html` header):
```html
<div class="header">
    <div class="logo-container">
        <img src="{{ url_for('static', filename='img/logo.png') }}" alt="Logo">
    </div>
    <h1>📊 Admin Dashboard</h1>
    <!-- ... rest of header ... -->
</div>
```

### 3. Logo Sizing

The CSS already handles logo sizing. Default maximums:
- **Registration Form:** max-width: 200px
- **Admin Login:** max-width: 150px  
- **Admin Dashboard:** max-height: 60px

To customize, edit the respective CSS file:
```css
.logo-container img {
    max-width: 200px;  /* Adjust as needed */
    height: auto;
}
```

## 🎨 Customizing Colors/Branding

### Change Brand Colors

Edit the CSS files to match your brand:

**Primary Gradient:** (used in buttons and backgrounds)
```css
/* In style.css and login.css */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change to your brand colors */
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

**Accent Colors:**
```css
/* Primary color for links, hover states */
color: #667eea;  /* Change to your brand color */
```

## 📝 Adding Custom CSS

### Method 1: Edit Existing Files
Add your custom styles to the appropriate CSS file:
- `style.css` - Registration form customization
- `admin.css` - Admin dashboard customization
- `login.css` - Login page customization

### Method 2: Create New CSS File
1. Create a new CSS file: `static/css/custom.css`
2. Add your custom styles
3. Link it in the template after the main stylesheet:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
```

## 🖼️ Adding Other Images

### Background Images
To add a custom background instead of gradient:

```css
/* In style.css or login.css */
body {
    background: url('{{ url_for('static', filename='img/background.jpg') }}') no-repeat center center fixed;
    background-size: cover;
}
```

### Icons/Decorative Images
Add images in templates:
```html
<img src="{{ url_for('static', filename='img/your-image.png') }}" alt="Description">
```

## 🔄 Cache Busting

The templates already include cache-busting for CSS files:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}?v={{ range(1, 10000) | random }}">
```

This ensures browsers load the latest version after updates. No action needed!

## 📱 Responsive Design

All stylesheets include responsive breakpoints:
- Mobile: < 600px
- Tablet: 600px - 768px
- Desktop: > 768px

Test your logo and customizations on different screen sizes.

## 🎨 Example Customization

Complete example of adding a logo and custom colors:

### 1. Add Files:
```
static/
├── img/
│   ├── logo.png
│   └── favicon.ico
└── css/
    └── custom.css
```

### 2. Customize Colors (`static/css/custom.css`):
```css
/* Override brand colors */
:root {
    --brand-primary: #ff6b6b;
    --brand-secondary: #4ecdc4;
}

body {
    background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-secondary) 100%);
}

.btn-primary {
    background: var(--brand-primary);
}

.header h1 {
    color: var(--brand-primary);
}
```

### 3. Update Template (`templates/index.html`):
```html
<head>
    ...
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/custom.css') }}">
    <link rel="icon" href="{{ url_for('static', filename='img/favicon.ico') }}">
</head>
<body>
    <div class="container">
        <div class="logo-container">
            <img src="{{ url_for('static', filename='img/logo.png') }}" alt="Event Logo">
        </div>
        ...
    </div>
</body>
```

## ✨ Tips

1. **Optimize Images:** Compress logos/images before uploading
2. **Use SVG:** When possible, use SVG for logos (scales perfectly)
3. **Test Mobile:** Always test logo placement on mobile devices
4. **Brand Consistency:** Use the same logo across all pages
5. **Accessibility:** Always include descriptive `alt` text for images

## 🚀 After Making Changes

1. **Clear Browser Cache:** Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
2. **Restart Flask:** If running in development mode
3. **Check All Pages:** Test registration form, login, and dashboard

---

Need help? Check the main README.md for contact information!
