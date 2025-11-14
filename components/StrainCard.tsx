'use client';

interface Pharmacy {
  id: string;
  name: string;
  city: string | null;
  inStock: boolean;
  price: number | null;
}

interface Strain {
  id: string;
  name: string;
  thcContent: number | null;
  cbdContent: number | null;
  description: string | null;
  genetics: string | null;
  score: number;
  matchingEffects: string[];
  matchingConditions: string[];
  availablePharmacies: Pharmacy[];
}

interface StrainCardProps {
  strain: Strain;
}

export default function StrainCard({ strain }: StrainCardProps) {
  return (
    <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-700 dark:to-gray-800 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-600">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
          {strain.name}
        </h3>
        <span className="bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-0.5 rounded dark:bg-green-900 dark:text-green-300">
          Score: {strain.score}
        </span>
      </div>

      {strain.description && (
        <p className="text-gray-600 dark:text-gray-300 text-sm mb-3">
          {strain.description}
        </p>
      )}

      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="bg-white dark:bg-gray-600 rounded p-2 text-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">THC</div>
          <div className="text-sm font-semibold text-gray-800 dark:text-white">
            {strain.thcContent !== null ? `${strain.thcContent}%` : 'N/A'}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-600 rounded p-2 text-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">CBD</div>
          <div className="text-sm font-semibold text-gray-800 dark:text-white">
            {strain.cbdContent !== null ? `${strain.cbdContent}%` : 'N/A'}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-600 rounded p-2 text-center">
          <div className="text-xs text-gray-500 dark:text-gray-400">Typ</div>
          <div className="text-sm font-semibold text-gray-800 dark:text-white">
            {strain.genetics || 'N/A'}
          </div>
        </div>
      </div>

      {strain.matchingEffects.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Wirkungen:
          </h4>
          <div className="flex flex-wrap gap-1">
            {strain.matchingEffects.map((effect, idx) => (
              <span
                key={idx}
                className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded dark:bg-green-900 dark:text-green-300"
              >
                {effect}
              </span>
            ))}
          </div>
        </div>
      )}

      {strain.matchingConditions.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
            Beschwerden:
          </h4>
          <div className="flex flex-wrap gap-1">
            {strain.matchingConditions.map((condition, idx) => (
              <span
                key={idx}
                className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded dark:bg-blue-900 dark:text-blue-300"
              >
                {condition}
              </span>
            ))}
          </div>
        </div>
      )}

      {strain.availablePharmacies.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
            Verfügbar in {strain.availablePharmacies.length} Apotheke(n):
          </h4>
          <div className="space-y-1">
            {strain.availablePharmacies.slice(0, 3).map((pharmacy) => (
              <div
                key={pharmacy.id}
                className="flex justify-between items-center text-xs bg-gray-100 dark:bg-gray-600 rounded px-2 py-1"
              >
                <span className="text-gray-700 dark:text-gray-300">
                  {pharmacy.name} {pharmacy.city && `(${pharmacy.city})`}
                </span>
                {pharmacy.price && (
                  <span className="font-semibold text-green-600 dark:text-green-400">
                    ~{pharmacy.price.toFixed(0)}€
                  </span>
                )}
              </div>
            ))}
            {strain.availablePharmacies.length > 3 && (
              <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                +{strain.availablePharmacies.length - 3} weitere
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
