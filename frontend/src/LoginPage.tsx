// frontend/src/LoginPage.tsx
import React, { useState } from 'react';
import { Container, Form, Button, Card } from 'react-bootstrap';

interface LoginPageProps {
    onLogin: (publicKey: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
    const [publicKey, setPublicKey] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (publicKey.trim()) {
            onLogin(publicKey.trim());
        }
    };

    return (
        <Container className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
            <Card style={{ width: '30rem' }}>
                <Card.Body>
                    <Card.Title as="h2" className="text-center mb-4">Login / Register</Card.Title>
                    <Form onSubmit={handleSubmit}>
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
                                If the key does not exist, a new user will be created.
                            </Form.Text>
                        </Form.Group>
                        <Button variant="primary" type="submit" className="w-100">
                            Continue
                        </Button>
                    </Form>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default LoginPage;
