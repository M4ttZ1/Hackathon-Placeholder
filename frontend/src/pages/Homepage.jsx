import { useState } from 'react';

// --- Sub-component for the score card (No changes) ---
const ScoreCard = ({ score, label }) => {
    const getScoreColor = (s) => {
        if (s >= 70) return 'text-red-400';
        if (s >= 40) return 'text-yellow-400';
        return 'text-green-400';
    };
    const getLabelClasses = (l) => {
        if (l === 'high_risk') return 'bg-red-500/20 text-red-300 ring-red-500/30';
        if (l === 'suspicious') return 'bg-yellow-500/20 text-yellow-300 ring-yellow-500/30';
        return 'bg-green-500/20 text-green-300 ring-green-500/30';
    };
    return (
        <div className="bg-slate-800/50 rounded-lg p-6 text-center">
            <div className={`font-bold text-7xl ${getScoreColor(score)}`}>{score}</div>
            <div className="text-slate-400 mt-1">Risk Score</div>
            <div className={`mt-4 inline-block px-3 py-1 text-sm font-semibold rounded-full ring-1 ${getLabelClasses(label)}`}>
                {label.replace('_', ' ').toUpperCase()}
            </div>
        </div>
    );
};

// --- UPDATED: This component now displays BOTH reasons and similar examples ---
const EvidenceSection = ({ reasons, examples, isInsufficientData }) => (
    <div>
        <h3 className="text-lg font-semibold text-slate-300 mb-3">Evidence Found</h3>
        
        {isInsufficientData ? (
            // Display message for insufficient data
            <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                <p className="text-slate-400 text-sm">Not enough data to analyze. Please provide more text or a URL/link.</p>
            </div>
        ) : (
            <>
                {/* Heuristic Reasons (as badges) */}
                <div className="flex flex-wrap gap-2 mb-6">
                    {reasons.map((reason, i) => (
                        <span key={i} className="bg-slate-700 text-slate-300 px-3 py-1 rounded-full text-sm">
                            {reason}
                        </span>
                    ))}
                </div>

                {/* Similar Examples from Faiss (as cards) */}
                {examples && examples.length > 0 && (
                    <div>
                         <h4 className="text-md font-semibold text-slate-400 mb-3">Similar Examples from Dataset:</h4>
                         <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {examples.map((example, i) => (
                                <div key={i} className="bg-slate-800/50 rounded-lg p-4 ring-1 ring-slate-700">
                                    <p className={`text-sm font-bold ${example.label === 'phishing' ? 'text-red-400' : 'text-green-400'}`}>
                                        {example.label === 'phishing' ? 'Similar Phishing Example' : 'Similar Benign Example'}
                                    </p>
                                    <p className="text-slate-400 mt-2 text-sm italic line-clamp-3">
                                        "{example.text}"
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </>
        )}
    </div>
);

// --- Main Page Component ---
export default function HomePage() {
    const [text, setText] = useState('');
    const [result, setResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null); 

    // Helper function to check if text contains a URL/link
    const containsLink = (text) => {
        const urlRegex = /(https?:\/\/[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?)/i;
        return urlRegex.test(text);
    };

    // Helper function to count words
    const countWords = (text) => {
        return text.trim().split(/\s+/).filter(word => word.length > 0).length;
    };

    const handleAnalyze = async () => {
        if (!text.trim()) return;
        
        const wordCount = countWords(text);
        const hasLink = containsLink(text);
        
        // Check if input is insufficient (less than 5 words and no link)
        if (wordCount < 5 && !hasLink) {
            setResult({
                score: 0,
                label: 'low_risk',
                reasons: [],
                similar_examples: [],
                insufficient_data: true
            });
            setError(null);
            return;
        }

        setIsLoading(true);
        setResult(null);
        setError(null);

        try {
            const response = await fetch('http://127.0.0.1:8000/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            setResult({ ...data, insufficient_data: false });

        } catch (err) {
            console.error("Failed to fetch:", err);
            setError("Could not connect to the analysis server. Please make sure it's running and try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-slate-900 text-white min-h-screen font-sans">
            <div className="container mx-auto p-4 sm:p-8 max-w-4xl">
                <header className="text-center mb-8">
                    <h1 className="text-4xl font-bold">OmniLens</h1>
                    <p className="text-slate-400 mt-2">Paste any suspicious Email, SMS, or message to analyze its risk.</p>
                </header>

                <main>
                    <div className="bg-slate-800 p-4 rounded-lg shadow-lg">
                        <textarea
                            id="text-input"
                            name="text-input"
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="Your package has been held at our warehouse..."
                            className="w-full h-40 p-3 bg-slate-900 rounded-md border border-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                        />
                        <div className="mt-4 flex justify-end">
                            <button
                                onClick={handleAnalyze}
                                disabled={isLoading}
                                className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-bold py-2 px-6 rounded-lg transition-colors"
                            >
                                {isLoading ? 'Analyzing...' : 'Analyze'}
                            </button>
                        </div>
                    </div>
                    
                    {error && (
                        <div className="mt-8 text-center text-red-400 bg-red-500/10 p-4 rounded-lg">
                            <p><strong>Error:</strong> {error}</p>
                        </div>
                    )}

                    {result && (
                        <div className="mt-8 space-y-8">
                            <ScoreCard score={result.score} label={result.label} />
                            <EvidenceSection 
                                reasons={result.reasons} 
                                examples={result.similar_examples} 
                                isInsufficientData={result.insufficient_data}
                            />
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}