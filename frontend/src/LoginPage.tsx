import React, { useState, useEffect } from 'react';
import { Alert } from 'react-bootstrap';
import styled from 'styled-components';
import { decryptPrivateKey, signMessage } from './crypto';
import { AuthContainer, StyledButton } from './components/StyledComponents';

interface LoginPageProps {
    onLogin: (publicKey: string, signature: string) => Promise<boolean>;
    onSwitchToRegister: () => void;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || '';
const API_URL = `${API_BASE_URL}/api`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
`;

const Label = styled.label`
  display: block;
  margin-bottom: ${({ theme }) => theme.spacing(1)};
  font-family: ${({ theme }) => theme.font.familySerif};
  color: ${({ theme }) => theme.colors.accent};
  text-transform: uppercase;
  font-size: 0.9rem;
  letter-spacing: 1px;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  background-color: ${({ theme }) => theme.colors.paper};
  color: ${({ theme }) => theme.colors.textOnPaper};
  border: 1px solid ${({ theme }) => theme.colors.accent};
  border-radius: 4px;
  font-family: ${({ theme }) => theme.font.family};
  &:focus {
    border-color: ${({ theme }) => theme.colors.accent2};
    box-shadow: 0 0 5px ${({ theme }) => theme.colors.accent};
    outline: none;
  }
`;

const Textarea = styled.textarea`
  width: 100%;
  padding: 12px;
  min-height: 80px;
  resize: vertical;
  background-color: ${({ theme }) => theme.colors.paper};
  color: ${({ theme }) => theme.colors.textOnPaper};
  border: 1px solid ${({ theme }) => theme.colors.accent};
  border-radius: 4px;
  font-family: ${({ theme }) => theme.font.family};
  &:focus {
    border-color: ${({ theme }) => theme.colors.accent2};
    box-shadow: 0 0 5px ${({ theme }) => theme.colors.accent};
    outline: none;
  }
`;

const LinkButton = styled.button`
  background: none;
  border: none;
  color: ${({ theme }) => theme.colors.accent};
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
  margin-top: 1rem;
  display: block;
  width: 100%;
  text-align: center;
  font-family: ${({ theme }) => theme.font.familySerif};
`;

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
            <div>
                <h2 style={{ textAlign: 'center', fontFamily: 'Garamond, serif', color: '#c5b358', marginBottom: '2rem' }}>
                    Enter the Study
                </h2>
                
                {error && <Alert variant="danger">{error}</Alert>}
                
                <form onSubmit={handleLoginSubmit}>
                    <FormGroup>
                        <Label>Public Key</Label>
                        <Textarea
                            placeholder="Your public key"
                            value={publicKey}
                            onChange={(e) => setPublicKey(e.target.value)}
                            required
                            disabled={isLoading}
                        />
                    </FormGroup>

                    <FormGroup>
                        <Label>Passphrase</Label>
                        <Input
                            type="password"
                            placeholder="Your passphrase"
                            value={passphrase}
                            onChange={(e) => setPassphrase(e.target.value)}
                            required
                            disabled={isLoading}
                        />
                    </FormGroup>

                    {isLoading ? (
                        <div style={{ textAlign: 'center' }}>
                            <p>Authenticating...</p>
                        </div>
                    ) : (
                        <>
                            <StyledButton type="submit" style={{ width: '100%' }}>
                                Login
                            </StyledButton>
                            <LinkButton type="button" onClick={onSwitchToRegister}>
                                New user? Create an identity
                            </LinkButton>
                        </>
                    )}
                </form>
            </div>
        </AuthContainer>
    );
};

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

export default LoginPage;
