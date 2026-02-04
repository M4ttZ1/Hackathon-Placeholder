import { useState, useEffect, useRef } from 'react';
import BackgroundElements from '../components/BackgroundElements';

const ScoreCard = ({ score, label }) => {
    const getScoreColor = (s) => {
        if (s >= 70) return 'text-red-600';  // High risk (70+)
        if (s >= 40) return 'text-yellow-400';  // Suspicious (40-69)
        if (s >= 10) return 'text-blue-400';  // Low risk (10-39)
        return 'text-green-400';  // Benign (0-9)
    };
    const getLabelClasses = (l) => {
        if (l === 'confirmed_phishing') return 'bg-red-700/30 text-red-200 ring-red-700/50 animate-pulse';
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
    const [lowDetail, setLowDetail] = useState(() => {
        return localStorage.getItem('omnilensLowDetail') === 'true';
    });

    // PERFORMANCE: Use ref to avoid recreating effect on every lowDetail change
    const lowDetailRef = useRef(lowDetail);
    useEffect(() => {
        lowDetailRef.current = lowDetail;
    }, [lowDetail]);

    useEffect(() => {
        const handleStorageChange = () => {
            setLowDetail(localStorage.getItem('omnilensLowDetail') === 'true');
        };
        window.addEventListener('storage', handleStorageChange);
        
        // PERFORMANCE: Keep 100ms interval (no behavior change), but use ref to avoid closure issues
        const interval = setInterval(() => {
            const current = localStorage.getItem('omnilensLowDetail') === 'true';
            if (current !== lowDetailRef.current) {
                setLowDetail(current);
            }
        }, 100);
        
        return () => {
            window.removeEventListener('storage', handleStorageChange);
            clearInterval(interval);
        };
    }, []); // Empty deps - effect runs once

    const handleAnalyze = async () => {
        if (!text.trim()) return;
        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/analyze`, {
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

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        if (!file.name.endsWith('.eml')) {
            setError('Please upload a .eml file.');
            return;
        }

        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) throw new Error('Network response was not ok.');
            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError('Failed to analyze file. The backend might be down.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    if (lowDetail) {
        // Plain original version
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
                                placeholder="Your package has been held at our warehouse..."
                                className="w-full h-40 p-3 bg-slate-900 rounded-md border border-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none text-white"
                            />
                            <div className="mt-4 flex justify-end gap-3">
                                <input
                                    type="file"
                                    accept=".eml"
                                    onChange={handleFileUpload}
                                    disabled={isLoading}
                                    className="hidden"
                                    id="file-upload"
                                />
                                <label
                                    htmlFor="file-upload"
                                    className={`bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 px-6 rounded-lg transition-colors cursor-pointer ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                                >
                                    {isLoading ? 'Uploading...' : 'Upload .eml'}
                                </label>
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
                                {result.reasons?.length > 0 && <ReasonBadges reasons={result.reasons} />}
                                {result.neighbors && result.neighbors.length > 0 && <Neighbors neighbors={result.neighbors} />}
                            </div>
                        )}
                    </main>
                </div>
            </div>
        );
    }

    // Fancy version with animations
    return (
        <div className="text-white min-h-screen font-sans">
            <BackgroundElements />
            <div className="container mx-auto p-4 sm:p-8 max-w-4xl relative z-10">
                <header className="text-center mb-8">
                    <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-300 via-blue-400 to-cyan-300 bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(56,189,248,0.6)]">
                        OmniLens
                    </h1>
                    <p className="text-slate-300 mt-3 text-lg font-medium">Real-time AI security scanner for suspicious messages</p>
                    <p className="text-slate-400 mt-1 text-sm">Detects phishing, scams, and malicious intent in seconds</p>
                </header>
                <main>
                    <div className="scanner-card bg-white/5 border border-white/10 p-6 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.35)] relative">
                        <div className="scanner-card-border-shimmer"></div>
                        <div className="relative" style={{ position: 'relative', zIndex: 2 }}>
                            <div className="relative">
                                <textarea
                                    value={text}
                                    onChange={(e) => setText(e.target.value)}
                                    placeholder="Paste suspicious content here..."
                                    className="w-full h-40 p-4 bg-black/30 rounded-xl border border-cyan-400/20 focus:ring-2 focus:ring-cyan-400/60 focus:outline-none resize-none placeholder:text-slate-500 text-white transition-all duration-300 caret-cyan-400 shadow-inner"
                                />
                                <div className="absolute bottom-3 left-4 capability-indicator pointer-events-none">
                                    Email • SMS • URLs • Attachments
                                </div>
                                <div className="absolute bottom-3 right-4 capability-indicator pointer-events-none">
                                    Pattern + ML Analysis
                                </div>
                            </div>
                            <div className="mt-4 flex justify-end gap-3">
                            <input
                                type="file"
                                accept=".eml"
                                onChange={handleFileUpload}
                                disabled={isLoading}
                                className="hidden"
                                id="file-upload"
                            />
                            <label
                                htmlFor="file-upload"
                                className={`bg-white/10 hover:bg-white/15 text-white font-semibold py-2 px-6 rounded-xl transition-all cursor-pointer border border-cyan-400/20 hover:border-cyan-400/40 backdrop-blur-sm ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-[0_0_20px_rgba(56,189,248,0.3)]'}`}
                            >
                                {isLoading ? 'Uploading...' : 'Upload .eml'}
                            </label>
                            <button
                                onClick={handleAnalyze}
                                disabled={isLoading}
                                className="analyze-button disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-bold py-2 px-8 rounded-xl transition-colors"
                            >
                                {isLoading ? 'Analyzing...' : 'Analyze'}
                            </button>
                            </div>
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