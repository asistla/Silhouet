import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Form, Button, Navbar } from 'react-bootstrap';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import { PERSONALITY_KEYS } from './config';
import LoginPage from './LoginPage'; // Import the LoginPage component

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const API_URL = process.env.REACT_APP_API_URL || '/api';

// --- Type Definitions ---
interface Scores {
    [key: string]: number;
}

interface Filters {
    [key: string]: string;
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

function App() {
    const [user, setUser] = useState<User | null>(null);
    const [userScores, setUserScores] = useState<Scores>({});
    const [cohortScores, setCohortScores] = useState<Scores>({});
    const [filters, setFilters] = useState<Filters>({
        age_min: '',
        age_max: '',
        sex: '',
        gender: '',
        religion: '',
        ethnicity: '',
        pincode: '',
        city: '',
        district: '',
        state: '',
        country: '',
        nationality: '',
    });
    const [journalText, setJournalText] = useState('');
    const socket = useRef<WebSocket | null>(null);

    useEffect(() => {
        const loggedInUser = localStorage.getItem('user');
        if (loggedInUser) {
            const foundUser = JSON.parse(loggedInUser);
            setUser(foundUser);
        }
    }, []);

    useEffect(() => {
        if (!user) return;

        const fetchUserScores = async () => {
            const response = await fetch(`${API_URL}/users/${user.user_id}`);
            const data = await response.json();
            const scores: Scores = {};
            PERSONALITY_KEYS.forEach(key => {
                scores[key] = data[`avg_${key}_score`];
            });
            setUserScores(scores);
        };
        fetchUserScores();

        socket.current = new WebSocket(`${API_URL.replace('http', 'ws')}/ws/${user.user_id}`);
        socket.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.user_id === user.user_id) {
                const updatedScores: Scores = {};
                PERSONALITY_KEYS.forEach(key => {
                    updatedScores[key] = data.scores[`avg_${key}_score`];
                });
                setUserScores(updatedScores);
            }
        };

        return () => {
            socket.current?.close();
        };
    }, [user]);

    const handleLogin = async (publicKey: string) => {
        const response = await fetch(`${API_URL}/users/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                public_key: publicKey,
                // Provide default values for other fields for new users
                pincode: "00000",
                city: "Unknown",
                district: "Unknown",
                state: "Unknown",
                country: "Unknown",
                nationality: "Unknown"
            })
        });
        if (response.ok) {
            const userData = await response.json();
            const loggedInUser = { user_id: userData.user_id, public_key: userData.public_key };
            localStorage.setItem('user', JSON.stringify(loggedInUser));
            setUser(loggedInUser);
        } else {
            alert("Login failed. Please try again.");
        }
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
            const scores: Scores = {};
            PERSONALITY_KEYS.forEach(key => {
                scores[key] = data[`avg_${key}_score`];
            });
            setCohortScores(scores);
        } else {
            setCohortScores({});
            alert("Could not fetch data for the selected cohort.");
        }
    };

    const handleJournalSubmit = async () => {
        if (!user || !journalText) return;
        await fetch(`${API_URL}/posts/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.user_id, raw_text: journalText })
        });
        setJournalText('');
    };

    if (!user) {
        return <LoginPage onLogin={handleLogin} />;
    }

    const chartData = {
        labels: PERSONALITY_KEYS,
        datasets: [
            {
                label: 'My Scores',
                data: PERSONALITY_KEYS.map(key => userScores[key] || 0),
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
            },
            {
                label: 'Cohort Scores',
                data: PERSONALITY_KEYS.map(key => cohortScores[key] || 0),
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
            },
        ],
    };

    const chartOptions = {
        indexAxis: 'y' as const,
        scales: {
            x: {
                min: -1,
                max: 1,
            },
        },
        maintainAspectRatio: false,
    };

    return (
        <>
            <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
                <Container>
                    <Navbar.Brand href="#">Silhouet</Navbar.Brand>
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