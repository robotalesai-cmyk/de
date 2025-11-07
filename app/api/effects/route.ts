import { NextResponse } from 'next/server';
import { getAllEffects } from '@/lib/recommendations';

export async function GET() {
  try {
    const effects = await getAllEffects();
    return NextResponse.json(effects);
  } catch (error) {
    console.error('Error fetching effects:', error);
    return NextResponse.json(
      { error: 'Failed to fetch effects' },
      { status: 500 }
    );
  }
}
