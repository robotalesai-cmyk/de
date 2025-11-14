import StrainFinder from '@/components/StrainFinder';
import Disclaimer from '@/components/Disclaimer';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <main className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-green-800 dark:text-green-400 mb-2">
            Cannabis Apotheken Finder
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Finden Sie medizinische Cannabis-Sorten nach Wirkung und Beschwerden
          </p>
        </header>

        <Disclaimer />
        
        <div className="mt-8">
          <StrainFinder />
        </div>

        <footer className="mt-16 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>
            Alle Daten stammen aus öffentlich zugänglichen, legalen Quellen.
          </p>
          <p className="mt-2">
            Diese Anwendung dient nur zu Informationszwecken. Konsultieren Sie
            immer einen Arzt für medizinische Beratung.
          </p>
        </footer>
      </main>
    </div>
  );
}
