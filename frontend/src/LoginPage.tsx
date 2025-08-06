// frontend/src/LoginPage.tsx
import React, { useState, useEffect } from 'react';
import { Container, Form, Button, Card, Spinner, Alert } from 'react-bootstrap';
import { decryptPrivateKey, signMessage } from './crypto';

interface LoginPageProps {
    onLogin: (publicKey: string, signature: string) => Promise<boolean>;
    onSwitchToRegister: () => void;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || '';
const API_URL = `${API_BASE_URL}/api`;

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onSwitchToRegister }) => {
    const [publicKey, setPublicKey] = useState('');
    const [passphrase, setPassphrase] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        // Pre-fill public key if it exists in localStorage
        const lastUsedPk = localStorage.getItem('last_user_pk');
        if (lastUsedPk) {
            setPublicKey(lastUsedPk);
        }
    }, []);

    const handleLoginSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        if (!publicKey.trim() || !passphrase.trim()) {
            setError("Public Key and Passphrase are required.");
            return;
        }
        setIsLoading(true);

        try {
            // 1. Get encrypted private key from localStorage
            const encryptedPrivateKeyB64 = localStorage.getItem(`user_pk_${publicKey}`);
            if (!encryptedPrivateKeyB64) {
                throw new Error("No private key found for this public key. Make sure you are on the correct device/browser or register a new identity.");
            }

            // 2. Decrypt private key
            const privateKey = decryptPrivateKey(encryptedPrivateKeyB64, passphrase);
            if (!privateKey) {
                throw new Error("Invalid passphrase. Could not decrypt private key.");
            }

            // 3. Fetch challenge from the backend
            const challengeResponse = await fetch(`${API_URL}/auth/challenge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ public_key: publicKey }),
            });

            if (!challengeResponse.ok) {
                throw new Error("Could not get authentication challenge from server. User may not exist.");
            }
            const { challenge } = await challengeResponse.json();

            // 4. Sign the challenge
            const signature = signMessage(challenge, privateKey);

            // 5. Attempt login with signature
            const loginSuccess = await onLogin(publicKey, signature);
            if (!loginSuccess) {
                 throw new Error("Login failed. The server rejected the authentication signature.");
            }

        } catch (err: any) {
            setError(err.message || "An unknown error occurred.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Container className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
            <Card style={{ width: '30rem' }}>
                <Card.Body>
                    <Card.Title as="h2" className="text-center mb-4">Login</Card.Title>
                    {error && <Alert variant="danger">{error}</Alert>}
                    
                    <Form onSubmit={handleLoginSubmit}>
                        <Form.Group className="mb-3">
                            <Form.Label>Public Key</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={3}
                                placeholder="Enter your public key"
                                value={publicKey}
                                onChange={(e) => setPublicKey(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Passphrase</Form.Label>
                            <Form.Control
                                type="password"
                                placeholder="Enter your passphrase"
                                value={passphrase}
                                onChange={(e) => setPassphrase(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                        </Form.Group>

                        {isLoading ? (
                            <div className="text-center">
                                <Spinner animation="border" role="status">
                                    <span className="visually-hidden">Loading...</span>
                                </Spinner>
                            </div>
                        ) : (
                            <>
                                <Button variant="primary" type="submit" className="w-100">
                                    Login
                                </Button>
                                <Button variant="link" onClick={onSwitchToRegister} className="w-100 mt-2">
                                    New user? Go to Register
                                </Button>
                            </>
                        )}
                    </Form>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default LoginPage;
