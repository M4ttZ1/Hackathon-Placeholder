// frontend/src/App.jsx
import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/Homepage';
import GetStarted from './pages/GetStarted';

function App() {
    return (
        <Routes>
            <Route path="/" element={<GetStarted />} />
            <Route path="/home" element={<HomePage />} />
        </Routes>
    );
}

export default App;