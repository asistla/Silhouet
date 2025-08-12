import React, { useState, useEffect } from 'react';
import { Alert } from 'react-bootstrap';
import { decryptPrivateKey, signMessage } from './crypto';
import { AuthContainer } from './components/StyledComponents';
import { StyledButton } from './components/StyledComponents';

interface LoginPageProps {
    onLogin: (publicKey: string, signature: string) => Promise<boolean>;
    onSwitchToRegister: () => void;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || '';
const API_URL = `${API_BASE_URL}/api`;

const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px',
    marginBottom: '1rem',
    backgroundColor: '#f5f5dc',
    color: '#3d3d3d',
    border: '1px solid #c5b358',
    borderRadius: '4px',
    fontFamily: 'Georgia, serif',
};

const linkStyle: React.CSSProperties = {
    background: 'none',
    border: 'none',
    color: '#c5b358',
    textDecoration: 'underline',
    cursor: 'pointer',
    padding: '0',
    marginTop: '1rem',
    display: 'block',
    width: '100%',
    textAlign: 'center'
};

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onSwitchToRegister }) => {
    const [publicKey, setPublicKey] = useState('');
    const [passphrase, setPassphrase] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
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
            const encryptedPrivateKeyB64 = localStorage.getItem(`user_pk_${publicKey}`);
            if (!encryptedPrivateKeyB64) {
                throw new Error("No private key found for this public key. Make sure you are on the correct device/browser or register a new identity.");
            }

            const privateKey = decryptPrivateKey(encryptedPrivateKeyB64, passphrase);
            if (!privateKey) {
                throw new Error("Invalid passphrase. Could not decrypt private key.");
            }

            const challengeResponse = await fetch(`${API_URL}/auth/challenge`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ public_key: publicKey }),
            });

            if (!challengeResponse.ok) {
                throw new Error("Could not get authentication challenge from server. User may not exist.");
            }
            const { challenge } = await challengeResponse.json();

            const signature = signMessage(challenge, privateKey);

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
        <AuthContainer>
            <h2 style={{ textAlign: 'center', fontFamily: 'Garamond, serif', color: '#c5b358', marginBottom: '2rem' }}>
                Enter the Study
            </h2>
            
            {error && <Alert variant="danger">{error}</Alert>}
            
            <form onSubmit={handleLoginSubmit}>
                <label style={{ marginBottom: '0.5rem', display: 'block' }}>Public Key</label>
                <textarea
                    style={{ ...inputStyle, minHeight: '80px', resize: 'vertical' }}
                    placeholder="Your public key"
                    value={publicKey}
                    onChange={(e) => setPublicKey(e.target.value)}
                    required
                    disabled={isLoading}
                />

                <label style={{ marginBottom: '0.5rem', display: 'block' }}>Passphrase</label>
                <input
                    type="password"
                    style={inputStyle}
                    placeholder="Your passphrase"
                    value={passphrase}
                    onChange={(e) => setPassphrase(e.target.value)}
                    required
                    disabled={isLoading}
                />

                {isLoading ? (
                    <div style={{ textAlign: 'center' }}>
                        <p>Authenticating...</p>
                    </div>
                ) : (
                    <>
                        <StyledButton type="submit" style={{ width: '100%' }}>
                            Login
                        </StyledButton>
                        <button type="button" onClick={onSwitchToRegister} style={linkStyle}>
                            New user? Create an identity
                        </button>
                    </>
                )}
            </form>
        </AuthContainer>
    );
};

export default LoginPage;