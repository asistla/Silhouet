import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Container, Row, Col, Form, Button, Navbar, Nav, Modal, Alert } from 'react-bootstrap';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { Country, State } from 'country-state-city';
import { ICountry } from 'country-state-city/lib/interface';
import { PERSONALITY_KEYS } from './config';
import LoginPage from './LoginPage';
import RegistrationPage from './RegistrationPage';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const API_BASE_URL = process.env.REACT_APP_API_URL || '';
const API_URL = `${API_BASE_URL}/api`;
const LOGOUT_DELAY = parseInt(process.env.REACT_APP_AUTO_LOGOUT_DELAY || '600000', 10);

// --- Type Definitions ---
interface Scores { [key: string]: number; }
interface Filters { [key: string]: string; }
interface User { user_id: string; public_key: string; }
interface AuthData extends User { token: string; }
interface NewUserInfo { user_id: string; public_key: string; created_at: string; }

type AppView = 'login' | 'register' | 'dashboard';

function App() {
    const [auth, setAuth] = useState<AuthData | null>(null);
    const [view, setView] = useState<AppView>('login');
    const [newUserInfo, setNewUserInfo] = useState<NewUserInfo | null>(null);
    const [userScores, setUserScores] = useState<Scores>({});
    const [cohortScores, setCohortScores] = useState<Scores>({});
    const [filters, setFilters] = useState<Filters>({ age_min: '', age_max: '', sex: '', gender: '', religion: '', ethnicity: '', pincode: '', city: '', district: '', state: '', country: '', nationality: '' });
    const [journalText, setJournalText] = useState('');
    const logoutTimer = useRef<NodeJS.Timeout | null>(null);

    const [selectedFilterCountry, setSelectedFilterCountry] = useState<ICountry | null>(null);
    const filterCountries = useMemo(() => Country.getAllCountries(), []);
    const filterStates = useMemo(() => selectedFilterCountry ? State.getStatesOfCountry(selectedFilterCountry.isoCode) : [], [selectedFilterCountry]);

    const getAuthHeaders = useCallback(() => {
        return auth ? { 'Authorization': `Bearer ${auth.token}` } : {};
    }, [auth]);

    const handleLogout = useCallback(() => {
        localStorage.removeItem('auth');
        setAuth(null);
        setView('login');
        if (logoutTimer.current) clearTimeout(logoutTimer.current);
    }, []);

    const resetLogoutTimer = useCallback(() => {
        if (logoutTimer.current) clearTimeout(logoutTimer.current);
        logoutTimer.current = setTimeout(handleLogout, LOGOUT_DELAY);
    }, [handleLogout]);

    const fetchUserScores = useCallback(async () => {
        if (!auth) return;
        try {
            const headers = getAuthHeaders();
            const response = await fetch(`${API_URL}/scores/me`, { 
            headers: headers.Authorization ? headers : undefined 
            });
            if (response.ok) setUserScores(await response.json());
            else setUserScores(PERSONALITY_KEYS.reduce((acc, key) => ({ ...acc, [`avg_${key}_score`]: 0.5 }), {}));
        } catch (error) { 
            console.error("Failed to fetch user scores:", error); 
        }
    }, [auth, getAuthHeaders]);

    useEffect(() => {
        const events = ['mousemove', 'keydown', 'mousedown', 'touchstart'];
        const resetTimer = () => { if (auth) resetLogoutTimer(); };
        if (auth) {
            events.forEach(event => window.addEventListener(event, resetTimer));
            resetLogoutTimer();
        }
        return () => {
            events.forEach(event => window.removeEventListener(event, resetTimer));
            if (logoutTimer.current) clearTimeout(logoutTimer.current);
        };
    }, [auth, resetLogoutTimer]);

    useEffect(() => {
        const storedAuth = localStorage.getItem('auth');
        if (storedAuth) {
            try {
                const foundAuth: AuthData = JSON.parse(storedAuth);
                setAuth(foundAuth);
                setView('dashboard');
            } catch (error) {
                console.error("Error parsing auth from localStorage", error);
                handleLogout();
            }
        }
    }, [handleLogout]);

    useEffect(() => {
        if (auth) {
            fetchUserScores();
        }
    }, [auth, fetchUserScores]);

    const handleLogin = async (publicKey: string, signature: string): Promise<boolean> => {
        try {
            const response = await fetch(`${API_URL}/users/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ public_key: publicKey, signature: signature })
            });
            if (response.ok) {
                const data = await response.json();
                const newAuth: AuthData = { user_id: data.user_id, public_key: data.public_key, token: data.access_token };
                localStorage.setItem('auth', JSON.stringify(newAuth));
                localStorage.setItem('last_user_pk', newAuth.public_key);
                setAuth(newAuth);
                setView('dashboard');
                return true;
            }
            return false;
        } catch (error) {
            console.error("Login API call failed:", error);
            return false;
        }
    };

    const handleRegistration = async (registrationData: any) => {
        try {
            const regResponse = await fetch(`${API_URL}/users/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(registrationData)
            });
    
            if (regResponse.ok) {
                const newUser: NewUserInfo = await regResponse.json();
                setNewUserInfo(newUser);
                // Automatically log the user in after registration
                const loginSuccess = await handleLogin(registrationData.public_key, registrationData.signature);
                if (!loginSuccess) {
                    // This part is tricky, as login requires a new challenge.
                    // For now, we will just show the registration success and let them log in manually.
                    setView('login'); 
                }
            } else {
                const errorData = await regResponse.json();
                alert(`Registration failed: ${errorData.detail || 'Please try again.'}`);
            }
        } catch (error) {
            console.error("Registration API call failed:", error);
            alert("Registration failed due to a network error.");
        }
    };

