# ✅ ChatKit Install & Test - DO THIS NOW

**Status**: Package installed ✓ | Code fixed ✓ | Ready to test

---

## 🚀 Steps to Test (Follow Exactly)

### Step 1: Stop the dev server
```bash
# In your terminal where npm run dev is running
Press: Ctrl+C
```

### Step 2: Run npm install (already done, but verify)
```bash
cd frontend
npm install
```

### Step 3: Restart dev server
```bash
npm run dev
```

**Wait for**: `ready - started server on 0.0.0.0:3000, url: http://localhost:3000`

### Step 4: Open browser
```
http://localhost:3000
```

### Step 5: Hard refresh
```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

### Step 6: Open Console
```
F12 or Right-click → Inspect → Console tab
```

### Step 7: Look for these messages
You should see:
```
✓ ChatKit element found
✓ New ChatKit session created: session-...
Configuring ChatKit...
✓ ChatKit configured successfully
```

✅ **If you see all 4 messages, ChatKit is working!**

### Step 8: Click chat button
- Look for **blue button** (💬) in **top-right corner**
- Click it
- ChatKit should appear at **bottom-right**

### Step 9: Test message
1. Type: `Hello`
2. Press Enter
3. Message should appear in chat

✅ **If message appears, ChatKit is fully working!**

---

## 🐛 If You See Errors

### Error: "Module not found: @openai/chatkit"
```bash
# Run this:
npm install @openai/chatkit --save
npm run dev
```

### Error: "ChatKit element not found"
1. Check console (F12)
2. Make sure you hard-refreshed (Ctrl+Shift+R)
3. Wait 2-3 seconds after page loads

### Error: "Session creation failed"
1. Verify backend is running: `python -m uvicorn app.main:app --reload`
2. Check `.env.local` has: `NEXT_PUBLIC_AGENT_API_URL=http://localhost:8000/agent`
3. Check Network tab (F12) for `/agent/session` request

### Error: "Can't send messages"
1. Verify backend is running
2. Check `/agent/chat` endpoint exists in backend
3. Look for errors in backend terminal

---

## ✅ Success Checklist

- [ ] npm install completed
- [ ] dev server running (port 3000)
- [ ] Browser shows page
- [ ] Blue chat button visible (top-right)
- [ ] Console shows 4 success messages
- [ ] Clicking button shows ChatKit UI
- [ ] ChatKit has:
  - [ ] Header: "AI Assistant"
  - [ ] Greeting message
  - [ ] Three prompt buttons
  - [ ] Input field
- [ ] Can type and send messages
- [ ] Messages appear in chat

---

## 🎯 What Should Happen

### Page Loads
```
✓ Page displays normally
✓ Blue chat button visible in top-right
✓ Console shows success messages (F12)
```

### Click Chat Button
```
✓ Button turns red with X
✓ ChatKit appears at bottom-right
✓ ChatKit shows greeting and prompts
✓ Input field is ready
```

### Send Message
```
✓ Type message
✓ Press Enter
✓ Message appears in chat
✓ Agent responds (or connection error if backend not ready)
```

---

## 📝 Commands Reference

**Install packages**:
```bash
cd frontend
npm install
```

**Start dev server**:
```bash
npm run dev
```

**Check backend**:
```bash
curl http://localhost:8000/health
```

**View session storage**:
```
F12 → Application → Session Storage → look for: ims-chatkit-session-id
```

---

## 🆘 Still Not Working?

Provide this info:

1. **Terminal output** when running `npm run dev`
   - Copy any red errors

2. **Console output** (F12)
   - Copy any red error messages

3. **Network requests** (F12 → Network)
   - Screenshot of failed requests
   - Look for red X marks

4. **Backend status**
   - Is it running? (you should see logs)
   - What port? (should be 8000)
   - Any errors in backend terminal?

---

## 🎉 Expected Result

When everything works:

1. **Page loads** with blue chat button
2. **Click button** → ChatKit UI appears
3. **Type message** → appears in chat
4. **Agent responds** → message appears
5. **Session persists** → works across page navigation

---

## 🚀 Next After Success

Once ChatKit is working:

1. ✅ Phase 2 is complete
2. ✅ Ready for Phase 3 (inventory add)
3. ✅ Test with real messages like: "Add 10kg sugar at 160 per kg"

---

**That's it! Follow the steps above and report back!** 💬
