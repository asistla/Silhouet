// frontend/src/RegistrationPage.tsx
import React, { useState } from 'react';
import { Container, Form, Button, Card, Row, Col } from 'react-bootstrap';

interface RegistrationPageProps {
    onRegister: (userData: any) => void;
    publicKey: string;
}

const RegistrationPage: React.FC<RegistrationPageProps> = ({ onRegister, publicKey }) => {
    const [formData, setFormData] = useState({
        public_key: publicKey,
        passphrase: '',
        age: '',
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

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // Basic validation
        if (formData.passphrase.trim() && formData.pincode.trim()) {
            onRegister(formData);
        } else {
            alert('Please fill in all required fields.');
        }
    };

    return (
        <Container className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
            <Card style={{ width: '50rem' }}>
                <Card.Body>
                    <Card.Title as="h2" className="text-center mb-4">Create New User</Card.Title>
                    <Form onSubmit={handleSubmit}>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Public Key</Form.Label>
                                    <Form.Control type="text" value={formData.public_key} readOnly />
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Passphrase</Form.Label>
                                    <Form.Control
                                        type="password"
                                        name="passphrase"
                                        placeholder="Create a passphrase"
                                        value={formData.passphrase}
                                        onChange={handleChange}
                                        required
                                    />
                                </Form.Group>
                            </Col>
                        </Row>
                        <Row>
                            {Object.keys(formData).filter(k => k !== 'public_key' && k !== 'passphrase').map(key => (
                                <Col md={4} key={key}>
                                    <Form.Group className="mb-3">
                                        <Form.Label>{key.charAt(0).toUpperCase() + key.slice(1)}</Form.Label>
                                        <Form.Control
                                            type={key === 'age' ? 'number' : 'text'}
                                            name={key}
                                            placeholder={`Enter ${key}`}
                                            value={formData[key as keyof typeof formData]}
                                            onChange={handleChange}
                                            required
                                        />
                                    </Form.Group>
                                </Col>
                            ))}
                        </Row>
                        <Button variant="primary" type="submit" className="w-100 mt-3">
                            Register
                        </Button>
                    </Form>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default RegistrationPage;
