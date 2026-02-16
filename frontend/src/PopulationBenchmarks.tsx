import React, { useState, useEffect } from 'react';
import * as d3 from 'd3';
import { feature } from 'topojson-client';

interface BenchmarkData {
    state: string;
    value: number;
}

const PopulationBenchmarks: React.FC = () => {
    const [measure, setMeasure] = useState('Maternal Mortality');
    const [data, setData] = useState<BenchmarkData[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedState, setSelectedState] = useState<string | null>(null);

    useEffect(() => {
        fetchData();
    }, [measure]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const response = await fetch(`/api/v1/benchmarks/ahr?measure=${encodeURIComponent(measure)}`);
            const results = await response.json();
            setData(results);
        } catch (err) {
            console.error('Failed to fetch benchmark data', err);
        }
        setLoading(false);
    };

    return (
        <div className="p-6 bg-white rounded-xl shadow-lg">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">U.S. Population Benchmarks</h2>
                <select
                    value={measure}
                    onChange={(e) => setMeasure(e.target.value)}
                    className="p-2 border rounded-md"
                >
                    <option>Maternal Mortality</option>
                    <option>Preterm Birth</option>
                    <option>Low Birthweight</option>
                    <option>Severe Maternal Morbidity</option>
                </select>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-gray-50 p-4 rounded-lg min-h-[400px] flex items-center justify-center">
                    {/* US Map Placeholder - Real implementation would use D3 + us-atlas */}
                    <div className="text-gray-400 text-center">
                        <p className="text-6xl mb-4">🗺️</p>
                        <p>US Choropleth Map: {measure}</p>
                        <p className="text-sm">(D3 Map rendering would target this container)</p>
                    </div>
                </div>

                <div className="bg-white border p-4 rounded-lg">
                    <h3 className="font-semibold mb-4 text-gray-700">Disparity Insights: {selectedState || 'National'}</h3>
                    <div className="space-y-4">
                        {/* Mock Disparity Chart */}
                        {['White', 'Black', 'Hispanic', 'Asian'].map(race => (
                            <div key={race}>
                                <div className="flex justify-between text-xs mb-1">
                                    <span>{race}</span>
                                    <span>{Math.floor(Math.random() * 50)}%</span>
                                </div>
                                <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
                                    <div
                                        className="bg-blue-500 h-full"
                                        style={{ width: `${Math.random() * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="mt-8 pt-6 border-t">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Model vs. Population</h4>
                        <div className="flex items-end gap-2 h-24">
                            <div className="flex-1 bg-blue-100 rounded-t-md relative group">
                                <div className="absolute inset-0 bg-blue-400 opacity-20 rounded-t-md h-[40%]" />
                                <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px]">Model</span>
                            </div>
                            <div className="flex-1 bg-green-100 rounded-t-md relative">
                                <div className="absolute inset-0 bg-green-400 opacity-20 rounded-t-md h-[60%]" />
                                <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px]">Actual</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PopulationBenchmarks;
