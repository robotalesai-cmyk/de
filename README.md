# Cannabis Apotheken Finder

Eine deutschsprachige Web-Anwendung zum Finden und Filtern von medizinischen Cannabis-Sorten nach Wirkungen, Effekten und Beschwerden.

## Über das Projekt

Diese Anwendung wurde entwickelt, um Patienten und medizinisches Fachpersonal bei der Suche nach geeigneten medizinischen Cannabis-Sorten zu unterstützen. Die App scannt legal verfügbare öffentliche Daten deutscher Cannabis-Apotheken und ermöglicht eine strukturierte Suche basierend auf:

- **Wirkungen**: Entspannend, Schmerzlindernd, Beruhigend, etc.
- **Beschwerden**: Chronische Schmerzen, Angstzustände, Schlafstörungen, etc.
- **THC/CBD-Gehalt**: Filterbar nach Cannabinoid-Profil
- **Genetik**: Indica, Sativa, oder Hybrid
- **Verfügbarkeit**: In deutschen Apotheken

## Technologie-Stack

- **Frontend**: Next.js 16, React 19, TypeScript
- **Styling**: Tailwind CSS
- **Backend**: Next.js API Routes
- **Datenbank**: PostgreSQL mit Prisma ORM
- **Datenquellen**: Öffentlich zugängliche, legale Quellen

## Funktionen

✅ Filtern nach Wirkungen und Beschwerden
✅ Erweiterte Filteroptionen (THC/CBD-Gehalt, Genetik, Standort)
✅ Empfehlungsalgorithmus basierend auf Nutzerpräferenzen
✅ Anzeige verfügbarer Apotheken und Preise
✅ Responsive Design für Desktop und Mobile
✅ Rechtlicher Disclaimer

## Installation

1. Repository klonen:
```bash
git clone <repository-url>
cd de
```

2. Abhängigkeiten installieren:
```bash
npm install
```

3. Umgebungsvariablen konfigurieren:
```bash
# .env Datei bearbeiten
DATABASE_URL="postgresql://user:password@localhost:5432/cannabis_pharmacy"
```

4. Datenbank einrichten:
```bash
# Prisma migrations ausführen
npx prisma migrate dev --name init

# Optional: Datenbank mit Beispieldaten füllen
npx tsx scripts/seed.ts
```

5. Entwicklungsserver starten:
```bash
npm run dev
```

Öffnen Sie [http://localhost:3000](http://localhost:3000) im Browser.

## Datenbank Schema

Das Datenbankmodell umfasst:

- **Strain**: Cannabis-Sorten mit THC/CBD-Gehalt und Beschreibung
- **Pharmacy**: Apotheken-Informationen mit Standort
- **Effect**: Wirkungen (z.B. entspannend, schmerzlindernd)
- **Condition**: Medizinische Beschwerden
- **PharmacyStrain**: Verknüpfung zwischen Apotheken und Sorten
- **StrainEffect**: Verknüpfung zwischen Sorten und Wirkungen
- **StrainCondition**: Verknüpfung zwischen Sorten und Beschwerden

## API Endpoints

- `GET /api/strains` - Alle verfügbaren Sorten
- `GET /api/pharmacies` - Alle Apotheken
- `GET /api/effects` - Alle Wirkungen
- `GET /api/conditions` - Alle Beschwerden
- `POST /api/recommendations` - Personalisierte Empfehlungen
- `POST /api/seed` - Datenbank mit Beispieldaten füllen

## Rechtlicher Hinweis

⚠️ **Wichtig**: Diese Anwendung dient ausschließlich zu Informationszwecken.

- Alle Daten stammen aus öffentlich zugänglichen, legalen Quellen
- Medizinisches Cannabis ist in Deutschland verschreibungspflichtig
- Diese App stellt keine medizinische Beratung dar
- Konsultieren Sie immer einen qualifizierten Arzt
- Die Verfügbarkeit und Preise können variieren

## Entwicklung

```bash
# Entwicklungsserver
npm run dev

# Production Build
npm run build

# Production Server starten
npm start

# Linting
npm run lint

# Prisma Studio (Datenbank GUI)
npx prisma studio
```

## Deployment

Die App kann auf Plattformen wie Vercel, Railway oder anderen Node.js-Hosting-Diensten deployed werden. Stellen Sie sicher, dass eine PostgreSQL-Datenbank verfügbar ist.

## Lizenz

Dieses Projekt dient ausschließlich zu Bildungs- und Informationszwecken.
