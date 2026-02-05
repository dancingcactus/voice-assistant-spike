# Milestone 3: Untrigger Functionality - Testing Guide

## Quick Start

### Prerequisites
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:5175` (or check console for actual port)

### Step-by-Step Testing

## Test 1: Basic Untrigger Flow (5 minutes)

### 1. Open the Dashboard
- Navigate to: **http://localhost:5175**
- You should see the main dashboard

### 2. Open Story Beat Tool
- Click on **"Story Beat Tool"** in the navigation
- Select user: **user_justin** (or any existing user)
- You'll see the chapter and beat list

### 3. Trigger a Beat
- Find a beat that's marked as **"ready"** (green badge)
- Click on the beat to open the detail modal
- Click **"Trigger"** button for any variant
- The beat should now show as **"delivered"** (blue badge)

### 4. Trigger a Dependent Beat
- Find **"first_timer"** beat (depends on "awakening_confusion")
- Trigger it as well
- Now you have 2 delivered beats with a dependency relationship

### 5. Test Untrigger with Dry-Run Preview
- Click on **"awakening_confusion"** beat (the one that first_timer depends on)
- In the detail modal, scroll down to the **"Delivery Status"** section
- Click the **"Untrigger Beat"** button (red button)
- **A modal will appear showing:**
  - Explanation of what will happen
  - List of dependent beats that will also be untriggered
  - In this case, you should see "first_timer" in the dependencies list

### 6. Confirm Untrigger
- Click the **"Untrigger"** button in the modal (red button)
- The modal will close
- Both beats should now be reset to "ready" or "locked" status
- The chapter diagram will update to reflect the change

### 7. Verify Re-trigger Works
- Click on **"awakening_confusion"** again
- Trigger it again
- It should work, proving the beat can be re-triggered after untrigger

---

## Test 2: Untrigger Without Dependencies (3 minutes)

### 1. Trigger a Standalone Beat
- Find a beat that doesn't have any other beats depending on it
- For example, look for an optional beat
- Trigger it

### 2. Untrigger It
- Click on the beat
- Click **"Untrigger Beat"**
- The modal should show:
  - Explanation that only this beat will be removed
  - **No dependent beats listed** (empty list)

### 3. Confirm
- Click **"Untrigger"**
- Only that beat should be reset

---

## Test 3: Untrigger Already Untriggered Beat (2 minutes)

### 1. Try to Untrigger a Non-Delivered Beat
- Click on a beat that hasn't been delivered yet
- The **"Untrigger Beat"** button should **NOT appear**
- Only delivered beats show the untrigger button

---

## Test 4: Progression Beat Stage Untrigger (Advanced - 5 minutes)

### 1. Find a Progression Beat
- Look for beats with type **"progression"**
- Example: "self_awareness" or "recipe_help"

### 2. Trigger Multiple Stages
- Trigger stage 1
- Then trigger stage 2
- Then trigger stage 3 (if available)

### 3. Untrigger a Specific Stage
- Click on the progression beat
- In the detail modal, you'll see all delivered stages
- Click **"Untrigger Beat"**
- The modal should explain that untriggering will roll back the current stage and all later stages

### 4. Confirm and Verify
- After untrigger, check that only earlier stages remain
- The beat should still show as partially delivered

---

## Visual Indicators to Look For

### Beat Status Badges
- 🔵 **delivered** - Beat has been triggered
- 🟢 **ready** - Beat can be triggered now
- ⚫ **locked** - Prerequisites not met
- 🟡 **auto-advance** - Special auto-advance beat

### Untrigger Button
- Located in the **"Delivery Status"** section
- Only appears on **delivered beats**
- Red background color (indicates destructive action)
- Text: "Untrigger Beat"

### Untrigger Modal
- **Title**: "Untrigger '[beat name]'?"
- **Explanation section**: Yellow background with warning icon
- **Dependencies section**: Red background (if dependencies exist)
- **Buttons**:
  - Gray "Cancel" button
  - Red "Untrigger" button

---

## Common Issues and Solutions

### Issue: "Untrigger Beat" button doesn't appear
- **Solution**: Make sure the beat is actually delivered (blue badge)
- Check that you're looking at the beat detail modal, not just the beat card

### Issue: Modal shows "Beat has not been delivered yet"
- **Solution**: This is expected behavior - trigger the beat first

### Issue: Changes don't reflect immediately
- **Solution**: Click the refresh button (🔄) in the top right of the Story Beat Tool
- Or wait 3 seconds - the UI auto-refreshes every 3 seconds

### Issue: Untrigger succeeds but beat still shows as delivered
- **Solution**: Check browser console for errors
- Verify backend is running and check backend logs
- Try refreshing the page

---

## Backend API Testing (Optional)

If you want to test the API directly:

```bash
# Dry-run untrigger (preview only)
curl -X POST 'http://localhost:8000/api/v1/story/users/user_justin/beats/awakening_confusion/untrigger?dry_run=true' \
  -H 'Authorization: Bearer dev_token_12345' | python3 -m json.tool

# Actual untrigger
curl -X POST 'http://localhost:8000/api/v1/story/users/user_justin/beats/awakening_confusion/untrigger?dry_run=false' \
  -H 'Authorization: Bearer dev_token_12345' | python3 -m json.tool
```

---

## Success Criteria Checklist

- ✅ Untrigger button appears on delivered beats
- ✅ Modal shows dry-run preview before confirming
- ✅ Dependencies are clearly listed
- ✅ Untrigger operation removes beat from user progress
- ✅ Dependent beats are also removed
- ✅ Beat can be re-triggered after untrigger
- ✅ UI updates reflect changes immediately
- ✅ Chapter diagram updates to show new state

---

## Quick Access URLs

- **Dashboard**: http://localhost:5175
- **Story Beat Tool**: http://localhost:5175/#story-beat-tool (after opening dashboard)
- **Backend API Docs**: http://localhost:8000/docs
- **Untrigger Endpoint**: `POST /api/v1/story/users/{user_id}/beats/{beat_id}/untrigger`

---

## Testing Time Estimate

- **Quick smoke test**: 5-10 minutes
- **Full test suite**: 15-20 minutes
- **Exploratory testing**: 30+ minutes

Enjoy testing the untrigger functionality! 🎉
