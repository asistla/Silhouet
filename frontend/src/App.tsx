import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Container, Row, Col, Form, Button, Navbar, Nav } from 'react-bootstrap';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import { PERSONALITY_KEYS } from './config';
import LoginPage from './LoginPage';
import RegistrationPage from './RegistrationPage';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const API_BASE_URL = process.env.REACT_APP_API_URL || '';
const API_URL = `${API_BASE_URL}/api`;
const LOGOUT_DELAY = parseInt(process.env.REACT_APP_AUTO_LOGOUT_DELAY || '60000', 10);

// --- Type Definitions ---
interface Scores {
    [key: string]: number;
}

interface Filters {
    [key:string]: string;
    age_min: string;
    age_max: string;
    sex: string;
    gender: string;
    religion: string;
    ethnicity: string;
    pincode: string;
    city: string;
    district: string;
    state: string;
    country: string;
    nationality: string;
}

interface User {
    user_id: string;
    public_key: string;
}

type AppView = 'login' | 'register' | 'dashboard';

function App() {
    const [user, setUser] = useState<User | null>(null);
    const [view, setView] = useState<AppView>('login');
    const [publicKeyForRegistration, setPublicKeyForRegistration] = useState('');
    const [userScores, setUserScores] = useState<Scores>({});
    const [cohortScores, setCohortScores] = useState<Scores>({});
    const [filters, setFilters] = useState<Filters>({
        age_min: '', age_max: '', sex: '', gender: '', religion: '',
        ethnicity: '', pincode: '', city: '', district: '',
        state: '', country: '', nationality: '',
    });
    const [journalText, setJournalText] = useState('');
    const logoutTimer = useRef<NodeJS.Timeout | null>(null);

    const handleLogout = useCallback(() => {
        localStorage.removeItem('user');
        setUser(null);
        setView('login');
        if (logoutTimer.current) {
            clearTimeout(logoutTimer.current);
        }
    }, []);

    const resetLogoutTimer = useCallback(() => {
        if (logoutTimer.current) {
            clearTimeout(logoutTimer.current);
        }
        logoutTimer.current = setTimeout(handleLogout, LOGOUT_DELAY);
    }, [handleLogout]);

    const fetchUserScores = useCallback(async (publicKey: string) => {
        try {
            const response = await fetch(`${API_URL}/scores/${publicKey}`);
            if (response.ok) {
                const data = await response.json();
                console.log(data)
                setUserScores(data);
            } else {
                // Initialize scores if user not found or has no scores
                const initialScores: Scores = {};
                PERSONALITY_KEYS.forEach(key => {
                    initialScores[`avg_${key}_score`] = 0.5;
                });
                setUserScores(initialScores);
            }
        } catch (error) {
            console.error("Failed to fetch user scores:", error);
        }
    }, []);

    useEffect(() => {
        const events = ['mousemove', 'keydown', 'mousedown', 'touchstart'];
        const resetTimer = () => {
            if (user) resetLogoutTimer();
        };

        if (user) {
            events.forEach(event => window.addEventListener(event, resetTimer));
            resetLogoutTimer();
        }

        return () => {
            events.forEach(event => window.removeEventListener(event, resetTimer));
            if (logoutTimer.current) clearTimeout(logoutTimer.current);
        };
    }, [user, resetLogoutTimer]);

    useEffect(() => {
        const loggedInUser = localStorage.getItem('user');
        if (loggedInUser) {
            try {
                const foundUser = JSON.parse(loggedInUser);
                setUser(foundUser);
                setView('dashboard');
                fetchUserScores(foundUser.public_key);
            } catch (error) {
                console.error("Error parsing user from localStorage", error);
                handleLogout();
            }
        }
    }, [fetchUserScores, handleLogout]);

    const handleLogin = async (publicKey: string) => {
        const response = await fetch(`${API_URL}/users/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ public_key: publicKey })
        });
        if (response.ok) {
            const userData = await response.json();
            const loggedInUser = { user_id: userData.user_id, public_key: userData.public_key };
            localStorage.setItem('user', JSON.stringify(loggedInUser));
            setUser(loggedInUser);
            setView('dashboard');
            fetchUserScores(loggedInUser.public_key);
        } else {
            alert("Login failed. The public key might not exist.");
        }
    };
    
    const handleRegistration = async (registrationData: any) => {
        const response = await fetch(`${API_URL}/users/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(registrationData)
        });
        if (response.ok) {
            const userData = await response.json();
            const loggedInUser = { user_id: userData.user_id, public_key: userData.public_key };
            localStorage.setItem('user', JSON.stringify(loggedInUser));
            setUser(loggedInUser);
            setView('dashboard');
            fetchUserScores(loggedInUser.public_key);
        } else {
            alert("Registration failed. Please try again.");
        }
    };

    const handleSwitchToRegister = (publicKey: string) => {
        setPublicKeyForRegistration(publicKey);
        setView('register');
    };

    const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFilters({ ...filters, [e.target.name]: e.target.value });
    };

    const handleApplyFilters = async () => {
        const query = Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''));
        const response = await fetch(`${API_URL}/scores/filtered`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(query)
        });
        if (response.ok) {
            const data = await response.json();
            setCohortScores(data);
        } else {
            setCohortScores({});
            alert("Could not fetch data for the selected cohort.");
        }
    };

    const handleJournalSubmit = async () => {
        if (!user || !journalText) return;
        const response = await fetch(`${API_URL}/posts/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.user_id, raw_text: journalText })
        });
        if (response.ok) {
            setJournalText('');
            // Wait a moment for backend processing, then fetch updated scores
            setTimeout(() => fetchUserScores(user.public_key), 2000);
        } else {
            alert("Failed to submit journal entry.");
        }
    };

    if (view === 'login') {
        return <LoginPage onLogin={handleLogin} onSwitchToRegister={handleSwitchToRegister} />;
    }

    if (view === 'register') {
        return <RegistrationPage onRegister={handleRegistration} publicKey={publicKeyForRegistration} />;
    }

    const chartData = {
        labels: PERSONALITY_KEYS,
        datasets: [
            {
                label: 'My Scores',
                data: PERSONALITY_KEYS.map(key => userScores[`avg_${key}_score`] || 0.5),
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
            },
            {
                label: 'Cohort Scores',
                data: PERSONALITY_KEYS.map(key => cohortScores[`avg_${key}_score`] || 0.5),
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
            },
        ],
    };

    const chartOptions = {
        indexAxis: 'y' as const,
        scales: { x: { min: -1, max: 1 } },
        maintainAspectRatio: false,
    };

    return (
        <>
            <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
                <Container>
                    <Navbar.Brand href="#">Silhouet</Navbar.Brand>
                    <Navbar.Toggle />
                    <Navbar.Collapse className="justify-content-end">
                        <Nav>
                            <Button variant="outline-light" onClick={handleLogout}>Logout</Button>
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
            <Container fluid>
                <Row className="mb-3">
                    {Object.keys(filters).map(key => (
                        <Col md={2} key={key}>
                            <Form.Group>
                                <Form.Label>{key.replace(/_/g, ' ')}</Form.Label>
                                <Form.Control
                                    type={key.includes('age') ? 'number' : 'text'}
                                    name={key}
                                    value={filters[key]}
                                    onChange={handleFilterChange}
                                />
                            </Form.Group>
                        </Col>
                    ))}
                    <Col md={2} className="d-flex align-items-end">
                        <Button onClick={handleApplyFilters}>Apply Filters</Button>
                    </Col>
                </Row>
                <Row>
                    <Col md={4}>
                        <h2>Journal</h2>
                        <Form.Control
                            as="textarea"
                            rows={15}
                            value={journalText}
                            onChange={(e) => setJournalText(e.target.value)}
                            placeholder="Write your thoughts here..."
                        />
                        <Button className="mt-2" onClick={handleJournalSubmit}>Submit</Button>
                    </Col>
                    <Col md={8}>
                        <h2>Personality Scores</h2>
                        <div style={{ height: '80vh' }}>
                            <Bar data={chartData} options={chartOptions} />
                        </div>
                    </Col>
                </Row>
            </Container>
        </>
    );
}

export default App;