const handleJournalSubmit = async () => {
    if (!auth || !journalText) return;
    
    const authHeaders = getAuthHeaders();
    const headers = {
        'Content-Type': 'application/json',
        ...(authHeaders.Authorization && { Authorization: authHeaders.Authorization })
    };
    
    const response = await fetch(`${API_URL}/posts/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ raw_text: journalText })
    });
    
    if (response.ok) {
        setJournalText('');
        setTimeout(fetchUserScores, 2000); // Re-fetch scores after a delay
    } else {
        alert("Failed to submit journal entry.");
    }
};
    
    // Other handlers (filter change, apply filters, etc.) remain largely the same
    const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));

        if (name === 'country') {
            const country = filterCountries.find(c => c.isoCode === value);
            setSelectedFilterCountry(country || null);
            setFilters(prev => ({ ...prev, state: '' }));
        }
    };

    const handleApplyFilters = async () => {
        const query = Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''));
        const response = await fetch(`${API_URL}/scores/filtered`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(query)
        });
        if (response.ok) setCohortScores(await response.json());
        else {
            setCohortScores({});
            alert("Could not fetch data for the selected cohort.");
        }
    };

    const closeKeyModal = () => {
        setNewUserInfo(null);
        setView('login'); // After registration, guide user to login
    }

    if (view === 'login') return <LoginPage onLogin={handleLogin} onSwitchToRegister={() => setView('register')} />;
    if (view === 'register') return <RegistrationPage onRegister={handleRegistration} />;

    const chartData = {
        labels: PERSONALITY_KEYS.map(key => key.replace(/_/g, ' ')),
        datasets: [
            { label: 'My Scores', data: PERSONALITY_KEYS.map(key => userScores[`avg_${key}_score`] || 0.5), backgroundColor: 'rgba(199, 0, 57, 0.8)' },
            { label: 'Cohort Scores', data: PERSONALITY_KEYS.map(key => cohortScores[`avg_${key}_score`] || 0.5), backgroundColor: 'rgba(165, 138, 120, 0.7)' },
        ],
    };

    const chartOptions = {
        indexAxis: 'y' as const,
        scales: { x: { min: -1, max: 1 } },
        maintainAspectRatio: false
    };

    return (
        <>
            <Modal show={!!newUserInfo} onHide={closeKeyModal} backdrop="static" keyboard={false}>
                <Modal.Header><Modal.Title>Registration Successful!</Modal.Title></Modal.Header>
                <Modal.Body>
                    <Alert variant="success">Please proceed to the login page to sign in with your new identity.</Alert>
                    <Form.Group className="mb-3">
                        <Form.Label>Your Public Key</Form.Label>
                        <Form.Control as="textarea" rows={4} value={newUserInfo?.public_key} readOnly />
                    </Form.Group>
                </Modal.Body>
                <Modal.Footer><Button variant="primary" onClick={closeKeyModal}>Go to Login</Button></Modal.Footer>
            </Modal>

            <Navbar expand="lg" className="mb-4">
                <Container>
                    <Navbar.Brand href="#">Silhouet</Navbar.Brand>
                    <Navbar.Toggle aria-controls="basic-navbar-nav" />
                    <Navbar.Collapse id="basic-navbar-nav" className="justify-content-end">
                        <Nav><Button variant="outline-light" onClick={handleLogout}>Logout</Button></Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>
            <Container fluid>
                <Row className="filter-bar">
                    {/* Filter Controls */}
                    {Object.keys(filters).map(key => (
                        <Col md={2} key={key} className="mb-2">
                            <Form.Group>
                                <Form.Label>{key.replace(/_/g, ' ')}</Form.Label>
                                <Form.Control type={key.includes('age') ? 'number' : 'text'} name={key} value={filters[key]} onChange={handleFilterChange} />
                            </Form.Group>
                        </Col>
                    ))}
                    <Col md={12} className="d-flex justify-content-end mt-2"><Button onClick={handleApplyFilters}>Apply Filters</Button></Col>
                </Row>
                <Row>
                    <Col md={4} className="journal-section">
                        <h2>Journal</h2>
                        <Form.Control as="textarea" rows={10} value={journalText} onChange={(e) => setJournalText(e.target.value)} placeholder="Write your thoughts here..." />
                        <Button className="mt-2 w-100" onClick={handleJournalSubmit}>Submit</Button>
                    </Col>
                    <Col md={8} className="scores-section">
                        <h2>Personality Scores</h2>
                        <div className="chart-container"><Bar data={chartData} options={chartOptions as any} /></div>
                    </Col>
                </Row>
            </Container>
        </>
    );
}

export default App;
