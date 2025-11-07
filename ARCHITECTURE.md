# Cannabis Apotheken Finder - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (UI)                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Homepage   │  │ StrainFinder │  │  StrainCard     │  │
│  │  Disclaimer  │  │   Component  │  │   Component     │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│         │                  │                    │           │
│         └──────────────────┴────────────────────┘           │
│                            │                                │
└────────────────────────────┼────────────────────────────────┘
                             │
                    HTTP Requests
                             │
┌────────────────────────────┼────────────────────────────────┐
│                    Next.js API Routes                        │
│                                                              │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐    │
│  │ /strains │  │ /effects  │  │ /recommendations     │    │
│  │          │  │           │  │                      │    │
│  └──────────┘  └───────────┘  └──────────────────────┘    │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐    │
│  │/pharmacies│  │/conditions│  │ /seed                │    │
│  └──────────┘  └───────────┘  └──────────────────────┘    │
│         │              │                   │                │
│         └──────────────┴───────────────────┘                │
│                        │                                    │
└────────────────────────┼────────────────────────────────────┘
                         │
                 Prisma ORM Client
                         │
┌────────────────────────┼────────────────────────────────────┐
│                Business Logic Layer                          │
│                                                              │
│  ┌────────────────┐              ┌────────────────────┐    │
│  │  Fetcher.ts    │              │ Recommendations.ts │    │
│  │  Data Sources  │              │ Ranking Algorithm  │    │
│  └────────────────┘              └────────────────────┘    │
│                                                              │
└────────────────────────┼────────────────────────────────────┘
                         │
                    SQL Queries
                         │
┌────────────────────────┼────────────────────────────────────┐
│                  PostgreSQL Database                         │
│                                                              │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌───────────┐     │
│  │ Strain  │  │ Pharmacy │  │ Effect │  │ Condition │     │
│  └─────────┘  └──────────┘  └────────┘  └───────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │PharmacyStrain│  │ StrainEffect │  │StrainCondition│     │
│  │  (junction)  │  │  (junction)  │  │  (junction)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Search Flow
```
User → StrainFinder Component → POST /api/recommendations
                                      ↓
                            Recommendations.rankStrains()
                                      ↓
                            Query Database (Prisma)
                                      ↓
                            Apply Scoring Algorithm
                                      ↓
                            Return Ranked Results
                                      ↓
                            Display in StrainCards
```

### 2. Data Seeding Flow
```
Admin → POST /api/seed → fetcher.seedDatabase()
                              ↓
                    fetchSampleStrains()
                    fetchSamplePharmacies()
                              ↓
                    Create Database Records
                              ↓
                    Link Relations (Effects, Conditions)
```

## Database Schema

### Core Tables
- **Strain**: Cannabis varieties with THC/CBD content
- **Pharmacy**: German pharmacy locations
- **Effect**: Effects like "Entspannend", "Schmerzlindernd"
- **Condition**: Medical conditions like "Chronische Schmerzen"

### Junction Tables (Many-to-Many)
- **PharmacyStrain**: Which pharmacies stock which strains
- **StrainEffect**: Which effects each strain has
- **StrainCondition**: Which conditions each strain helps with

## Recommendation Algorithm

### Scoring Weights
```typescript
EFFECT_MATCH: 10           // Points per matching effect
CONDITION_MATCH: 15        // Points per matching condition (higher priority)
THC_COMPLIANCE: 20         // Bonus for staying within THC limit
THC_VIOLATION_PENALTY: 30  // Penalty for exceeding THC limit
CBD_COMPLIANCE: 25         // Bonus for meeting CBD requirement
GENETICS_MATCH: 15         // Bonus for matching genetics preference
AVAILABILITY: 5            // Bonus per pharmacy
```

### Scoring Process
1. Match user-selected effects → Add points × intensity
2. Match medical conditions → Add points × efficacy
3. Check THC/CBD preferences → Add/subtract points
4. Check genetics preference → Add bonus
5. Check availability → Add bonus per pharmacy
6. Filter out negative scores
7. Sort by score descending

## Component Structure

### Main Components
- **page.tsx**: Main landing page
- **StrainFinder.tsx**: Search interface with filters
- **StrainCard.tsx**: Display individual strain info
- **Disclaimer.tsx**: Legal disclaimer component

### State Management
- React useState for local component state
- No external state management needed (keeps it simple)
- API calls use native fetch

## API Design

All endpoints follow RESTful conventions:
- GET for retrieving data
- POST for recommendations (accepts preferences in body)
- POST for seeding (admin operation)

## Security Measures

1. **Prisma ORM**: Prevents SQL injection
2. **Environment Variables**: Sensitive config external
3. **Input Validation**: Type checking with TypeScript
4. **No User Authentication**: Reduces attack surface
5. **Read-Only Operations**: Most endpoints are GET
6. **Legal Compliance**: Only public data sources

## Deployment Options

### Development
```bash
docker-compose up -d  # PostgreSQL
npm run dev          # Next.js dev server
```

### Production

**Option 1: Vercel**
- Push to GitHub
- Connect Vercel
- Add PostgreSQL (Vercel Postgres, Supabase, etc.)
- Set DATABASE_URL
- Deploy

**Option 2: Docker**
```bash
docker build -t cannabis-pharmacy .
docker run -p 3000:3000 \
  -e DATABASE_URL="postgresql://..." \
  cannabis-pharmacy
```

**Option 3: Railway**
- Connect GitHub repo
- Add PostgreSQL service
- Deploy automatically

## Performance Considerations

1. **Database Indexes**: On frequently queried fields
2. **Static Generation**: Homepage pre-rendered
3. **Prisma Connection Pooling**: Efficient DB connections
4. **Lazy Loading**: Components loaded as needed
5. **Optimized Queries**: Include relations in one query

## Scalability

Current design supports:
- **100s of strains**: Efficient indexing
- **1000s of pharmacies**: Indexed by city/postal
- **Concurrent users**: Stateless API, scales horizontally
- **Growing data**: Normalized schema prevents duplication

## Monitoring & Logging

Built-in:
- Server console logs for errors
- Next.js build-time warnings
- Prisma query logging (dev mode)

Recommended additions:
- Sentry for error tracking
- Vercel Analytics
- Custom logging middleware

## Future Enhancements

1. **Caching**: Redis for frequently accessed data
2. **Search**: Full-text search with PostgreSQL or Elasticsearch
3. **Real-time**: WebSocket for live availability updates
4. **CDN**: Static assets via CDN
5. **Microservices**: Separate services for different data sources

---

**Last Updated:** 2025-11-07
