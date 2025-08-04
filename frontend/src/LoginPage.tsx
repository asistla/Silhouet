// frontend/src/LoginPage.tsx
import React, { useState } from 'react';
import { Container, Form, Button, Card, Spinner } from 'react-bootstrap';

const API_URL = process.env.REACT_APP_API_URL || '/api';

interface LoginPageProps {
    onLogin: (publicKey: string) => void;
    onSwitchToRegister: (publicKey: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onSwitchToRegister }) => {
    const [publicKey, setPublicKey] = useState('');
    const [passphrase, setPassphrase] = useState('');
    const [step, setStep] = useState('key'); // 'key', 'passphrase', 'loading'
    const [error, setError] = useState('');

    const handleKeySubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (!publicKey.trim()) return;

        setStep('loading');
        try {
            const response = await fetch(`${API_URL}/users/check/${publicKey.trim()}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            if (data.exists) {
                setStep('passphrase');
            } else {
                onSwitchToRegister(publicKey.trim());
            }
        } catch (err) {
            setError('Failed to check public key. Please try again.');
            setStep('key');
        }
    };

    const handlePassphraseSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // The actual passphrase validation will happen in a future phase.
        // For now, we just proceed with the login.
        onLogin(publicKey.trim());
    };

    return (
        <Container className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
            <Card style={{ width: '30rem' }}>
                <Card.Body>
                    <Card.Title as="h2" className="text-center mb-4">
                        {step === 'passphrase' ? 'Enter Passphrase' : 'Login / Register'}
                    </Card.Title>
                    {error && <p className="text-danger text-center">{error}</p>}
                    
                    {step === 'loading' && (
                        <div className="text-center">
                            <Spinner animation="border" role="status">
                                <span className="visually-hidden">Loading...</span>
                            </Spinner>
                        </div>
                    )}

                    {step === 'key' && (
                        <Form onSubmit={handleKeySubmit}>
                            <Form.Group className="mb-3">
                                <Form.Label>Public Key</Form.Label>
                                <Form.Control
                                    type="text"
                                    placeholder="Enter your public key"
                                    value={publicKey}
                                    onChange={(e) => setPublicKey(e.target.value)}
                                    required
                                />
                                <Form.Text className="text-muted">
                                    Enter your key to login or begin registration.
                                </Form.Text>
                            </Form.Group>
                            <Button variant="primary" type="submit" className="w-100">
                                Continue
                            </Button>
                        </Form>
                    )}

                    {step === 'passphrase' && (
                        <Form onSubmit={handlePassphraseSubmit}>
                             <Form.Group className="mb-3">
                                <Form.Label>Public Key</Form.Label>
                                <Form.Control type="text" value={publicKey} readOnly />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Passphrase</Form.Label>
                                <Form.Control
                                    type="password"
                                    placeholder="Enter your passphrase"
                                    value={passphrase}
                                    onChange={(e) => setPassphrase(e.target.value)}
                                    required
                                />
                            </Form.Group>
                            <Button variant="primary" type="submit" className="w-100">
                                Login
                            </Button>
                        </Form>
                    )}
                </Card.Body>
            </Card>
        </Container>
    );
};

export default LoginPage;
