# Centralized Navigation Bar Component

## Overview
The `app-navbar` is a reusable navigation component that provides consistent navigation across all pages of the Burnout Prevention application.

## Features
- ✅ **Responsive Design** - Adapts to desktop, tablet, and mobile screens
- ✅ **Active Route Highlighting** - Automatically highlights the current page
- ✅ **Mobile Menu** - Hamburger menu for mobile devices
- ✅ **User Menu** - User profile and notifications
- ✅ **Material Design** - Uses Angular Material components
- ✅ **Sticky Navigation** - Stays at the top when scrolling

## Usage

### 1. Import SharedModule
The navbar is exported from the `SharedModule`. Import it in your feature module:

```typescript
import { SharedModule } from '../shared/shared-module';

@NgModule({
  imports: [
    // ... other imports
    SharedModule
  ]
})
export class YourModule { }
```

### 2. Add to Template
Simply add the component to your page template:

```html
<!-- At the top of your page -->
<app-navbar></app-navbar>

<!-- Your page content -->
<div class="your-content">
  <!-- ... -->
</div>
```

## Navigation Items
The navbar includes the following navigation items:
- **Dashboard** - `/hr/dashboard` - Overview and statistics
- **Employees** - `/hr/employees` - Employee management
- **Daily Logs** - `/hr/daily-logs` - Daily wellness logs
- **Predictions** - `/hr/predictions` - AI predictions
- **Reviews** - `/hr/reviews` - Manual reviews

## Customization

### Adding New Navigation Items
Edit `navbar.ts` and add items to the `navItems` array:

```typescript
navItems = [
  { label: 'Your Page', route: '/hr/your-page', icon: 'icon_name' },
  // ... existing items
];
```

### Changing Colors
The navbar uses the application's primary gradient. To customize, edit `navbar.css`:

```css
.navbar {
  background: linear-gradient(135deg, your-color-1, your-color-2);
}
```

### User Information
To display dynamic user information, update the `user-name` span in `navbar.html`:

```html
<span class="user-name">{{ currentUser?.name }}</span>
```

## Responsive Breakpoints
- **Desktop**: > 968px - Full horizontal menu
- **Tablet**: 640px - 968px - Condensed menu with icons
- **Mobile**: < 640px - Hamburger menu

## Components Used
- `MatIconModule` - Material icons
- `MatButtonModule` - Material buttons
- `MatBadgeModule` - Notification badges
- `RouterModule` - Angular routing

## File Structure
```
shared/
├── navbar/
│   ├── navbar.ts          # Component logic
│   ├── navbar.html        # Template
│   └── navbar.css         # Styles
└── shared-module.ts       # Module exports
```

## Examples

### Dashboard Page
```html
<app-navbar></app-navbar>

<div class="dashboard">
  <main class="main">
    <!-- Dashboard content -->
  </main>
</div>
```

### Other Pages
```html
<app-navbar></app-navbar>

<div class="page-container">
  <!-- Page content -->
</div>
```

## Notes
- The navbar is **sticky** and will remain at the top when scrolling
- Active route highlighting is automatic via `routerLinkActive`
- The mobile menu closes automatically when a route is selected
- Notification badge count is currently hardcoded (3) - update as needed
