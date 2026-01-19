# shadcn/ui Interactive Playground

**Created**: 2025-12-22  
**Status**: Production Ready ✅  
**Location**: `/srv/data/apps/fibreflow/public/shadcn-enhanced-v2-demo.html`

## Overview

A comprehensive, interactive design system playground for **shadcn/ui** - a popular React component library. This single-page HTML application allows developers and designers to visually experiment with UI design configurations and export production-ready CSS.

## Access URLs

- **Primary**: `http://100.96.203.105:3005/shadcn-enhanced-v2-demo.html`
- **Alternative**: `https://velo-server:9090/shadcn-enhanced-v2-demo.html`
- **Alternative**: `https://192.168.1.150:9090/shadcn-enhanced-v2-demo.html`

## What It Does

### 🎨 Visual Customization (Real-time)
- **6 Color Themes**: Blue, Green, Orange, Red, Violet, Rose
- **5 Font Families**: Inter, Roboto, Outfit, Poppins, Montserrat
- **5 Border Radius Options**: None (0) to XL (1rem)
- **5 Animation Speeds**: Instant (0ms) to Very Slow (500ms)
- **4 Density Levels**: Compact (0.75x) to Spacious (1.5x)
- **5 Shadow Intensities**: None (0) to Dramatic (2x)
- **4 Typography Scales**: Tight (0.875x) to Large (1.25x)
- **Dark/Light Mode Toggle**

### 🎮 Interactive Components (28+ Components)

All components are fully functional and respond to user interaction:

#### Core Interactive Elements
- **Dialog/Modal** - Overlay dialogs with backdrop
- **Dropdown Menu** - Contextual menus with options
- **Toast Notifications** - Slide-in notifications
- **Switch/Toggle** - On/off toggles with state labels
- **Checkbox** - Checkable inputs with visual feedback
- **Radio Groups** - Single-selection radio buttons
- **Tabs** - Multi-tab content switching
- **Progress Bars** - Adjustable progress indicators

#### Standard Components
- **Buttons** - 5 variants (Primary, Secondary, Outline, Destructive, Ghost)
- **Badges** - 3 variants (Primary, Secondary, Outline)
- **Input Fields** - Text, email, password, textarea with focus states
- **Alerts** - 4 types (Info, Success, Warning, Error)
- **Typography** - All heading levels and text sizes
- **Cards** - Nested cards with shadows
- **Skeleton Loaders** - Animated loading states
- **Chart Components** - Interactive bar charts with hover effects

### 📋 Export Functionality

**CSS Configuration Export**:
- Click "Copy to Clipboard" button
- Paste into your project's `globals.css` file
- Instantly apply the exact theme you configured

Example export:
```css
:root {
  --radius: 0.75rem;
  --animation-speed: 300ms;
  --spacing-scale: 1.25;
  --shadow-intensity: 1.5;
  --typography-scale: 1;

  --primary: 142.1 76.2% 36.3%;
  --primary-foreground: 355.7 100% 97.3%;
  --ring: 142.1 76.2% 36.3%;
}

body {
  font-family: 'Poppins', sans-serif;
}
```

## Features

### Visual Feedback System
- **Pulsing Active Controls** - Active settings have glowing animation
- **Change Notifications** - Toast notifications appear for every change
- **Live Preview Banner** - Prominent banner showing real-time updates
- **Current Configuration Display** - Dashboard showing all active settings

### Persistence
- **LocalStorage** - Settings persist across page reloads
- **State Management** - Maintains configuration between sessions

### User Experience
- **Instant Updates** - All changes apply in real-time (0ms delay)
- **Smooth Animations** - Configurable animation speeds
- **Responsive Design** - Works on all screen sizes
- **Accessibility** - Proper focus states and keyboard navigation

## Technical Details

### File Structure
```
/srv/data/apps/fibreflow/public/
└── shadcn-enhanced-v2-demo.html (56KB)
    ├── Embedded CSS (custom properties + component styles)
    ├── Embedded JavaScript (state management + interactivity)
    └── HTML (component showcase + controls)
```

### Technology Stack
- **Pure HTML/CSS/JavaScript** - No build process required
- **Tailwind CSS** - Via CDN for utility classes
- **Google Fonts** - 5 font families loaded on demand
- **CSS Custom Properties** - For dynamic theming
- **LocalStorage API** - For state persistence

### Performance
- **File Size**: 56KB (single file, no dependencies)
- **Load Time**: <1 second on local network
- **Interactivity**: Instant (JavaScript-driven, no server calls)
- **Memory**: Minimal (no frameworks, vanilla JS)

## Use Cases

