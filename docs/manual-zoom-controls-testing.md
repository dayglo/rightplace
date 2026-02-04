# Manual Zoom Controls Testing Guide

## Implementation Summary

Added manual zoom +/- controls to the CirclePacking visualization component. The controls allow users to zoom in/out independently of clicking circles, providing finer control over the zoom level.

## Changes Made

### Files Modified
- `web-ui/src/lib/components/rollcall/CirclePacking.svelte`

### Key Changes
1. Added component-level state for zoom controls:
   - `root`: Hierarchy root reference for zoom limits
   - `handleManualZoomFn`: Function reference for manual zoom
   - `zoomFn`: Function reference for programmatic zoom
   - `canZoomIn`: Reactive variable for zoom-in button state
   - `canZoomOut_manual`: Reactive variable for zoom-out button state

2. Modified `renderCirclePacking()`:
   - Changed `root` from `const` to module-level variable
   - Added local `svg`, `node`, `label` references
   - Updated `zoomTo()` to check for reference existence
   - Added `handleManualZoom()` function for manual zoom
   - Exposed `handleManualZoom` and `zoom` to component template

3. Added UI controls:
   - Two buttons (+ and -) in bottom-right corner
   - Buttons disable when at zoom limits
   - Smooth 300ms transition on manual zoom

### Zoom Behavior
- **Zoom In (+)**: Decreases view diameter by 20% (zooms in 1.25x)
- **Zoom Out (-)**: Increases view diameter by 20% (zooms out 0.8x)
- **Limits**:
  - Min: `focus.r * 1.5` (can zoom in 1.73x closer than current node)
  - Max: `root.r * 2.6` (can't zoom out past root level)

## Manual Testing Checklist

### Prerequisites
1. Start the FastAPI server:
   ```bash
   cd server
   source .venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Start the web UI dev server:
   ```bash
   cd web-ui
   npm run dev
   ```

3. Navigate to the roll call visualization page: http://localhost:5176/rollcalls/visualization

### Test Cases

#### 1. Zoom Controls Visibility
- [ ] Manual zoom controls (+/-) appear in bottom-right corner
- [ ] Buttons are styled consistently with other UI controls
- [ ] Buttons don't obscure visualization content
- [ ] Controls are visible on all screen sizes

#### 2. Zoom In Functionality
- [ ] Click + button → zooms in smoothly by 20%
- [ ] Center point remains the same (view doesn't shift)
- [ ] Transition is smooth (300ms duration)
- [ ] Multiple clicks work smoothly without glitches
- [ ] Button disables when at minimum zoom limit
- [ ] Tooltip shows "Zoom In" on hover

#### 3. Zoom Out Functionality
- [ ] Click - button → zooms out smoothly by 20%
- [ ] Center point remains the same (view doesn't shift)
- [ ] Transition is smooth (300ms duration)
- [ ] Multiple clicks work smoothly without glitches
- [ ] Button disables when at maximum zoom limit
- [ ] Tooltip shows "Zoom Out" on hover

#### 4. Zoom Limits
- [ ] Can't zoom in beyond `focus.r * 1.5` (button disables)
- [ ] Can't zoom out beyond `root.r * 2.6` (button disables)
- [ ] Disabled buttons have reduced opacity (50%)
- [ ] Disabled buttons show not-allowed cursor
- [ ] Limits work correctly at all hierarchy levels

#### 5. Interaction with Existing Features
- [ ] Click circle → zooms to circle (existing behavior preserved)
- [ ] Click background → zooms out to parent (existing behavior preserved)
- [ ] "Zoom Out" button (top-left) still works
- [ ] Alt+click still triggers slow zoom (7500ms)
- [ ] Manual zoom + click circle work together
- [ ] Can manually zoom in, then click a different circle to focus it
- [ ] Can manually zoom out, then click a circle to focus it

#### 6. Hierarchy Level Testing
Test at each hierarchy level:
- [ ] **Prison level**: Manual zoom works correctly
- [ ] **Houseblock level**: Manual zoom works correctly
- [ ] **Wing level**: Manual zoom works correctly
- [ ] **Landing level**: Manual zoom works correctly
- [ ] **Cell level**: Manual zoom works correctly

#### 7. Multi-Prison Testing
Test with different prisons:
- [ ] HMP Berwyn (720 inmates)
- [ ] HMP Oakwood (1800 inmates)
- [ ] HMP Parc (1900 inmates)

#### 8. Label Visibility
- [ ] Labels remain visible and readable during manual zoom
- [ ] Labels don't flicker or disappear during transition
- [ ] Font sizes scale appropriately with zoom level

#### 9. Edge Cases
- [ ] Rapid clicking of +/- buttons doesn't break visualization
- [ ] Manual zoom works immediately after page load
- [ ] Manual zoom works after switching prisons
- [ ] Manual zoom works after clicking circles
- [ ] Can zoom in fully, then zoom out fully
- [ ] Can zoom out fully, then zoom in fully

#### 10. Browser Compatibility
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Edge

### Performance Testing
- [ ] No lag or stuttering during manual zoom
- [ ] Smooth transitions even with large datasets
- [ ] No memory leaks after repeated zoom operations
- [ ] No console errors or warnings

## Known Issues

### Pre-existing TypeScript Warnings
The following warnings existed before this implementation:
- Unused export properties `onNodeClick` and `onZoomOut`
- Implicit 'any' type for `this` in label truncation code
- Type mismatch between `TreemapNode` and `TreemapResponse`

These are unrelated to the manual zoom controls and should be addressed separately.

## Testing Results

### Date: [To be filled in during testing]
### Tested by: [To be filled in during testing]
### Environment: [Browser, OS, Screen size]

#### Results Summary
- [ ] All tests passed
- [ ] Some tests failed (document below)
- [ ] Needs additional testing

#### Failed Tests
[Document any failed tests here]

#### Additional Notes
[Any observations or recommendations]

## Success Criteria

✅ Implementation is complete when:
1. All checkboxes in the manual testing checklist are checked
2. No regressions in existing zoom behavior
3. Smooth transitions without visual glitches
4. Zoom limits enforced correctly
5. Works across all hierarchy levels and prisons
6. No console errors or warnings related to new code

## Future Enhancements

Potential improvements to consider:
1. **Mouse wheel zoom**: Zoom in/out with scroll wheel
2. **Keyboard shortcuts**: +/- keys to zoom, arrow keys to pan
3. **Pan/drag functionality**: Drag the viewport to move around
4. **Touch support**: Touch-based zoom gestures
5. **Reset view button**: Return to default view for current focus
6. **Zoom level indicator**: Show current zoom percentage
