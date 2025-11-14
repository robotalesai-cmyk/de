# Contributing Guide

Vielen Dank für Ihr Interesse an diesem Projekt! Diese Anleitung hilft Ihnen, zur Weiterentwicklung beizutragen.

## Datenquellen erweitern

### Wichtige Hinweise zu Datenquellen

⚠️ **Rechtliche Anforderungen:**
- Verwenden Sie nur öffentlich zugängliche, legale Datenquellen
- Beachten Sie die Nutzungsbedingungen jeder Datenquelle
- Fügen Sie keine urheberrechtlich geschützten Daten ohne Erlaubnis hinzu
- Respektieren Sie die Datenschutzbestimmungen (DSGVO)

### Neue Datenquellen hinzufügen

Alle Datenquellen werden in `lib/fetcher.ts` verwaltet. Hier ist ein Beispiel:

```typescript
// lib/fetcher.ts

export interface ApiPharmacySource {
  url: string;
  parser: (data: any) => PharmacyData[];
}

export async function fetchFromPublicAPI(
  apiUrl: string
): Promise<StrainData[]> {
  try {
    const response = await fetch(apiUrl, {
      headers: {
        'User-Agent': 'Cannabis-Apotheken-Finder/1.0'
      }
    });
    
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }
    
    const data = await response.json();
    return parseApiData(data);
  } catch (error) {
    console.error('Error fetching from API:', error);
    return [];
  }
}

function parseApiData(data: any): StrainData[] {
  // Implementieren Sie hier Ihre Parsing-Logik
  return data.strains.map((strain: any) => ({
    name: strain.name,
    thcContent: parseFloat(strain.thc),
    cbdContent: parseFloat(strain.cbd),
    description: strain.description,
    genetics: strain.type,
    effects: strain.effects || [],
    conditions: strain.medicalUses || []
  }));
}
```

### HTML-Scraping (falls keine API verfügbar)

```typescript
import * as cheerio from 'cheerio';

export async function scrapePharmacyWebsite(
  url: string
): Promise<PharmacyData> {
  const response = await fetch(url);
  const html = await response.text();
  const $ = cheerio.load(html);
  
  return {
    name: $('.pharmacy-name').text().trim(),
    address: $('.address').text().trim(),
    city: $('.city').text().trim(),
    postalCode: $('.postal-code').text().trim(),
    // ... weitere Felder
  };
}
```

**Wichtig:** Scraping sollte nur als letztes Mittel verwendet werden. Prüfen Sie vorher:
1. Gibt es eine offizielle API?
2. Erlauben die robots.txt und Nutzungsbedingungen das Scraping?
3. Implementieren Sie Rate-Limiting

### Datenvalidierung

Validieren Sie alle eingehenden Daten:

```typescript
function validateStrainData(data: Partial<StrainData>): StrainData | null {
  if (!data.name || data.name.trim().length === 0) {
    console.warn('Strain missing name');
    return null;
  }
  
  if (data.thcContent && (data.thcContent < 0 || data.thcContent > 100)) {
    console.warn('Invalid THC content');
    return null;
  }
  
  // Weitere Validierungen...
  
  return data as StrainData;
}
```

## Neue Features hinzufügen

### 1. Datenmodell erweitern

Wenn Sie neue Felder benötigen, aktualisieren Sie das Prisma-Schema:

```prisma
// prisma/schema.prisma

model Strain {
  // Vorhandene Felder...
  
  // Neues Feld hinzufügen:
  flavors      String[]  // Array für Geschmacksrichtungen
  harvestDate  DateTime? // Erntezeit
}
```

Dann Migration erstellen:

```bash
npx prisma migrate dev --name add_strain_flavors
```

### 2. API-Endpoints hinzufügen

Erstellen Sie neue API-Routes unter `app/api/`:

```typescript
// app/api/flavors/route.ts

import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
  try {
    const strains = await prisma.strain.findMany({
      select: { flavors: true },
      distinct: ['flavors']
    });
    
    const uniqueFlavors = [...new Set(strains.flatMap(s => s.flavors))];
    return NextResponse.json(uniqueFlavors);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch flavors' }, { status: 500 });
  }
}
```

### 3. UI-Komponenten erweitern

Neue React-Komponenten unter `components/`:

```typescript
// components/FlavorFilter.tsx

'use client';

import { useState, useEffect } from 'react';

export default function FlavorFilter({ onFilterChange }: Props) {
  const [flavors, setFlavors] = useState<string[]>([]);
  
  useEffect(() => {
    fetch('/api/flavors')
      .then(res => res.json())
      .then(setFlavors);
  }, []);
  
  return (
    <div>
      {flavors.map(flavor => (
        <button key={flavor} onClick={() => onFilterChange(flavor)}>
          {flavor}
        </button>
      ))}
    </div>
  );
}
```

## Code-Qualität

### Linting

```bash
npm run lint
```

### TypeScript Type-Checking

```bash
npx tsc --noEmit
```

### Code-Formatierung

Wir empfehlen die Verwendung von Prettier:

```bash
npx prettier --write .
```

## Testing

### Manuelle Tests

1. Starten Sie den Dev-Server: `npm run dev`
2. Testen Sie alle Features manuell
3. Überprüfen Sie die Browser-Konsole auf Fehler
4. Testen Sie auf verschiedenen Bildschirmgrößen

### API-Tests

Verwenden Sie Tools wie curl oder Postman:

```bash
# Strains abrufen
curl http://localhost:3000/api/strains

# Empfehlungen abrufen
curl -X POST http://localhost:3000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{"conditions":["Schmerzen"]}'
```

## Pull Requests

1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch: `git checkout -b feature/mein-feature`
3. Committen Sie Ihre Änderungen: `git commit -m 'Add some feature'`
4. Pushen Sie zum Branch: `git push origin feature/mein-feature`
5. Öffnen Sie einen Pull Request

### PR-Checkliste

- [ ] Code folgt dem bestehenden Stil
- [ ] Alle Builds laufen erfolgreich
- [ ] Keine Linting-Fehler
- [ ] README/Dokumentation aktualisiert (falls nötig)
- [ ] Nur legale, öffentliche Datenquellen verwendet
- [ ] Datenschutz beachtet

## Bekannte öffentliche Datenquellen

Hier sind einige potenzielle Quellen für medizinische Cannabis-Informationen in Deutschland (Stand 2024):

1. **Bundesinstitut für Arzneimittel und Medizinprodukte (BfArM)**
   - Offizielle Informationen zu medizinischem Cannabis
   - URL: https://www.bfarm.de/

2. **Deutscher Hanfverband**
   - Rechtliche und medizinische Informationen
   - URL: https://hanfverband.de/

3. **Apotheken-APIs** (falls verfügbar)
   - Viele Apotheken bieten öffentliche Verfügbarkeitsinformationen

**Hinweis:** Überprüfen Sie immer die Aktualität und Legalität der Nutzung dieser Quellen.

## Fragen?

Bei Fragen oder Problemen öffnen Sie bitte ein Issue im GitHub-Repository.
