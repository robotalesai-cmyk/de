'use client';

import { useState, useEffect } from 'react';
import StrainCard from './StrainCard';

interface Effect {
  id: string;
  name: string;
}

interface Condition {
  id: string;
  name: string;
}

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

export default function StrainFinder() {
  const [effects, setEffects] = useState<Effect[]>([]);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [selectedEffects, setSelectedEffects] = useState<string[]>([]);
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<Strain[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [maxThc, setMaxThc] = useState<number>(25);
  const [minCbd, setMinCbd] = useState<number>(0);
  const [genetics, setGenetics] = useState<string>('');
  const [city, setCity] = useState<string>('');

  useEffect(() => {
    loadEffectsAndConditions();
  }, []);

  async function loadEffectsAndConditions() {
    try {
      const [effectsRes, conditionsRes] = await Promise.all([
        fetch('/api/effects'),
        fetch('/api/conditions'),
      ]);

      if (effectsRes.ok) {
        const effectsData = await effectsRes.json();
        setEffects(effectsData);
      }

      if (conditionsRes.ok) {
        const conditionsData = await conditionsRes.json();
        setConditions(conditionsData);
      }
    } catch (error) {
      console.error('Error loading effects and conditions:', error);
    }
  }

  async function handleSearch() {
    setLoading(true);
    try {
      const preferences = {
        preferredEffects: selectedEffects,
        conditions: selectedConditions,
        maxThc: showAdvanced ? maxThc : undefined,
        minCbd: showAdvanced ? minCbd : undefined,
        genetics: showAdvanced && genetics ? genetics : undefined,
        location: showAdvanced && city ? { city } : undefined,
      };

      const response = await fetch('/api/recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });

      if (response.ok) {
        const data = await response.json();
        setRecommendations(data);
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  }

  function toggleEffect(effectName: string) {
    setSelectedEffects((prev) =>
      prev.includes(effectName)
        ? prev.filter((e) => e !== effectName)
        : [...prev, effectName]
    );
  }

  function toggleCondition(conditionName: string) {
    setSelectedConditions((prev) =>
      prev.includes(conditionName)
        ? prev.filter((c) => c !== conditionName)
        : [...prev, conditionName]
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
          Suche nach Wirkung & Beschwerden
        </h2>

        <div className="space-y-6">
          {/* Effects Selection */}
          <div>
            <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3">
              Gewünschte Wirkungen
            </h3>
            <div className="flex flex-wrap gap-2">
              {effects.map((effect) => (
                <button
                  key={effect.id}
                  onClick={() => toggleEffect(effect.name)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    selectedEffects.includes(effect.name)
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  {effect.name}
                </button>
              ))}
            </div>
          </div>

          {/* Conditions Selection */}
          <div>
            <h3 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3">
              Beschwerden
            </h3>
            <div className="flex flex-wrap gap-2">
              {conditions.map((condition) => (
                <button
                  key={condition.id}
                  onClick={() => toggleCondition(condition.name)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    selectedConditions.includes(condition.name)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  {condition.name}
                </button>
              ))}
            </div>
          </div>

          {/* Advanced Options */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-green-600 dark:text-green-400 hover:underline text-sm font-medium"
            >
              {showAdvanced ? '▼' : '▶'} Erweiterte Optionen
            </button>

            {showAdvanced && (
              <div className="mt-4 space-y-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Max. THC-Gehalt: {maxThc}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="30"
                    value={maxThc}
                    onChange={(e) => setMaxThc(Number(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Min. CBD-Gehalt: {minCbd}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="25"
                    value={minCbd}
                    onChange={(e) => setMinCbd(Number(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Genetik
                  </label>
                  <select
                    value={genetics}
                    onChange={(e) => setGenetics(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-600 dark:border-gray-500 dark:text-white"
                  >
                    <option value="">Alle</option>
                    <option value="Indica">Indica</option>
                    <option value="Sativa">Sativa</option>
                    <option value="Hybrid">Hybrid</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Stadt
                  </label>
                  <input
                    type="text"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    placeholder="z.B. Berlin"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md dark:bg-gray-600 dark:border-gray-500 dark:text-white dark:placeholder-gray-400"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Search Button */}
          <button
            onClick={handleSearch}
            disabled={loading || (selectedEffects.length === 0 && selectedConditions.length === 0)}
            className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Suche läuft...' : 'Empfehlungen finden'}
          </button>
        </div>
      </div>

      {/* Results */}
      {recommendations.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
            Empfohlene Sorten ({recommendations.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((strain) => (
              <StrainCard key={strain.id} strain={strain} />
            ))}
          </div>
        </div>
      )}

      {!loading && recommendations.length === 0 && (selectedEffects.length > 0 || selectedConditions.length > 0) && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            Keine passenden Sorten gefunden. Versuchen Sie andere Suchkriterien.
          </p>
        </div>
      )}
    </div>
  );
}
