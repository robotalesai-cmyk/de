import { seedDatabase } from '../lib/fetcher';

async function main() {
  try {
    await seedDatabase();
    process.exit(0);
  } catch (error) {
    console.error('Error seeding database:', error);
    process.exit(1);
  }
}

main();
