# Setup Guide - Cannabis Apotheken Finder

Diese Anleitung erklärt die Einrichtung und Inbetriebnahme der Anwendung.

## Voraussetzungen

- Node.js 18+ 
- PostgreSQL 14+ (oder Docker)
- npm oder yarn

## Schnellstart mit Docker

Die einfachste Methode ist die Verwendung von Docker für die Datenbank:

```bash
# 1. Docker-Container für PostgreSQL starten
docker-compose up -d

# 2. Abhängigkeiten installieren
npm install

# 3. Datenbank-Schema erstellen
npm run db:migrate

# 4. Beispieldaten einfügen
npm run db:seed

# 5. Entwicklungsserver starten
npm run dev
```

Öffnen Sie [http://localhost:3000](http://localhost:3000) im Browser.

## Manuelle Installation (ohne Docker)

### 1. PostgreSQL installieren und konfigurieren

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS (mit Homebrew)
brew install postgresql
brew services start postgresql

# Windows
# Laden Sie PostgreSQL von https://www.postgresql.org/download/windows/ herunter
```

### 2. Datenbank erstellen

```bash
psql -U postgres
CREATE DATABASE cannabis_pharmacy;
\q
```

### 3. Umgebungsvariablen konfigurieren

Bearbeiten Sie die `.env` Datei:

```env
DATABASE_URL="postgresql://postgres:IhrPasswort@localhost:5432/cannabis_pharmacy?schema=public"
NEXT_PUBLIC_APP_NAME="Cannabis Apotheken Finder"
```

### 4. Anwendung einrichten

```bash
# Abhängigkeiten installieren
npm install

# Prisma Client generieren
npm run prisma:generate

# Datenbank-Migrationen ausführen
npm run db:migrate

# Beispieldaten einfügen
npm run db:seed

# Entwicklungsserver starten
npm run dev
```

## Verfügbare Scripts

```bash
npm run dev              # Entwicklungsserver starten
npm run build            # Produktions-Build erstellen
npm start                # Produktionsserver starten
npm run lint             # Code-Linting
npm run db:push          # Schema direkt in DB pushen (ohne Migration)
npm run db:migrate       # Neue Migration erstellen und ausführen
npm run db:seed          # Datenbank mit Beispieldaten füllen
npm run prisma:generate  # Prisma Client generieren
npm run prisma:studio    # Prisma Studio öffnen (Datenbank-GUI)
```

## Datenbank verwalten

### Prisma Studio (GUI)

```bash
npm run prisma:studio
```

Öffnet eine grafische Benutzeroberfläche unter [http://localhost:5555](http://localhost:5555) zum Anzeigen und Bearbeiten der Daten.

### Neue Daten hinzufügen

**Option 1: Über die API**

```bash
# POST Request an /api/seed
curl -X POST http://localhost:3000/api/seed
```

**Option 2: Über das Seed-Script**

```bash
npm run db:seed
```

**Option 3: Über Prisma Studio**

```bash
npm run prisma:studio
# Navigieren Sie zu http://localhost:5555 und fügen Sie Daten manuell hinzu
```

## Produktions-Deployment

### Vercel

1. Repository zu Vercel verbinden
2. PostgreSQL-Datenbank hinzufügen (z.B. Vercel Postgres, Supabase, oder Railway)
3. Umgebungsvariablen setzen:
   - `DATABASE_URL`
4. Deploy!

### Railway

```bash
# Railway CLI installieren
npm i -g @railway/cli

# Einloggen
railway login

# Projekt erstellen
railway init

# PostgreSQL hinzufügen
railway add --database postgres

# Environment Variables werden automatisch gesetzt

# Deployen
railway up
```

### Docker (Produktion)

```bash
# Docker Image bauen
docker build -t cannabis-pharmacy .

# Container starten
docker run -p 3000:3000 \
  -e DATABASE_URL="postgresql://..." \
  cannabis-pharmacy
```

## Datenquellen erweitern

Um echte Datenquellen zu integrieren, bearbeiten Sie `lib/fetcher.ts`:

```typescript
// Beispiel: API-Integration
export async function fetchRealPharmacies(): Promise<PharmacyData[]> {
  const response = await fetch('https://api.example.com/pharmacies');
  const data = await response.json();
  return data;
}
```

**Wichtig:** Stellen Sie sicher, dass Sie nur öffentliche, legale Datenquellen verwenden.

## Troubleshooting

### Problem: Datenbank-Verbindung fehlgeschlagen

**Lösung:**
1. Überprüfen Sie, ob PostgreSQL läuft: `pg_isready`
2. Prüfen Sie die DATABASE_URL in `.env`
3. Testen Sie die Verbindung: `psql $DATABASE_URL`

### Problem: Prisma Client nicht gefunden

**Lösung:**
```bash
npm run prisma:generate
```

### Problem: Migrationen schlagen fehl

**Lösung:**
```bash
# Alle Migrationen zurücksetzen und neu starten
npx prisma migrate reset
npm run db:migrate
```

### Problem: Port 3000 bereits belegt

**Lösung:**
```bash
# Anderen Port verwenden
PORT=3001 npm run dev
```

## Weitere Ressourcen

- [Next.js Dokumentation](https://nextjs.org/docs)
- [Prisma Dokumentation](https://www.prisma.io/docs)
- [PostgreSQL Dokumentation](https://www.postgresql.org/docs/)
- [Tailwind CSS Dokumentation](https://tailwindcss.com/docs)

## Support

Bei Fragen oder Problemen öffnen Sie bitte ein Issue im GitHub-Repository.
