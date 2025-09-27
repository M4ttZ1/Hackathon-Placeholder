// frontend/src/App.jsx
import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import GetStarted from './pages/GetStarted';
import './App.css'; // You can remove this line if App.css is empty

function App() {
    return (
        <Routes>
            <Route path="/" element={<GetStarted />} />
            <Route path="/home" element={<HomePage />} />
        </Routes>
    );
}

export default App;