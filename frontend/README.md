# StoreLite IMS Frontend - Phase 3 (Next.js)

A modern, responsive Next.js frontend for StoreLite inventory and billing system.

## Features

- **Admin Interface** (`/admin`)
  - Add new inventory items
  - View and search items by name/category
  - Update item prices and stock quantities
  - Real-time item list management

- **POS Interface** (`/pos`)
  - Search and add items to bill
  - Adjust quantities and remove items
  - Real-time bill total calculation
  - Generate and print invoices
  - Stock level monitoring

- **Resilience Features**
  - Auto-retry API calls (3 attempts with exponential backoff)
  - Real-time stock monitoring (5-10s polling)
  - User-friendly error messages
  - Manual retry button on failures

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios with retry logic
- **State Management**: React Context API

## Prerequisites

- Node.js 18+
- npm or yarn
- Phase 2 FastAPI backend running at `http://localhost:8000`
- PostgreSQL accessible (via FastAPI)

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Setup

Copy `.env.local.example` to `.env.local` and update configuration:

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### 4. Access the Application

- **Admin Page**: http://localhost:3000/admin
- **POS Page**: http://localhost:3000/pos

## Available Scripts

```bash
# Development server (with hot reload)
npm run dev

# Production build
npm run build

# Run production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint
```

## Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root layout with navigation
│   ├── page.tsx                 # Landing page
│   ├── admin/
│   │   ├── layout.tsx
│   │   └── page.tsx            # Admin inventory page
│   ├── pos/
│   │   ├── layout.tsx
│   │   └── page.tsx            # POS billing page
│   └── globals.css             # Global styles
├── components/
│   ├── admin/                  # Admin-specific components
│   ├── pos/                    # POS-specific components
│   └── shared/                 # Shared components (Header, Navigation, etc.)
├── lib/
│   ├── api.ts                  # API client with retry logic
│   ├── hooks.ts                # Custom React hooks
│   ├── types.ts                # TypeScript interfaces
│   ├── validation.ts           # Form validation rules
│   ├── constants.ts            # App constants
│   └── errorMap.ts             # Error message mapping
├── styles/                     # Optional CSS modules
├── public/                     # Static assets
├── package.json
├── tsconfig.json              # TypeScript configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── next.config.js             # Next.js configuration
├── postcss.config.js          # PostCSS configuration
└── README.md                  # This file
```

## API Integration

The frontend integrates with the FastAPI backend using these endpoints:

### Items Endpoints
- `GET /items` - List all items (with optional filters)
- `POST /items` - Add new item
- `GET /items/{id}` - Get single item
- `PUT /items/{id}` - Update item

### Bills Endpoints
- `POST /bills` - Create bill and deduct stock
- `GET /bills/{id}` - Retrieve bill for invoice

All requests include:
- Automatic retry (3 attempts with exponential backoff)
- User-friendly error handling
- Request/response type validation

## Development Workflow

### Adding a New Component

1. Create component file in appropriate directory (`admin/`, `pos/`, or `shared/`)
2. Use TypeScript interfaces from `lib/types.ts`
3. Import shared utilities from `lib/`
4. Style with Tailwind CSS classes

### Adding a New API Call

1. Add method to `APIClient` class in `lib/api.ts`
2. Define request/response types in `lib/types.ts`
3. Use in components via custom hooks from `lib/hooks.ts`

### Form Validation

Use validation functions from `lib/validation.ts`:
```typescript
import { validateItem } from '@/lib/validation';
const errors = validateItem(formData);
```

## Testing

### Manual Testing Scenarios

1. **Admin Workflow**
   - Navigate to `/admin`
   - Add item with form validation
   - Search items by name/category
   - Edit item price/stock

2. **POS Workflow**
   - Navigate to `/pos`
   - Search and add items
   - Adjust quantities
   - Generate and print invoice

3. **Error Handling**
   - Stop FastAPI backend
   - Try API call
   - Verify retry mechanism
   - Verify error message display

4. **Stock Monitoring**
   - Open POS page with item in bill
   - Update item stock to 0 via Admin page
   - Wait for monitoring alert
   - Verify warning overlay

## Performance Goals

- Page load: < 3 seconds
- Search/filter: < 1 second response
- Bill total calculation: < 100ms
- Stock monitoring: 5-10 second polling interval

## Troubleshooting

### "Cannot connect to API"
- Verify FastAPI backend is running at `http://localhost:8000`
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Verify CORS is enabled on FastAPI backend

### "Items not loading"
- Check browser console for network errors
- Verify database has items (check via FastAPI Swagger docs)
- Try manual retry button

### TypeScript errors
Run type checking: `npm run type-check`

## Next Steps

1. Complete Phase 1 setup
2. Run `npm install` to install dependencies
3. Create `.env.local` and configure API URL
4. Run `npm run dev` to start development server
5. Proceed to Phase 2 (Foundational infrastructure)

## Support

For issues or questions, refer to:
- Specification: `specs/003-nextjs-frontend-p3/spec.md`
- Implementation Plan: `specs/003-nextjs-frontend-p3/plan.md`
- Task Breakdown: `specs/003-nextjs-frontend-p3/tasks.md`

---

**Phase 3 Frontend Ready for Implementation**
