import { NextResponse } from 'next/server';
import { getAllConditions } from '@/lib/recommendations';

export async function GET() {
  try {
    const conditions = await getAllConditions();
    return NextResponse.json(conditions);
  } catch (error) {
    console.error('Error fetching conditions:', error);
    return NextResponse.json(
      { error: 'Failed to fetch conditions' },
      { status: 500 }
    );
  }
}
