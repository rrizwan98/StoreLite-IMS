# IMS - Intelligent Inventory Management System

> Your personal AI-powered inventory assistant that automates your business operations, saving you hours of manual work every day.

## What is IMS?

IMS is a **complete inventory and billing solution** powered by artificial intelligence. Instead of manually entering data, generating reports, and managing stock — simply tell the AI what you need in plain language.

**No coding required. No complex setup. Just connect and start talking.**

---

## Why IMS? The Problem We Solve

| Traditional Inventory Systems | IMS with AI |
|------------------------------|-------------|
| Manual data entry for every item | "Add 50 kg rice at Rs. 120/kg" — done |
| Complex report generation | "Show me last week's sales" — instant |
| Switching between multiple screens | One chat interface for everything |
| Learning curve for new staff | Natural language — anyone can use it |
| Separate tools for billing, analytics, emails | All integrated in one AI assistant |
| Hours spent on repetitive tasks | Automated scheduling handles it |

---

## Time Savings: Real Numbers

Based on typical business operations:

| Task | Manual Time | With IMS AI | You Save |
|------|-------------|-------------|----------|
| Add 20 inventory items | 30 minutes | 5 minutes | **25 minutes** |
| Generate daily sales report | 15 minutes | 30 seconds | **14.5 minutes** |
| Send low-stock alerts | 20 minutes | Automated | **20 minutes** |
| Create & send invoice | 10 minutes | 2 minutes | **8 minutes** |
| Monthly analytics review | 2 hours | 10 minutes | **1 hour 50 minutes** |

> **Estimated daily time saved: 2-4 hours**

---

## Core Features at a Glance

### 1. AI Agent — Your Personal Business Assistant
Talk to your inventory system like talking to a person. The AI understands context, remembers your preferences, and executes complex tasks.

**Example Conversations:**
```
You: "Add 100 pieces of Samsung Galaxy cases at Rs. 450 each"
AI: ✓ Added Samsung Galaxy cases - 100 pcs @ Rs. 450

You: "How many cases do I have left?"
AI: You have 100 Samsung Galaxy cases in stock worth Rs. 45,000

You: "Create a bill for 5 cases for customer Ahmed"
AI: ✓ Bill created: Rs. 2,250 (5 × Rs. 450) - Invoice #INV-2025-0042
```

[📖 Full AI Agent Documentation →](./ai-agent.md)

---

### 2. Smart Dashboard — Everything at a Glance
A customizable dashboard showing your business health:
- **Real-time KPIs**: Total items, active stock value, revenue, orders
- **Visual Analytics**: Charts, graphs, and trend indicators
- **Inventory Alerts**: Low stock warnings before you run out
- **Recent Activity**: Track what's happening in your business

---

### 3. Automated Scheduler — Set It and Forget It
Schedule tasks to run automatically:
- Daily inventory reports at 9 AM
- Weekly low-stock alerts every Monday
- Monthly sales summary on the 1st
- Automatic email notifications

**Example:**
```
"Every Monday at 8 AM, send me a report of items below 10 units stock"
```

[📖 Full Scheduler Documentation →](./scheduler.md)

---

### 4. Tools & Connectors — Extend Your AI
Connect external services to superpower your assistant:
- **Gmail**: Send invoices and reports via email
- **Google Drive**: Backup and store documents
- **Notion**: Sync inventory data
- **Custom MCP Servers**: Add any tool you need

[📖 Full Tools & Connectors Documentation →](./tools-connectors.md)

---

### 5. Developer API — Build Your Own Solutions
For developers who want to integrate IMS into their applications:
- RESTful API with full documentation
- Publish AI agents for external users
- Embed chat widgets on your website
- Rate limiting and access control

[📖 Full Developer Documentation →](./developer.md)

---

## Three Ways to Use IMS

IMS adapts to your needs with three connection modes:

### Option 1: Quick Start (Our Database)
**Best for**: Small businesses, trying out IMS
- No setup required
- Start immediately
- Full inventory + billing features
- AI assistant included

### Option 2: Bring Your Own Database
**Best for**: Existing businesses with data
- Connect your PostgreSQL database
- Full control over your data
- Complete IMS features
- Custom schema support

### Option 3: Schema Query Only
**Best for**: Analytics and reporting
- Read-only access to your database
- AI-powered SQL generation
- Advanced analytics
- No modifications to your data

---

## Quick Start Guide

### Step 1: Create Your Account
Sign up at the login page with email and password.

### Step 2: Choose Your Connection Type
On the dashboard, select how you want to use IMS:
- **Use Our Database**: Start immediately
- **Connect Your Database**: Provide PostgreSQL URI
- **Schema Query Only**: For analytics

### Step 3: Start Talking to Your AI
Open the chat interface and try:
```
"Show me my inventory overview"
"Add a new item: Blue T-Shirt, 50 pieces, Rs. 350 each"
"What's my best selling item this month?"
```

### Step 4: Connect Your Tools (Optional)
Go to Settings → Connectors to add:
- Gmail for email
- Google Drive for storage
- Custom MCP servers

### Step 5: Schedule Automation (Optional)
Set up automated tasks:
```
"Schedule daily inventory report at 9 AM"
```

---

## Security & Privacy

Your data security is our priority:

- **User Isolation**: Your data is completely separate from other users
- **Encrypted Storage**: Sensitive credentials encrypted at rest
- **JWT Authentication**: Secure token-based authentication
- **No Data Sharing**: Your inventory data stays yours
- **Read-Only Option**: Schema Query mode never modifies your data

---

## Support

Need help? We're here for you:

1. **In-App Help**: Click the "?" button on any page
2. **Documentation**: You're reading it!
3. **Support Tickets**: Submit issues through the app
4. **GitHub Issues**: Report bugs at our repository

---

## Documentation Navigation

| Document | Description |
|----------|-------------|
| [AI Agent Guide](./ai-agent.md) | Complete guide to using the AI assistant |
| [Developer Documentation](./developer.md) | API reference and integration guide |
| [Scheduler Guide](./scheduler.md) | Automation and task scheduling |
| [Tools & Connectors](./tools-connectors.md) | External integrations and extensions |

---

## What Makes IMS Different?

### No Need for Personal AI Agents
Many businesses think they need to build custom AI solutions. With IMS:
- AI is built-in and ready to use
- Pre-configured for inventory operations
- Understands business context
- Works immediately — no training needed

### Natural Language Everything
Don't learn a new system. Just describe what you need:
- ❌ Navigate to Reports → Sales → Filter by Date → Export
- ✅ "Show me last week's sales and send it to my email"

### Intelligent Context
The AI remembers your conversation and business context:
```
You: "Add 50 shirts"
AI: What's the price per shirt?
You: "350"
AI: ✓ Added 50 Shirts @ Rs. 350 = Rs. 17,500 total value
You: "Make it 100"
AI: ✓ Updated to 100 Shirts @ Rs. 350 = Rs. 35,000 total value
```

---

## Ready to Start?

1. **Sign up** for an account
2. **Connect** your database (or use ours)
3. **Start talking** to your AI assistant
4. **Save hours** every day

---

*IMS - Making inventory management intelligent.*
