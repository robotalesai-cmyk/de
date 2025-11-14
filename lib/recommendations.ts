/**
 * Recommendation Engine
 * 
 * Ranks and recommends cannabis strains based on user preferences,
 * effects, and medical conditions.
 */

import { prisma } from './prisma';

// Scoring constants for the recommendation algorithm
const SCORING_WEIGHTS = {
  EFFECT_MATCH: 10,           // Points per matching effect * intensity
  CONDITION_MATCH: 15,         // Points per matching condition * efficacy (higher weight for medical needs)
  THC_COMPLIANCE: 20,          // Bonus for staying within THC limit
  THC_VIOLATION_PENALTY: 30,   // Penalty for exceeding max THC
  CBD_COMPLIANCE: 25,          // Bonus for meeting minimum CBD requirement
  GENETICS_MATCH: 15,          // Bonus for matching genetics preference
  AVAILABILITY_PER_PHARMACY: 5 // Bonus points per pharmacy that has the strain
} as const;

export interface UserPreferences {
  preferredEffects?: string[];
  conditions?: string[];
  maxThc?: number;
  minCbd?: number;
  genetics?: string; // Indica/Sativa/Hybrid
  location?: {
    city?: string;
    postalCode?: string;
  };
}

export interface RankedStrain {
  id: string;
  name: string;
  thcContent: number | null;
  cbdContent: number | null;
  description: string | null;
  genetics: string | null;
  score: number;
  matchingEffects: string[];
  matchingConditions: string[];
  availablePharmacies: {
    id: string;
    name: string;
    city: string | null;
    inStock: boolean;
    price: number | null;
  }[];
}

/**
 * Calculate strain ranking based on user preferences
 */
export async function rankStrains(
  preferences: UserPreferences
): Promise<RankedStrain[]> {
  // Fetch all strains with their relations
  const strains = await prisma.strain.findMany({
    include: {
      effects: {
        include: {
          effect: true
        }
      },
      conditions: {
        include: {
          condition: true
        }
      },
      pharmacies: {
        include: {
          pharmacy: true
        },
        where: preferences.location?.city
          ? {
              pharmacy: {
                city: preferences.location.city
              }
            }
          : undefined
      }
    }
  });

  // Rank strains
  const rankedStrains: RankedStrain[] = strains
    .map(strain => {
      let score = 0;
      const matchingEffects: string[] = [];
      const matchingConditions: string[] = [];

      // Score based on effects
      if (preferences.preferredEffects?.length) {
        strain.effects.forEach(se => {
          if (preferences.preferredEffects!.includes(se.effect.name)) {
            score += se.intensity * SCORING_WEIGHTS.EFFECT_MATCH;
            matchingEffects.push(se.effect.name);
          }
        });
      }

      // Score based on conditions
      if (preferences.conditions?.length) {
        strain.conditions.forEach(sc => {
          if (preferences.conditions!.includes(sc.condition.name)) {
            score += sc.efficacy * SCORING_WEIGHTS.CONDITION_MATCH;
            matchingConditions.push(sc.condition.name);
          }
        });
      }

      // Score based on THC/CBD preferences
      if (preferences.maxThc !== undefined && strain.thcContent !== null) {
        if (strain.thcContent <= preferences.maxThc) {
          score += SCORING_WEIGHTS.THC_COMPLIANCE;
        } else {
          score -= SCORING_WEIGHTS.THC_VIOLATION_PENALTY;
        }
      }

      if (preferences.minCbd !== undefined && strain.cbdContent !== null) {
        if (strain.cbdContent >= preferences.minCbd) {
          score += SCORING_WEIGHTS.CBD_COMPLIANCE;
        }
      }

      // Score based on genetics preference
      if (preferences.genetics && strain.genetics === preferences.genetics) {
        score += SCORING_WEIGHTS.GENETICS_MATCH;
      }

      // Bonus for availability
      if (strain.pharmacies.length > 0) {
        score += strain.pharmacies.length * SCORING_WEIGHTS.AVAILABILITY_PER_PHARMACY;
      }

      return {
        id: strain.id,
        name: strain.name,
        thcContent: strain.thcContent,
        cbdContent: strain.cbdContent,
        description: strain.description,
        genetics: strain.genetics,
        score,
        matchingEffects,
        matchingConditions,
        availablePharmacies: strain.pharmacies.map(ps => ({
          id: ps.pharmacy.id,
          name: ps.pharmacy.name,
          city: ps.pharmacy.city,
          inStock: ps.inStock,
          price: ps.price
        }))
      };
    })
    .filter(strain => strain.score > 0) // Only return strains with positive scores
    .sort((a, b) => b.score - a.score); // Sort by score descending

  return rankedStrains;
}

/**
 * Get strain recommendations based on a specific condition
 */
export async function getRecommendationsForCondition(
  conditionName: string,
  limit: number = 5
): Promise<RankedStrain[]> {
  const preferences: UserPreferences = {
    conditions: [conditionName]
  };

  const ranked = await rankStrains(preferences);
  return ranked.slice(0, limit);
}

/**
 * Get all available effects
 */
export async function getAllEffects() {
  return await prisma.effect.findMany({
    orderBy: { name: 'asc' }
  });
}

/**
 * Get all available conditions
 */
export async function getAllConditions() {
  return await prisma.condition.findMany({
    orderBy: { name: 'asc' }
  });
}
