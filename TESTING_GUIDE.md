# NIWI Dashboard UI Testing Guide

## Quick Start
1. **Development Server:** http://localhost:5173/
2. **Login:** Use your admin credentials
3. **Test:** Follow the checklist below

---

## Visual Inspection Checklist

### 1. Overview Dashboard (`/admin/dashboard`)

**Statistics Cards (Top Section)**
- [ ] 4 cards displayed in a row
- [ ] Large bold numbers (40px font size)
- [ ] Even spacing between cards (16px gaps)
- [ ] Icons visible in top-right corners
- [ ] "Action Needed" badge visible on Pending Review
- [ ] Hover effect: cards lift slightly

**Weekly Comparison**
- [ ] 4 metrics in a row
- [ ] Clear labels and values
- [ ] Background color distinct from main cards
- [ ] Values properly centered

**Pending Actions (Left Column)**
- [ ] Clean list of pending submissions
- [ ] "Review →" buttons on each row
- [ ] Hover highlights row background
- [ ] Count badge visible if items exist

**Recent Submissions (Right Column)**
- [ ] Avatar circles with initials
- [ ] Organization names visible
- [ ] Status badges (Pending/Sent) clear
- [ ] Score displayed for each entry
- [ ] "See all →" link at top

### 2. Submissions List (`/admin/submissions`)

**Filter Bar**
- [ ] Search box prominent with icon
- [ ] Date range inputs (From/To) functional
- [ ] "Clear" button visible
- [ ] "Download CSV" button with counter
- [ ] All controls properly aligned

**Table**
- [ ] Headers bold and uppercase
- [ ] Adequate spacing between rows (~50px height)
- [ ] Hover highlights entire row
- [ ] Download button (⬇) in last column
- [ ] Email column not too wide
- [ ] ID column subtle (gray text)

**Responsive Behavior**
- [ ] Filter controls stack on narrow screens
- [ ] Table scrolls horizontally if needed
- [ ] No content cut off

### 3. Analytics (`/admin/analytics`)

**Charts Section**
- [ ] Radar chart centered and clear
- [ ] Donut chart with legend below
- [ ] Bar chart readable labels
- [ ] Trend line chart showing data
- [ ] All charts have titles and subtitles

**Rankings Lists**
- [ ] Top performers on left
- [ ] Needs support on right
- [ ] Numbered badges visible
- [ ] Progress bars displaying
- [ ] Scores aligned right

### 4. Submission Detail (`/admin/submissions/:id`)

**Respondent Info**
- [ ] 2-column grid of info boxes
- [ ] Each box has border and padding
- [ ] Labels uppercase and small
- [ ] Values clear and readable
- [ ] Status badge prominent

**Score Breakdown**
- [ ] Score table formatted correctly
- [ ] Overall row highlighted

**Dimension Cards**
- [ ] 2-column grid
- [ ] Each dimension in bordered box
- [ ] Score and commentary visible
- [ ] Color coding based on score
- [ ] Adequate padding (~18-20px)

**Email Editor**
- [ ] Large text area (420px min height)
- [ ] Text readable (14px+)
- [ ] Action buttons at bottom
- [ ] Save/Send buttons clear
- [ ] "Sent" confirmation if already sent

---

## Responsive Testing

### Desktop (1400px+)
Open browser DevTools → Toggle device toolbar → Select "Responsive"

**Set to 1440px width:**
- [ ] Full 4-column stat grid
- [ ] Content uses most of screen width
- [ ] No excessive white space on sides
- [ ] Sidebar visible and hoverable
- [ ] All text readable

### Tablet (768px)
**Set to 768px width:**
- [ ] Stats change to 2 columns
- [ ] Pending/Recent stack vertically
- [ ] Weekly comparison becomes 2x2 grid
- [ ] Filter bar remains usable
- [ ] Navigation accessible

### Mobile (375px)
**Set to 375px width (iPhone SE):**
- [ ] Stats display 2 per row
- [ ] All sections stack vertically
- [ ] Sidebar becomes horizontal bar
- [ ] Filter controls full width
- [ ] Buttons easy to tap (44px+)
- [ ] No horizontal scrolling
- [ ] Text remains legible

---

## Functional Testing

