import { NextResponse } from 'next/server';
import { rankStrains, UserPreferences } from '@/lib/recommendations';

export async function POST(request: Request) {
  try {
    const preferences: UserPreferences = await request.json();

    // Validate preferredEffects (should be an array if present)
    if (
      preferences.preferredEffects !== undefined &&
      !Array.isArray(preferences.preferredEffects)
    ) {
      return NextResponse.json(
        { error: 'Invalid preferredEffects: must be an array' },
        { status: 400 }
      );
    }

    // Validate conditions (should be an array if present)
    if (
      preferences.conditions !== undefined &&
      !Array.isArray(preferences.conditions)
    ) {
      return NextResponse.json(
        { error: 'Invalid conditions: must be an array' },
        { status: 400 }
      );
    }

    // Validate maxThc (should be a number between 0 and 100 if present)
    if (
      preferences.maxThc !== undefined &&
      (typeof preferences.maxThc !== 'number' ||
        preferences.maxThc < 0 ||
        preferences.maxThc > 100)
    ) {
      return NextResponse.json(
        { error: 'Invalid maxThc: must be a number between 0 and 100' },
        { status: 400 }
      );
    }

    // Validate minCbd (should be a number between 0 and 100 if present)
    if (
      preferences.minCbd !== undefined &&
      (typeof preferences.minCbd !== 'number' ||
        preferences.minCbd < 0 ||
        preferences.minCbd > 100)
    ) {
      return NextResponse.json(
        { error: 'Invalid minCbd: must be a number between 0 and 100' },
        { status: 400 }
      );
    }

    // Validate genetics (should be one of the allowed values if present)
    if (
      preferences.genetics !== undefined &&
      !['Indica', 'Sativa', 'Hybrid'].includes(preferences.genetics)
    ) {
      return NextResponse.json(
        { error: 'Invalid genetics: must be Indica, Sativa, or Hybrid' },
        { status: 400 }
      );
    }

    const recommendations = await rankStrains(preferences);

    return NextResponse.json(recommendations);
  } catch (error) {
    console.error('Error generating recommendations:', error);
    return NextResponse.json(
      { error: 'Failed to generate recommendations' },
      { status: 500 }
    );
  }
}
