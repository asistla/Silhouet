import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Container, Row, Col, Form, Button, Navbar, Nav, Modal, Alert } from 'react-bootstrap';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css'; // Import custom CSS
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
interface Filters {
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
    [key:string]: string;
}
interface User { user_id: string; public_key: string; }
interface NewUserInfo { user_id: string; public_key: string; created_at: string; }

type AppView = 'login' | 'register' | 'dashboard';

function App() {
    const [user, setUser] = useState<User | null>(null);
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

    const handleLogout = useCallback(() => {
        localStorage.removeItem('user');
        setUser(null);
        setView('login');
        if (logoutTimer.current) clearTimeout(logoutTimer.current);
    }, []);

    const resetLogoutTimer = useCallback(() => {
        if (logoutTimer.current) clearTimeout(logoutTimer.current);
        logoutTimer.current = setTimeout(handleLogout, LOGOUT_DELAY);
    }, [handleLogout]);

    const fetchUserScores = useCallback(async (publicKey: string) => {
        try {
            const response = await fetch(`${API_URL}/scores/${publicKey}`);
            if (response.ok) setUserScores(await response.json());
            else setUserScores(PERSONALITY_KEYS.reduce((acc, key) => ({ ...acc, [`avg_${key}_score`]: 0.5 }), {}));
        } catch (error) { console.error("Failed to fetch user scores:", error); }
    }, []);

    useEffect(() => {
        const events = ['mousemove', 'keydown', 'mousedown', 'touchstart'];
        const resetTimer = () => { if (user) resetLogoutTimer(); };
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

    const handleLogin = async (publicKey: string, signature: string): Promise<boolean> => {
        try {
            const response = await fetch(`${API_URL}/users/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ public_key: publicKey, signature: signature })
            });
            if (response.ok) {
                const userData = await response.json();
                const loggedInUser = { user_id: userData.user_id, public_key: userData.public_key };
                localStorage.setItem('user', JSON.stringify(loggedInUser));
                localStorage.setItem('last_user_pk', loggedInUser.public_key);
                setUser(loggedInUser);
                setView('dashboard');
                fetchUserScores(loggedInUser.public_key);
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error("Login API call failed:", error);
            return false;
        }
    };

    const handleRegistration = async (registrationData: any) => {
        try {
            const response = await fetch(`${API_URL}/users/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(registrationData)
            });
    
            if (response.ok) {
                const newUser: NewUserInfo = await response.json();
                setNewUserInfo(newUser);
                const loggedInUser = { user_id: newUser.user_id, public_key: newUser.public_key };
                localStorage.setItem('user', JSON.stringify(loggedInUser));
                setUser(loggedInUser);
                fetchUserScores(loggedInUser.public_key);
            } else {
                const errorData = await response.json();
                alert(`Registration failed: ${errorData.detail || 'Please try again.'}`);
            }
        } catch (error) {
            console.error("Registration API call failed:", error);
            alert("Registration failed due to a network error.");
        }
    };

    const handleSwitchToRegister = () => setView('register');

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

    const handleJournalSubmit = async () => {
        if (!user || !journalText) return;
        const response = await fetch(`${API_URL}/posts/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.user_id, raw_text: journalText })
        });
        if (response.ok) {
            setJournalText('');
            setTimeout(() => fetchUserScores(user.public_key), 2000);
        } else {
            alert("Failed to submit journal entry.");
        }
    };

    const closeKeyModal = () => {
        setNewUserInfo(null);
        setView('dashboard');
    }

    if (view === 'login') return <LoginPage onLogin={handleLogin} onSwitchToRegister={handleSwitchToRegister} />;
    if (view === 'register') return <RegistrationPage onRegister={handleRegistration} />;

    const chartData = {
        labels: PERSONALITY_KEYS.map(key => key.replace(/_/g, ' ')),
        datasets: [
            { 
                label: 'My Scores', 
                data: PERSONALITY_KEYS.map(key => userScores[`avg_${key}_score`] || 0.5), 
                backgroundColor: 'rgba(199, 0, 57, 0.8)', // Deep Magenta
                borderColor: 'rgba(199, 0, 57, 1)',
                borderWidth: 1
            },
            { 
                label: 'Cohort Scores', 
                data: PERSONALITY_KEYS.map(key => cohortScores[`avg_${key}_score`] || 0.5), 
                backgroundColor: 'rgba(165, 138, 120, 0.7)', // Light Sepia
                borderColor: 'rgba(165, 138, 120, 1)',
                borderWidth: 1
            },
        ],
    };

    const chartOptions = {
        indexAxis: 'y' as const,
        scales: {
            x: {
                min: -1,
                max: 1,
                ticks: { color: '#F5F5F5' },
                grid: { color: 'rgba(112, 84, 70, 0.3)' }
            },
            y: {
                ticks: { color: '#F5F5F5', font: { size: 10 } },
                grid: { color: 'rgba(112, 84, 70, 0.3)' }
            }
        },
        plugins: {
            legend: {
                labels: { color: '#F5F5F5' }
            },
            tooltip: {
                titleFont: { size: 14 },
                bodyFont: { size: 12 },
            }
        },
        maintainAspectRatio: false
    };

    return (
        <>
            <Modal show={!!newUserInfo} onHide={closeKeyModal} backdrop="static" keyboard={false}>
                <Modal.Header><Modal.Title>Registration Successful!</Modal.Title></Modal.Header>
                <Modal.Body>
                    <Alert variant="success"><strong>Your new identity has been created!</strong></Alert>
                    <p>Your private key has been encrypted with your passphrase and stored securely in this browser's local storage. <strong>Do not lose your passphrase.</strong></p>
                    <Form.Group className="mb-3">
                        <Form.Label>Your Public Key</Form.Label>
                        <Form.Control as="textarea" rows={4} value={newUserInfo?.public_key} readOnly />
                        <Form.Text>This is your public identifier. You can share it safely.</Form.Text>
                    </Form.Group>
                </Modal.Body>
                <Modal.Footer><Button variant="primary" onClick={closeKeyModal}>Proceed to Dashboard</Button></Modal.Footer>
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
                    {['age_min', 'age_max', 'religion', 'ethnicity', 'pincode', 'city', 'district', 'nationality'].map(key => (
                        <Col md={2} key={key} className="mb-2"><Form.Group><Form.Label>{key.replace(/_/g, ' ')}</Form.Label><Form.Control type={key.includes('age') ? 'number' : 'text'} name={key} value={filters[key]} onChange={handleFilterChange} /></Form.Group></Col>
                    ))}
                    <Col md={2} className="mb-2"><Form.Group><Form.Label>Sex</Form.Label><Form.Select name="sex" value={filters.sex} onChange={handleFilterChange}><option value="">Any</option><option value="Male">Male</option><option value="Female">Female</option><option value="Other">Other</option></Form.Select></Form.Group></Col>
                    <Col md={2} className="mb-2"><Form.Group><Form.Label>Gender</Form.Label><Form.Select name="gender" value={filters.gender} onChange={handleFilterChange}><option value="">Any</option><option value="Man">Man</option><option value="Woman">Woman</option><option value="Other">Other</option></Form.Select></Form.Group></Col>
                    <Col md={2} className="mb-2"><Form.Group><Form.Label>Country</Form.Label><Form.Select name="country" value={filters.country} onChange={handleFilterChange}><option value="">Any</option>{filterCountries.map(c => <option key={c.isoCode} value={c.isoCode}>{c.name}</option>)}</Form.Select></Form.Group></Col>
                    <Col md={2} className="mb-2"><Form.Group><Form.Label>State</Form.Label><Form.Select name="state" value={filters.state} onChange={handleFilterChange} disabled={!selectedFilterCountry}><option value="">Any</option>{filterStates.map(s => <option key={s.isoCode} value={s.isoCode}>{s.name}</option>)}</Form.Select></Form.Group></Col>
                    
                    <Col md={12} className="d-flex justify-content-end mt-2"><Button onClick={handleApplyFilters}>Apply Filters</Button></Col>
                </Row>
                <Row>
                    <Col md={4} className="journal-section">
                        <h2>Journal</h2>
                        <Form.Control as="textarea" value={journalText} onChange={(e) => setJournalText(e.target.value)} placeholder="Write your thoughts here..." />
                        <Button className="mt-2 w-100" onClick={handleJournalSubmit}>Submit</Button>
                    </Col>
                    <Col md={8} className="scores-section">
                        <h2>Personality Scores</h2>
                        <div className="chart-container"><Bar data={chartData} options={chartOptions} /></div>
                    </Col>
                </Row>
            </Container>
        </>
    );
}

export default App;
