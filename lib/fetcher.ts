/**
 * Data Fetcher for German Cannabis Pharmacies
 * 
 * This module provides utilities to fetch publicly available data
 * about cannabis strains and pharmacies from legal sources.
 * 
 * IMPORTANT: Only uses publicly accessible, legal data sources.
 */

import { prisma } from './prisma';

// Price range constants for medical cannabis in Germany (in EUR)
// Based on typical pharmacy pricing as of 2024
const PRICE_RANGE = {
  MIN: 150,  // Minimum price per prescription unit
  MAX: 350   // Maximum price per prescription unit
} as const;

export interface StrainData {
  name: string;
  thcContent?: number;
  cbdContent?: number;
  description?: string;
  genetics?: string;
  effects?: string[];
  conditions?: string[];
}

export interface PharmacyData {
  name: string;
  address?: string;
  city?: string;
  postalCode?: string;
  phone?: string;
  email?: string;
  website?: string;
  latitude?: number;
  longitude?: number;
}

/**
 * Fetch sample strain data (to be replaced with real API calls)
 * In production, this would connect to legal public APIs
 */
export async function fetchSampleStrains(): Promise<StrainData[]> {
  // Sample data - in production, this would fetch from legal public APIs
  return [
    {
      name: "CBD-reiche Sorte 1",
      thcContent: 0.2,
      cbdContent: 18.0,
      description: "Hochwertige CBD-dominante Sorte für medizinische Anwendung",
      genetics: "Hybrid",
      effects: ["Entspannend", "Schmerzlindernd", "Beruhigend"],
      conditions: ["Chronische Schmerzen", "Angstzustände", "Schlafstörungen"]
    },
    {
      name: "Balanced Sorte 1",
      thcContent: 8.0,
      cbdContent: 8.0,
      description: "Ausgewogene THC/CBD Sorte für verschiedene Beschwerden",
      genetics: "Hybrid",
      effects: ["Ausbalanciert", "Entspannend", "Konzentrationsfähigkeit"],
      conditions: ["Migräne", "Entzündungen", "Stress"]
    },
    {
      name: "Medizinische Indica 1",
      thcContent: 15.0,
      cbdContent: 1.0,
      description: "Indica-dominante Sorte für Schmerztherapie",
      genetics: "Indica",
      effects: ["Stark entspannend", "Schmerzlindernd", "Appetitanregend"],
      conditions: ["Starke Schmerzen", "Appetitlosigkeit", "Schlafprobleme"]
    }
  ];
}

/**
 * Fetch sample pharmacy data (to be replaced with real API calls)
 * In production, this would connect to official German pharmacy databases
 */
export async function fetchSamplePharmacies(): Promise<PharmacyData[]> {
  // Sample data - in production, this would fetch from legal public APIs
  return [
    {
      name: "Apotheke am Marktplatz",
      address: "Marktplatz 1",
      city: "Berlin",
      postalCode: "10117",
      phone: "+49 30 12345678",
      website: "https://example-apotheke.de",
      latitude: 52.5200,
      longitude: 13.4050
    },
    {
      name: "Zentral-Apotheke",
      address: "Hauptstraße 45",
      city: "München",
      postalCode: "80331",
      phone: "+49 89 87654321",
      website: "https://example-zentral.de",
      latitude: 48.1351,
      longitude: 11.5820
    },
    {
      name: "Gesundheits-Apotheke",
      address: "Königsallee 12",
      city: "Hamburg",
      postalCode: "20095",
      phone: "+49 40 11223344",
      website: "https://example-gesundheit.de",
      latitude: 53.5511,
      longitude: 9.9937
    }
  ];
}

/**
 * Seed database with initial data
 */
export async function seedDatabase() {
  console.log('🌱 Seeding database with sample data...');

  // Clear existing data
  await prisma.strainCondition.deleteMany();
  await prisma.strainEffect.deleteMany();
  await prisma.pharmacyStrain.deleteMany();
  await prisma.condition.deleteMany();
  await prisma.effect.deleteMany();
  await prisma.strain.deleteMany();
  await prisma.pharmacy.deleteMany();

  // Fetch sample data
  const strains = await fetchSampleStrains();
  const pharmacies = await fetchSamplePharmacies();

  // Create pharmacies
  const pharmacyRecords = await Promise.all(
    pharmacies.map(pharmacy =>
      prisma.pharmacy.create({
        data: pharmacy
      })
    )
  );

  // Create effects and conditions sets
  const allEffects = new Set<string>();
  const allConditions = new Set<string>();

  strains.forEach(strain => {
    strain.effects?.forEach(effect => allEffects.add(effect));
    strain.conditions?.forEach(condition => allConditions.add(condition));
  });

  // Create effect records
  const effectRecords = await Promise.all(
    Array.from(allEffects).map(effectName =>
      prisma.effect.create({
        data: {
          name: effectName,
          category: 'positive'
        }
      })
    )
  );

  // Create condition records
  const conditionRecords = await Promise.all(
    Array.from(allConditions).map(conditionName =>
      prisma.condition.create({
        data: {
          name: conditionName
        }
      })
    )
  );

  // Create strains with relations
  for (const strainData of strains) {
    const strain = await prisma.strain.create({
      data: {
        name: strainData.name,
        thcContent: strainData.thcContent,
        cbdContent: strainData.cbdContent,
        description: strainData.description,
        genetics: strainData.genetics
      }
    });

    // Link effects
    if (strainData.effects) {
      const effectLinks = strainData.effects
        .map(effectName => {
          const effect = effectRecords.find(e => e.name === effectName);
          return effect
            ? {
                strainId: strain.id,
                effectId: effect.id,
                intensity: 7
              }
            : null;
        })
        .filter((link): link is { strainId: string; effectId: string; intensity: number } => link !== null);
      
      if (effectLinks.length > 0) {
        await prisma.strainEffect.createMany({
          data: effectLinks
        });
      }
    }

    // Link conditions
    if (strainData.conditions) {
      const conditionLinks = strainData.conditions
        .map(conditionName => {
          const condition = conditionRecords.find(c => c.name === conditionName);
          return condition
            ? {
                strainId: strain.id,
                conditionId: condition.id,
                efficacy: 7
              }
            : null;
        })
        .filter((link): link is { strainId: string; conditionId: string; efficacy: number } => link !== null);
      
      if (conditionLinks.length > 0) {
        await prisma.strainCondition.createMany({
          data: conditionLinks
        });
      }
    }

    // Link to pharmacies (randomly assign to some pharmacies)
    const randomPharmacies = pharmacyRecords
      .sort(() => Math.random() - 0.5)
      .slice(0, Math.floor(Math.random() * 2) + 1);

    if (randomPharmacies.length > 0) {
      await prisma.pharmacyStrain.createMany({
        data: randomPharmacies.map(pharmacy => ({
          pharmacyId: pharmacy.id,
          strainId: strain.id,
          inStock: true,
          price: Math.random() * (PRICE_RANGE.MAX - PRICE_RANGE.MIN) + PRICE_RANGE.MIN
        }))
      });
    }
  }

  console.log('✅ Database seeded successfully!');
  console.log(`Created ${strains.length} strains`);
  console.log(`Created ${pharmacies.length} pharmacies`);
  console.log(`Created ${effectRecords.length} effects`);
  console.log(`Created ${conditionRecords.length} conditions`);
}
