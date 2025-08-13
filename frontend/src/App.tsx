import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Modal, Alert } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

import { Country, State } from 'country-state-city';
import { ICountry } from 'country-state-city/lib/interface';
import { PERSONALITY_KEYS } from './config';

import { ReactComponent as Logo } from './logo.svg';
import LoginPage from './LoginPage';
import RegistrationPage from './RegistrationPage';
import ScoreChart from './components/ScoreChart';
import { MainContainer, LeftPanel, CenterPanel, RightPanel, TextArea, StyledButton, LogoutButton, LogoContainer } from './components/StyledComponents';
import { FilterPanel } from './components/ui/FilterPanel';
import { AdSlot } from './components/ui/AdSlot';
import InsightSlot from './components/ui/InsightSlot';


const API_BASE_URL = process.env.REACT_APP_API_URL || '';
const API_URL = `${API_BASE_URL}/api`;
const LOGOUT_DELAY = parseInt(process.env.REACT_APP_AUTO_LOGOUT_DELAY || '600000', 10);
 
interface Scores { [key: string]: number; }
interface Filters { [key: string]: string; }
interface User { user_id: string; public_key: string; }
interface AuthData extends User { token: string; }
interface NewUserInfo { user_id: string; public_key: string; created_at: string; }

type AppView = 'login' | 'register' | 'dashboard';

function App({ toggleTheme, isDark }: { toggleTheme: () => void; isDark: boolean }) {
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

    const getAuthHeaders = useCallback(() => auth ? { 'Authorization': `Bearer ${auth.token}` } : {}, [auth]);

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
            const response = await fetch(`${API_URL}/scores/me`, { headers: headers.Authorization ? headers : undefined });
            if (response.ok) setUserScores(await response.json());
            else setUserScores(PERSONALITY_KEYS.reduce((acc, key) => ({ ...acc, [`avg_${key}_score`]: 0 }), {}));
        } catch (error) { console.error("Failed to fetch user scores:", error); }
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

    useEffect(() => { if (auth) fetchUserScores(); }, [auth, fetchUserScores]);

    const handleLogin = async (publicKey: string, signature: string): Promise<boolean> => {
        try {
            const response = await fetch(`${API_URL}/users/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ public_key: publicKey, signature })
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
                setView('login');
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
        const headers = { 'Content-Type': 'application/json', ...(authHeaders.Authorization && { Authorization: authHeaders.Authorization }) };
        const response = await fetch(`${API_URL}/posts/`, { method: 'POST', headers, body: JSON.stringify({ raw_text: journalText }) });
        if (response.ok) {
            setJournalText('');
            setTimeout(fetchUserScores, 2000);
        } else {
            alert("Failed to submit journal entry.");
        }
    };

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

    const closeKeyModal = () => setNewUserInfo(null);

    const renderView = () => {
        switch (view) {
            case 'login':
                return <LoginPage onLogin={handleLogin} onSwitchToRegister={() => setView('register')} />;
            case 'register':
                return <RegistrationPage onRegister={handleRegistration} />;
            case 'dashboard':
                return (
                    <MainContainer>
                        <StyledButton 
                          onClick={toggleTheme} 
                          style={{ position: 'absolute', top: '2rem', left: '2rem', zIndex: 10 }}>
                            {isDark ? 'Light Mode' : 'Dark Mode'}
                        </StyledButton>
                        <LogoutButton onClick={handleLogout}>Logout</LogoutButton>
                        <LeftPanel>
                            <LogoContainer><Logo className="logo-svg" /></LogoContainer>
                            <FilterPanel filters={filters} onChange={handleFilterChange} onApply={handleApplyFilters} />
                        </LeftPanel>
                        <CenterPanel>
                            <h2>Journal</h2>
                            <TextArea value={journalText} onChange={(e: any) => setJournalText(e.target.value)} placeholder="The page is yours..." />
                            <StyledButton onClick={handleJournalSubmit} style={{ marginTop: '1rem', width: '100%' }}>Submit</StyledButton>
                            <AdSlot position="journal_footer" />
                        </CenterPanel>
                        <RightPanel>
                          <div className="ad-slot">
                            <AdSlot title="Ad" content="Sample Ad Content" callToAction="Click Here" />
                          </div>
                          <div className="insight-slot">
                            <InsightSlot text="Sample insight text"/>
                          </div>
                            <h2>Your Silhouette</h2>
                            <ScoreChart userScores={userScores} cohortScores={cohortScores} />
                        </RightPanel>
                    </MainContainer>
                );
            default:
                return <LoginPage onLogin={handleLogin} onSwitchToRegister={() => setView('register')} />;
        }
    };

    return (
        <>
            <Modal show={!!newUserInfo} onHide={closeKeyModal} centered>
                <Modal.Header>
                    <Modal.Title>Registration Successful!</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Alert variant="success">Your new identity has been created. Please proceed to the login page to sign in.</Alert>
                    <p>Your Public Key (Saved to Local Storage)</p>
                    <textarea rows={4} value={newUserInfo?.public_key} readOnly />
                </Modal.Body>
                <Modal.Footer>
                    <StyledButton onClick={closeKeyModal}>Go to Login</StyledButton>
                </Modal.Footer>
            </Modal>
            {renderView()}
        </>
    );
}

export default App;
