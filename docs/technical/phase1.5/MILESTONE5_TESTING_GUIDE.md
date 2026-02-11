# Milestone 5: Tool Calls Inspection - Testing Guide

## Quick Start

### 1. Ensure Backend is Running

The backend API should already be running on port 8000. You can verify:

```bash
curl http://localhost:8000/health
```

### 2. Ensure Frontend is Running

The frontend should be running on port 5173. Open your browser to:

```
http://localhost:5173/observability
```

### 3. Navigate to Tool Calls

Click the **"Tool Calls"** button in the navigation bar at the top.

---

## What to Test

### Timeline View

1. **View All Tool Calls**
   - Should see a list of 50 sample tool calls
   - Each entry shows: tool name, character, duration, timestamp
   - Status indicators: ✅ success, ❌ error, ⏱️ timeout

2. **Apply Filters**
   - **Tool Filter**: Select a specific tool (e.g., "get_recipe")
   - **Character Filter**: Select a character (e.g., "Delilah")
   - **Status Filter**: Filter by success/error/timeout
   - **Combine Filters**: Try multiple filters together
   - **Clear Filters**: Click "Clear Filters" to reset

3. **Click for Details**
   - Click any tool call in the timeline
   - Modal should open showing:
     - Complete request parameters
     - Complete response data
     - Timing information
     - Character reasoning (if available)
   - Try the "Copy Request" and "Copy Response" buttons
   - Close modal by clicking X or clicking outside

4. **Performance Indicators**
   - Fast calls (< 1s): Green duration
   - Medium calls (1-2s): Orange duration
   - Slow calls (> 2s): Red duration

### Statistics View

1. **Click "Statistics" Tab**
   - Should see aggregate metrics at the top:
     - Total calls
     - Successes
     - Errors
     - Success rate
     - Average duration

2. **By Tool Statistics**
   - Table showing all tools with their metrics
   - Success rates should be color-coded
   - Check that numbers match the timeline data

3. **By Character Statistics**
   - Table showing character usage
   - Most used tool per character
   - Average duration per character

4. **Slowest Calls Section**
   - Shows 5 slowest tool calls
   - Click any to see details

5. **Recent Errors Section**
   - Shows recent failed calls
   - Click any to see error details

---

## Sample Data Overview

The test data includes:

- **50 total tool calls** across 7 days
- **5 unique tools**:
  - `set_timer` (8 calls, 100% success)
  - `get_recipe` (5 calls, 60% success)
  - `light_control` (16 calls, 93.75% success)
  - `get_calendar_events` (13 calls, 100% success)
  - `unit_conversion` (8 calls, 100% success)

- **3 characters**:
  - Delilah (18 calls, prefers unit_conversion)
  - Hank (15 calls, prefers light_control)
  - Rex (17 calls, prefers get_calendar_events)

---

## Expected Behavior

### Filtering

- Filters should apply instantly
- Multiple filters work together (AND logic)
- Clear filters button resets all filters
- "Refresh" button refetches data

### Detail Modal

- Opens on click
- Shows full JSON request/response
- Copy buttons work
- Closes on X or outside click
- Can't scroll page while modal is open

### Statistics

- Numbers should be accurate
- Tables should be sortable by clicking headers
- Success rates color-coded:
  - Green: ≥ 95%
  - Orange: 80-94%
  - Red: < 80%

### Performance

- Timeline should load quickly (< 500ms)
- Filtering should be instant (client-side)
- Statistics calculation should be fast (< 200ms)
- No lag when scrolling the timeline

---

## Known Limitations

1. **Manual Refresh**: No real-time updates, must click "Refresh" to see new data
2. **No Replay**: Replay functionality not implemented in this milestone
3. **Time Range**: No date picker (shows all-time data)
4. **Export**: No CSV/JSON export yet

---

## Troubleshooting

### "Connection Error" on page load

- **Check backend**: `curl http://localhost:8000/health`
- **Check frontend**: Browser console for errors
- **Verify .env**: `/frontend/.env` should have `VITE_API_BASE_URL=http://localhost:8000` (no `/api/v1`)

### Empty timeline

- **Generate sample data**: `cd backend && python scripts/generate_sample_tool_calls.py`
- **Verify data file**: Check `/backend/data/tool_logs/user_justin_tool_calls.jsonl` exists

### Filters not working

- **Check console**: Look for JavaScript errors
- **Try refresh**: Click the "Refresh" button
- **Clear cache**: Hard refresh with Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### Statistics showing 0

- **Verify data**: Run test script `./tests/scripts/test_milestone5_tool_calls.sh`
- **Check API**: `curl -H "Authorization: Bearer dev_token_12345" "http://localhost:8000/tool-calls/stats?user_id=user_justin"`

---

## API Testing Commands

### List Tool Calls

```bash
curl -H "Authorization: Bearer dev_token_12345" \
  "http://localhost:8000/tool-calls?user_id=user_justin&limit=5"
```

### Get Statistics

```bash
curl -H "Authorization: Bearer dev_token_12345" \
  "http://localhost:8000/tool-calls/stats?user_id=user_justin"
```

### Filter by Tool

```bash
curl -H "Authorization: Bearer dev_token_12345" \
  "http://localhost:8000/tool-calls?user_id=user_justin&tool_name=get_recipe"
```

### Filter by Character

```bash
curl -H "Authorization: Bearer dev_token_12345" \
  "http://localhost:8000/tool-calls?user_id=user_justin&character=Delilah"
```

### Get Available Tools

```bash
curl -H "Authorization: Bearer dev_token_12345" \
  "http://localhost:8000/tool-calls/metadata/tools?user_id=user_justin"
```

---

## Success Criteria

✅ All backend API tests pass (`./tests/scripts/test_milestone5_tool_calls.sh`)
✅ Timeline view shows all tool calls
✅ Filters work individually and combined
✅ Detail modal opens and shows complete data
✅ Statistics are accurate and color-coded
✅ Copy buttons work for request/response
✅ UI is responsive and performs well
✅ No console errors

---

## Next Steps After Testing

Once you've verified everything works:

1. **Take screenshots** of the Timeline and Statistics views
2. **Test with different users** (if you have other test users)
3. **Try generating more data** with the sample data generator
4. **Move to Milestone 6**: Character Tool inspection

---

## Feedback Welcome

If you find any issues or have suggestions for improvements:

- UI/UX feedback
- Performance issues
- Missing features
- Bugs or errors

Let me know and I can address them!

---

*Milestone 5 Complete - Happy Testing! 🎉*
