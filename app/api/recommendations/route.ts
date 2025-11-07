import { NextResponse } from 'next/server';
import { rankStrains, UserPreferences } from '@/lib/recommendations';

export async function POST(request: Request) {
  try {
    const preferences: UserPreferences = await request.json();
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
