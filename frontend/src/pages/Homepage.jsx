import { useState } from 'react';

// Sub-component for the score card
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

// Sub-component for the reason badges
const ReasonBadges = ({ reasons }) => (
    <div>
        <h3 className="text-lg font-semibold text-slate-300 mb-3">Evidence Found</h3>
        <div className="flex flex-wrap gap-2">
            {reasons.map((reason, i) => (
                <span key={i} className="bg-slate-700 text-slate-300 px-3 py-1 rounded-full text-sm">
          {reason}
        </span>
            ))}
        </div>
    </div>
);

// Main Page Component
export default function HomePage() {
    const [text, setText] = useState('');
    const [result, setResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null); 

    const handleAnalyze = async () => {
        console.log("1. 'Analyze' button clicked. Starting handleAnalyze function.");

        if (!text.trim()) {
            console.log("Input text is empty. Aborting.");
            return;
        }
        
        setIsLoading(true);
        setResult(null);
        setError(null);

        console.log("2. Preparing to send text to backend:", { text });

        try {
            const response = await fetch('http://127.0.0.1:8000/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text }),
            });

            console.log("3. Received response from server:", response);

            if (!response.ok) {
                // This will be caught by the .catch() block below
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            console.log("4. Successfully parsed JSON data:", data);
            setResult(data);

        } catch (err) {
            // This block runs if the fetch fails or if we throw an error above
            console.error("5. An error occurred during the API call:", err);
            setError("Could not connect to the analysis server. Please make sure it's running and try again.");
        } finally {
            // This block runs regardless of success or failure
            console.log("6. API call finished. Setting isLoading to false.");
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
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="Paste any email or message here."
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
                            <ReasonBadges reasons={result.reasons} />
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}

