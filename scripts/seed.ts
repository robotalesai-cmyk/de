import { seedDatabase } from '../lib/fetcher';
import { prisma } from '../lib/prisma';

async function main() {
  try {
    await seedDatabase();
    
    // Verify seed operation completed successfully
    const strainCount = await prisma.strain.count();
    const pharmacyCount = await prisma.pharmacy.count();
    
    console.log(`✓ Verification: ${strainCount} strains and ${pharmacyCount} pharmacies in database`);
    
    if (strainCount === 0 || pharmacyCount === 0) {
      throw new Error('Seed verification failed: No data found in database');
    }
    
    process.exit(0);
  } catch (error) {
    console.error('Error seeding database:', error);
    process.exit(1);
  }
}

main();