### Navigation
- [ ] Click all sidebar items
- [ ] Each page loads correctly
- [ ] Back button works on detail pages
- [ ] Breadcrumbs functional (if present)
- [ ] URL updates properly

### Data Display
- [ ] Statistics show real numbers
- [ ] Tables populate with data
- [ ] Charts render correctly
- [ ] Filters update table
- [ ] Search finds submissions
- [ ] Date range filters work

### Interactions
- [ ] Refresh button works
- [ ] Click on table row → goes to detail
- [ ] Download CSV generates file
- [ ] Email editor saves changes
- [ ] Send email button functional
- [ ] Modal dialogs appear centered
- [ ] Profile menu opens/closes

### Forms & Inputs
- [ ] Search box accepts text
- [ ] Date pickers open calendar
- [ ] Buttons show hover states
- [ ] Disabled buttons appear gray
- [ ] Loading states visible

---

## Browser Testing

### Chrome/Edge (Chromium)
- [ ] Layout correct
- [ ] Fonts load properly
- [ ] Hover effects smooth
- [ ] No console errors

### Firefox
- [ ] Same as Chrome
- [ ] Grid layouts work
- [ ] Flexbox behaves correctly

### Safari (Mac/iOS)
- [ ] Border-radius displays
- [ ] Grid gaps correct
- [ ] Backdrop-filter works
- [ ] Touch targets adequate

---

## Common Issues to Check

### Layout Problems
- [ ] No overlapping text
- [ ] No cut-off content
- [ ] No unexpected scrollbars
- [ ] Cards aligned properly
- [ ] Gaps consistent

### Typography Issues
- [ ] All fonts loading
- [ ] Line heights readable
- [ ] No text overflow
- [ ] Weights correct (600, 700, 800)

### Color & Contrast
- [ ] Text readable on backgrounds
- [ ] Badges clear
- [ ] Links distinguishable
- [ ] Disabled states obvious

### Spacing Problems
- [ ] No elements touching edges
- [ ] Consistent padding in cards
- [ ] Even gaps in grids
- [ ] Adequate white space

---

## Performance Check

### Load Time
- [ ] Page loads < 2 seconds
- [ ] Images load quickly
- [ ] No layout shift

### Animations
- [ ] Hover effects smooth (60fps)
- [ ] Transitions don't lag
- [ ] No jank when scrolling

### Memory
- [ ] No memory leaks
- [ ] Charts don't slow down
- [ ] Can navigate freely

---

## Accessibility Quick Check

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Focus indicators visible
- [ ] Can activate buttons with Enter/Space
- [ ] Can close modals with Esc

### Screen Reader (Optional)
- [ ] Headings announced correctly
- [ ] Buttons have labels
- [ ] Form fields have labels
- [ ] Status messages announced

### Color Blind (Optional)
- [ ] Not relying solely on color
- [ ] Badges have text
- [ ] Charts have labels
- [ ] Status indicated with icons

---

## Sign-Off Checklist

Before marking as complete:

**Visual Design**
- [ ] Looks modern and professional
- [ ] Spacing feels balanced
- [ ] Typography hierarchy clear
- [ ] Colors on-brand

**Functionality**
- [ ] All features working
- [ ] No console errors
- [ ] Data displays correctly
- [ ] Forms submit properly

**Responsiveness**
- [ ] Desktop layout optimal
- [ ] Tablet usable
- [ ] Mobile functional
- [ ] No overflow issues

**Performance**
- [ ] Loads quickly
- [ ] Animations smooth
- [ ] No lag when interacting

**Cross-browser**
- [ ] Tested in 2+ browsers
- [ ] Layout consistent
- [ ] All features work

---

## Reporting Issues

If you find problems:

**Include:**
1. Browser & version
2. Screen size
3. Steps to reproduce
4. Screenshot if visual
5. Console errors if any

**Priority Levels:**
- **Critical:** App broken, can't use
- **High:** Major feature not working
- **Medium:** Visual issue or minor bug
- **Low:** Polish/enhancement

---

## Next Steps

After testing:
1. ✅ Confirm all items pass
2. 📝 Note any issues found
3. 🚀 Deploy to staging
4. 👥 User acceptance testing
5. 🎉 Production deployment

---

**Happy Testing! 🎨**
