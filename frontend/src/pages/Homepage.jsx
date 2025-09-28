import { useState } from 'react';

const ScoreCard = ({ score, label }) => {
    const getScoreColor = (s) => {
        if (s >= 50) return 'text-red-400';
        if (s >= 20) return 'text-yellow-400';
        if (s > 0) return 'text-blue-400';
        return 'text-green-400';
    };
    const getLabelClasses = (l) => {
        if (l === 'high_risk') return 'bg-red-500/20 text-red-300 ring-red-500/30';
        if (l === 'suspicious') return 'bg-yellow-500/20 text-yellow-300 ring-yellow-500/30';
        if (l === 'low_risk') return 'bg-blue-500/20 text-blue-300 ring-blue-500/30';
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

const Neighbors = ({ neighbors }) => (
    <div>
        <h3 className="text-lg font-semibold text-slate-300 mb-3">Similar Known Samples</h3>
        <div className="space-y-3">
            {neighbors.map((n, i) => (
                <div key={i} className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
                    <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-blue-400">{n.label.replace('_', ' ').toUpperCase()}</span>
                        <span className="text-sm text-slate-400">{(n.similarity * 100).toFixed(0)}% Match</span>
                    </div>
                    <p className="text-sm text-slate-500 bg-slate-900/50 p-2 rounded">{n.text}</p>
                </div>
            ))}
        </div>
    </div>
);

export default function HomePage() {
    const [text, setText] = useState('');
    const [result, setResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleAnalyze = async () => {
        if (!text.trim()) return;
        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch(import.meta.env.VITE_API_URL + '/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text }),
            });
            if (!response.ok) throw new Error('Network response was not ok.');
            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError('Failed to analyze. The backend might be down.');
            console.error(err);
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
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="Paste content here..."
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

                    {error && <div className="mt-6 bg-red-900/50 text-red-300 p-4 rounded-lg text-center">{error}</div>}

                    {result && (
                        <div className="mt-8 space-y-8">
                            <ScoreCard score={result.score} label={result.label} />
                            {result.reasons?.length > 0 && <ReasonBadges reasons={result.reasons} />}
                            {result.neighbors && result.neighbors.length > 0 && <Neighbors neighbors={result.neighbors} />}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}