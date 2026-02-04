# Prison Roll Call - Customer Presentation

Professional presentation slides for non-technical stakeholders (facility managers, administrators, procurement officers).

## 📐 Slide Specifications

- **Resolution:** 1920x1080 (Full HD landscape)
- **Format:** HTML + CSS (viewable in any browser)
- **Style:** Modern, clean, professional
- **Colors:** Security-themed blues, greens, grays

## 🎯 Quick Start

**View the complete presentation:**
- Open **`index.html`** in your browser for slide navigation
- Or jump directly to **`slide-01-cover.html`** to start presenting

## 📑 All Slides

1. **`slide-01-cover.html`** - Cover slide with key metrics
2. **`slide-02-problem.html`** - Before/After comparison
3. **`slide-03-journey.html`** - User journey timeline
4. **`slide-04-benefits.html`** - Benefits dashboard with ROI
5. **`slide-05-security.html`** - Security & privacy features
6. **`slide-06-setup.html`** - Physical setup diagram
7. **`slide-07-confidence.html`** - Confidence system explained
8. **`slide-08-screens.html`** - Screen showcase mockups
9. **`slide-09-timeline.html`** - Implementation timeline
10. **`slide-10-support.html`** - Support & training package
11. **`slide-11-casestudy.html`** - Pilot program results
12. **`slide-12-nextsteps.html`** - Next steps CTA

## 👀 How to View

### Option 1: Index Page (Recommended)
```bash
# Open the index page to see all slides
open index.html

# Or with a local server:
python -m http.server 8080
# Then: http://localhost:8080/
```

### Option 2: Direct File Open
```bash
# Open in your default browser
open slide-01-cover.html
# Navigate through slides manually
```

### Option 3: Local Server
```bash
# From this directory
python -m http.server 8080

# Then open in browser:
# http://localhost:8080/index.html
```

### Option 3: Live Server (VS Code)
1. Install "Live Server" extension
2. Right-click any HTML file
3. Select "Open with Live Server"

## 🎯 Design Features

### Typography
- **Headlines:** Bold, impactful, large (5rem / 3.5rem)
- **Body:** Clear, readable (1.5rem base)
- **Captions:** Uppercase, spaced (1.25rem)

### Color Palette
- **Primary Blue (#2563eb):** Trust, security, technology
- **Success Green (#059669):** Positive outcomes, efficiency
- **Alert Red (#dc2626):** Warnings, critical info
- **Warning Amber (#f59e0b):** Caution, review needed

### Components
- **Cards:** Elevated, rounded, hoverable
- **Badges:** Status indicators (success/warning/error)
- **Stats:** Large numbers with labels
- **Timeline:** Visual chronological flow
- **Icons:** Emoji-based (universal, no dependencies)

## 📋 Complete Slide Deck

All 12 slides are ready! ✅

1. **Cover** - Introduction with key metrics ✅
2. **Before/After** - Traditional vs modern comparison ✅
3. **User Journey** - Step-by-step officer experience ✅
4. **Benefits Dashboard** - ROI metrics and value props ✅
5. **Security & Privacy** - Air-gapped, encrypted, compliant ✅
6. **Physical Setup** - Simple deployment diagram ✅
7. **Confidence System** - Three-tier verification explained ✅
8. **Screen Showcase** - Key UI screenshots ✅
9. **Implementation Timeline** - Deployment process ✅
10. **Support & Training** - Ongoing assistance ✅
11. **Case Study** - Pilot program results ✅
12. **Next Steps** - Call to action ✅

## 🎨 Style Customization

All styles are in `styles.css`. Key variables:

```css
:root {
  --primary: #2563eb;        /* Main brand color */
  --secondary: #059669;      /* Success/positive */
  --accent: #dc2626;         /* Alerts/warnings */

  --space-xl: 3rem;          /* Large spacing */
  --radius-xl: 1rem;         /* Rounded corners */
  --shadow-xl: ...;          /* Card elevation */
}
```

## 📸 Export to PDF/Images

### Using Browser Print
1. Open slide in Chrome/Firefox
2. File → Print
3. Destination: "Save as PDF"
4. Paper size: Custom (1920 x 1080 px)
5. Margins: None
6. Background graphics: On

### Using Screenshot Tools
```bash
# macOS
# Cmd+Shift+4 then Space to capture window

# Linux
gnome-screenshot --window

# Windows
# Win+Shift+S for snipping tool
```

### Using Puppeteer (Automated)
```javascript
// Script to export all slides to PDF
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });

  await page.goto('file:///path/to/slide-01-cover.html');
  await page.pdf({
    path: 'slide-01-cover.pdf',
    width: '1920px',
    height: '1080px',
    printBackground: true
  });

  await browser.close();
})();
```

## 🔧 Editing Tips

### Adding New Slides
1. Copy an existing slide HTML file
2. Update the content inside `.slide-content`
3. Adjust slide number in `.slide-footer`
4. Keep the same header/footer structure

### Changing Backgrounds
```html
<!-- Gradient blue (default) -->
<div class="slide bg-gradient-blue">

<!-- Gradient green -->
<div class="slide bg-gradient-green">

<!-- White -->
<div class="slide bg-white">

<!-- Dark -->
<div class="slide bg-dark">
```

### Using Grid Layouts
```html
<!-- 2 columns -->
<div class="grid grid-2">
  <div>Column 1</div>
  <div>Column 2</div>
</div>

<!-- 3 columns -->
<div class="grid grid-3">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</div>
```

### Adding Stats
```html
<div class="stat primary">
  <div class="stat-value">99%</div>
  <div class="stat-label">Accuracy</div>
</div>
```

## 📊 Presentation Statistics

- **Total Slides:** 12
- **Resolution:** 1920x1080 (Full HD)
- **Format:** HTML + CSS
- **File Size:** ~150 KB total
- **Dependencies:** None (self-contained)
- **Color Schemes:** 4 (gradient blue, gradient green, white, dark)
- **Key Metrics:** 60% time savings, 99%+ accuracy, $45K savings/year

## 🎯 Target Audience

- Facility managers and administrators
- Procurement officers
- Security directors
- Government officials
- Budget committees
- Non-technical stakeholders

## 🎬 Presentation Tips

1. **Opening**: Start with slide 1 (cover) - sets the tone
2. **Problem**: Slide 2 shows the pain points clearly
3. **Solution**: Slides 3-8 demonstrate how it works
4. **Value**: Slides 4, 9-11 focus on ROI and proof
5. **Close**: Slide 12 with clear next steps

---

**Generated:** January 30, 2026
**Status:** ✅ Complete - 12 slides ready to present
