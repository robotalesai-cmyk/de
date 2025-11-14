import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const search = searchParams.get('search') || '';
    if (search.length > 100) {
      return NextResponse.json({ error: 'Search term too long' }, { status: 400 });
    }

    const strains = await prisma.strain.findMany({
      where: search
        ? {
            name: {
              contains: search,
              mode: 'insensitive'
            }
          }
        : undefined,
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
          }
        }
      },
      orderBy: {
        name: 'asc'
      }
    });

    return NextResponse.json(strains);
  } catch (error) {
    console.error('Error fetching strains:', error);
    return NextResponse.json(
      { error: 'Failed to fetch strains' },
      { status: 500 }
    );
  }
}