### 1. Design System Development
- Experiment with color palettes before committing to code
- Test different font combinations
- Find optimal spacing and shadow values
- Preview dark mode variants

### 2. Client Presentations
- Show clients different theme options interactively
- Get real-time feedback on design preferences
- Export chosen configuration immediately

### 3. Developer Onboarding
- Learn shadcn/ui component behavior
- Understand CSS custom property patterns
- See how different settings affect components

### 4. Prototyping
- Quickly mock up UI designs
- Test component interactions
- Validate design decisions before implementation

## How to Use

### Basic Workflow
1. **Open the playground** in your browser
2. **Click any control** (color, font, spacing, etc.)
3. **Watch the page update** in real-time
4. **Experiment** with different combinations
5. **Copy the CSS** when you find a design you like
6. **Paste into your project** and you're done!

### Advanced Usage
- **Test Dark Mode**: Toggle dark mode to see how your theme looks
- **Component Testing**: Interact with all components to verify behavior
- **Responsive Testing**: Resize browser to test different screen sizes
- **Export Multiple Themes**: Save different configurations for comparison

## Maintenance

### Updating the Playground

**Local Development**:
```bash
# Edit locally
nano /home/louisdup/Agents/claude/shadcn-enhanced-v2-demo.html

# Deploy to server
scp /home/louisdup/Agents/claude/shadcn-enhanced-v2-demo.html \
    louis@100.96.203.105:/srv/data/apps/fibreflow/public/
```

**Direct Server Edit** (not recommended):
```bash
ssh louis@100.96.203.105
nano /srv/data/apps/fibreflow/public/shadcn-enhanced-v2-demo.html
# No restart needed - static file served directly
```

### Adding New Components
1. Add HTML markup in the component showcase section
2. Add CSS styles in the `<style>` block
3. Add JavaScript event handlers if interactive
4. Test all theme combinations

### Adding New Themes
1. Add color values to `themes` object in JavaScript
2. Add theme circle in HTML with appropriate color
3. Update `applyTheme()` function if needed

## Troubleshooting

### Page Not Loading
- **Check FibreFlow service**: `ssh louis@100.96.203.105 "systemctl status fibreflow"`
- **Check port 3005**: `curl http://100.96.203.105:3005`
- **Restart if needed**: `ssh louis@100.96.203.105 "cd /srv/data/apps/fibreflow && ./restart.sh"`

### Changes Not Saving
- **Clear LocalStorage**: Open browser console → `localStorage.clear()` → Reload
- **Check browser**: Ensure cookies/localStorage not blocked

### Components Not Interactive
- **Check JavaScript errors**: Open browser console (F12)
- **Verify file integrity**: Compare file size (should be ~56KB)
- **Hard refresh**: Ctrl+Shift+R to clear cache

## Related Files

- **Source**: `/home/louisdup/Agents/claude/shadcn-enhanced-v2-demo.html`
- **Server**: `/srv/data/apps/fibreflow/public/shadcn-enhanced-v2-demo.html`
- **Documentation**: `/home/louisdup/Agents/claude/docs/tools/SHADCN_PLAYGROUND.md` (this file)
- **Demo Videos**: 
  - `~/.gemini/antigravity/brain/.../shadcn_interactive_demo.webp`
  - `~/.gemini/antigravity/brain/.../full_interactive_demo.webp`
  - `~/.gemini/antigravity/brain/.../complete_component_demo.webp`

## Version History

### v2 (2025-12-22)
- ✅ Added visual notification system for all changes
- ✅ Added pulsing animations to active controls
- ✅ Added live preview banner
- ✅ Enhanced interactivity feedback
- ✅ Tested all 28+ components
- ✅ Documented in CLAUDE.md

### v1 (2025-12-22)
- Initial creation with basic interactivity
- 28+ components implemented
- Theme customization system
- CSS export functionality

## Future Enhancements

### Potential Additions
- [ ] More color themes (Teal, Purple, Amber)
- [ ] Custom color picker for primary color
- [ ] Component code snippets (copy React/HTML code)
- [ ] Preset theme library (Material, iOS, etc.)
- [ ] Comparison mode (side-by-side themes)
- [ ] Screenshot export of current design
- [ ] Share configuration via URL parameters
- [ ] Integration with FibreFlow design system

## Support

For issues or questions:
1. Check this documentation first
2. Review browser console for errors
3. Verify file exists on server
4. Check FibreFlow service status
5. Contact: Louis (VF Server admin)

---

**Last Updated**: 2025-12-22  
**Maintained By**: FibreFlow Development Team  
**Server**: VF Velocity Server (100.96.203.105)
