import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const city = searchParams.get('city') || '';

    const pharmacies = await prisma.pharmacy.findMany({
      where: city
        ? {
            city: {
              contains: city,
              mode: 'insensitive'
            }
          }
        : undefined,
      include: {
        strains: {
          include: {
            strain: true
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });

    return NextResponse.json(pharmacies);
  } catch (error) {
    console.error('Error fetching pharmacies:', error);
    return NextResponse.json(
      { error: 'Failed to fetch pharmacies' },
      { status: 500 }
    );
  }
}
