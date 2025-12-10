# ChatKit Test Guide - Verify Pure Vanilla Implementation

**Last Updated**: 2025-12-09
**Status**: Ready for Testing

---

## ✅ Pre-Test Checklist

Before testing, ensure:

- [ ] Backend server running: `python -m uvicorn app.main:app --reload` (port 8000)
- [ ] Frontend dev server running: `npm run dev` (port 3000)
- [ ] PostgreSQL database running
- [ ] `.env.local` configured with: `NEXT_PUBLIC_AGENT_API_URL=http://localhost:8000/agent`

---

## 🧪 Test Procedure

### Step 1: Open Application
1. Navigate to: `http://localhost:3000`
2. Look for **blue chat button** (💬) in **top-right corner**
3. Button should NOT be hidden behind other elements

**Expected**: Blue circular button with chat icon visible

---

### Step 2: Verify Browser Console
1. Open Browser DevTools: **F12** or **Right-click → Inspect**
2. Go to **Console** tab
3. Look for initialization messages:

```
✓ ChatKit session created: session-[timestamp]-[uuid]...
Configuring ChatKit web component...
✓ ChatKit web component initialized successfully
```

**Expected**: All three messages should appear

---

### Step 3: Click Chat Button
1. Click the **blue chat button** (💬)
2. Button should change to **red** with **close icon** (✕)
3. ChatKit widget should appear at **bottom-right** of screen

**Expected**:
- Button color changes: Blue → Red
- Button icon changes: 💬 → ✕
- ChatKit UI appears with:
  - Header: "AI Assistant"
  - Greeting: "Hello! I can help you manage inventory..."
  - Three prompt buttons:
    - "Add item"
    - "Create bill"
    - "Check inventory"
  - Input field with placeholder: "Type your message..."

---

### Step 4: Test Message Input
1. Click in the message input field
2. Type: `Test message`
3. Press **Enter** or click send button

**Expected**:
- Message appears in chat history
- Console shows: `📨 User message sent: Test message`
- Agent responds with a message (or error if backend not configured)

---

### Step 5: Verify Session Persistence
1. Open **DevTools → Application → Session Storage**
2. Look for key: `chatkit-session-id`
3. Value should be: `session-[timestamp]-[uuid]...`

**Expected**: Session ID is stored and persists across navigation

---

### Step 6: Test Close Button
1. Click the **red close button** (✕)
2. ChatKit should disappear
3. Button should change back to **blue** with **chat icon**

**Expected**:
- Button color changes: Red → Blue
- Button icon changes: ✕ → 💬
- ChatKit widget hidden

---

### Step 7: Navigation Persistence
1. With chat button open, navigate to another route:
   - `/admin`
   - `/pos`
   - `/inventory`
2. Chat button state should persist (still open)
3. ChatKit session should persist

**Expected**: ChatKit remains open and ready across route changes

---

## 🐛 Troubleshooting

### Issue: Chat Button Doesn't Appear
**Solution**:
1. Check console for errors (F12)
2. Verify layout.tsx was updated
3. Hard refresh browser: `Ctrl+Shift+R` (Cmd+Shift+R on Mac)

### Issue: ChatKit UI is Empty
**Solution**:
1. Check console for initialization messages
2. Look for error: "ChatKit web component not found"
3. Verify @openai/chatkit is loaded from CDN
4. Check Network tab (F12) for `@openai/chatkit` CDN request

### Issue: Messages Don't Send
**Solution**:
1. Check backend is running on port 8000
2. Verify session creation in console
3. Check Network tab for POST to `/agent/chat`
4. Look for CORS errors

### Issue: Session Not Persisting
**Solution**:
1. Verify sessionStorage (DevTools → Application)
2. Check if cookies/storage are allowed in browser
3. Ensure `.env.local` has correct API URL

---

## 🔍 Console Log Reference

**Successful Initialization**:
```
✓ ChatKit session created: session-1733850000000-abc123def456...
Configuring ChatKit web component...
✓ ChatKit web component initialized successfully
```

**User Interaction**:
```
📨 User message sent: Test message
🤖 Agent is responding...
✓ Agent response complete
```

**Errors to Watch For**:
```
❌ ChatKit error: [error detail]
❌ Failed to initialize ChatKit: [error detail]
✗ Session creation failed: [error detail]
```

---

## 📊 Expected Network Requests

When testing, you should see these requests in Network tab (F12):

1. **ChatKit Web Component**
   - URL: `https://cdn.jsdelivr.net/npm/@openai/chatkit@latest/dist/index.js`
   - Method: GET
   - Status: 200

2. **Create Session**
   - URL: `http://localhost:8000/agent/session`
   - Method: POST
   - Status: 200
   - Response: `{ session_id: "session-...", created_at: "2025-12-09T..." }`

3. **Send Message**
   - URL: `http://localhost:8000/agent/chat`
   - Method: POST
   - Status: 200
   - Response: `{ session_id: "...", message: "...", type: "text", ... }`

---

## ✅ Success Criteria

All of these should be TRUE:

- [ ] Blue chat button visible in top-right corner
- [ ] Console shows initialization messages (3 success messages)
- [ ] Click button → ChatKit UI appears with full interface
- [ ] ChatKit shows greeting, prompts, and input field
- [ ] Can type and send messages
- [ ] Session ID visible in sessionStorage
- [ ] Click close button → ChatKit hides
- [ ] Button state and ChatKit persist across route navigation
- [ ] No console errors

---

## 📝 Report Template

If issues occur, please provide:

1. **Console Output** (F12 → Console)
   - Paste all messages shown

2. **Network Tab** (F12 → Network)
   - Screenshot of requests to `/agent/session` and `/agent/chat`

3. **Error Message**
   - Full error text from console or alert

4. **Steps to Reproduce**
   - What you did when the issue occurred

---

## 🚀 Next Steps After Successful Test

Once ChatKit is working:

1. **Test with Real Messages**
   - Try: "Add 10kg sugar at 160 per kg under grocery"
   - Verify agent understands the request

2. **Monitor Database**
   - Check conversation_history table:
     ```sql
     SELECT * FROM conversation_history ORDER BY created_at DESC LIMIT 10;
     ```

3. **Phase 3 Implementation**
   - Proceed with inventory add functionality
   - Implement natural language parsing
   - Test MCP tool integration

---

## 📞 Quick Debugging Commands

**Check Backend Health**:
```bash
curl http://localhost:8000/health
```

**Check Session Creation**:
```bash
curl -X POST http://localhost:8000/agent/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": null}'
```

**View Conversation History**:
```bash
psql -U [user] -d [database] -c \
  "SELECT session_id, user_message, agent_response, created_at FROM conversation_history ORDER BY created_at DESC LIMIT 5;"
```

---

**Status**: ✅ Ready for testing
**Expected Duration**: 5-10 minutes
**Success Rate**: Should be 100% if all prerequisites met
