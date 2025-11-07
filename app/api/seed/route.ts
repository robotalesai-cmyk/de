import { NextResponse } from 'next/server';
import { seedDatabase } from '@/lib/fetcher';

export async function POST() {
  // Restrict to development/staging environments only
  if (process.env.NODE_ENV === 'production' && process.env.ALLOW_SEED !== 'true') {
    return NextResponse.json(
      { error: 'Forbidden: Seeding is not allowed in production' },
      { status: 403 }
    );
  }

  try {
    await seedDatabase();
    return NextResponse.json({ message: 'Database seeded successfully' });
  } catch (error) {
    console.error('Error seeding database:', error);
    return NextResponse.json(
      { error: 'Failed to seed database' },
      { status: 500 }
    );
  }
}
