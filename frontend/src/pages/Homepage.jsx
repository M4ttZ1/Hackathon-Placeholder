// frontend/src/pages/HomePage.jsx
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

    const handleAnalyze = async () => {
        if (!text.trim()) return;
        setIsLoading(true);
        setResult(null);

        // --- MOCK DATA ---
        // Instead of a real API call, we define a fake response object here.
        const mockData = {
            score: 85,
            label: "high_risk",
            reasons: [
                "Urgency language detected: 'act now'",
                "Contains a shortened URL",
                "Requests payment via gift card",
                "High similarity to known phishing scams"
            ],
        };

        // We use a timeout to simulate the delay of a real network request.
        await new Promise(resolve => setTimeout(resolve, 800));

        setResult(mockData);
        setIsLoading(false);
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
                placeholder="Your package has been held at our warehouse. Please follow the instructions here: http://bit.ly/xyz to reschedule delivery. Act now to avoid fees."
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