// frontend/src/RegistrationPage.tsx
import React, { useState, useMemo } from 'react';
import { Container, Form, Button, Card, Row, Col, Alert } from 'react-bootstrap';
import { Country, State } from 'country-state-city';
import { ICountry } from 'country-state-city/lib/interface';
import { generateKeyPair, encryptPrivateKey } from './crypto';
import { encodeBase64 } from 'tweetnacl-util';

interface RegistrationPageProps {
    onRegister: (userData: any) => void;
}

const RegistrationPage: React.FC<RegistrationPageProps> = ({ onRegister }) => {
    const [formData, setFormData] = useState({
        passphrase: '',
        confirmPassphrase: '',
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
    const [error, setError] = useState('');

    const [selectedCountry, setSelectedCountry] = useState<ICountry | null>(null);

    const countries = useMemo(() => Country.getAllCountries(), []);
    const states = useMemo(() => selectedCountry ? State.getStatesOfCountry(selectedCountry.isoCode) : [], [selectedCountry]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });

        if (name === 'country') {
            const country = countries.find(c => c.isoCode === value);
            setSelectedCountry(country || null);
            setFormData(prev => ({ ...prev, state: '' }));
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (formData.passphrase !== formData.confirmPassphrase) {
            setError("Passphrases do not match.");
            return;
        }
        if (formData.passphrase.length < 8) {
            setError("Passphrase must be at least 8 characters long.");
            return;
        }

        try {
            // 1. Generate key pair
            const keyPair = generateKeyPair();
            const publicKeyB64 = encodeBase64(keyPair.publicKey);
            
            // 2. Encrypt private key with passphrase
            const encryptedPrivateKeyB64 = encryptPrivateKey(keyPair.secretKey, formData.passphrase);

            // 3. Store keys in localStorage
            localStorage.setItem(`user_pk_${publicKeyB64}`, encryptedPrivateKeyB64);
            localStorage.setItem('last_user_pk', publicKeyB64); // To easily find the last user

            // 4. Prepare data for backend (without passphrase)
            const { passphrase, confirmPassphrase, ...submissionData } = formData;
            const finalData = {
                ...submissionData,
                public_key: publicKeyB64,
                country: selectedCountry?.name,
                state: State.getStateByCodeAndCountry(formData.state, selectedCountry!.isoCode)?.name
            };
            
            // 5. Call the onRegister prop to send data to the backend
            onRegister(finalData);

        } catch (err) {
            console.error("Registration error:", err);
            setError("An unexpected error occurred during key generation. Please try again.");
        }
    };

    return (
        <Container className="d-flex align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
            <Card style={{ width: '60rem' }}>
                <Card.Body>
                    <Card.Title as="h2" className="text-center mb-4">Create Your Anonymous Identity</Card.Title>
                    {error && <Alert variant="danger">{error}</Alert>}
                    <Form onSubmit={handleSubmit}>
                        <Row>
                            {/* Passphrase Fields */}
                            <Col md={6}><Form.Group className="mb-3">
                                <Form.Label>Passphrase</Form.Label>
                                <Form.Control type="password" name="passphrase" value={formData.passphrase} onChange={handleChange} required />
                                <Form.Text>This will be used to encrypt your private key in this browser. Do not forget it.</Form.Text>
                            </Form.Group></Col>
                            <Col md={6}><Form.Group className="mb-3">
                                <Form.Label>Confirm Passphrase</Form.Label>
                                <Form.Control type="password" name="confirmPassphrase" value={formData.confirmPassphrase} onChange={handleChange} required />
                            </Form.Group></Col>
                            
                            {/* Demographic Fields */}
                            <Col md={6}><Form.Group className="mb-3"><Form.Label>Age</Form.Label><Form.Control type="number" name="age" value={formData.age} onChange={handleChange} required /></Form.Group></Col>
                            <Col md={6}><Form.Group className="mb-3"><Form.Label>Sex</Form.Label><Form.Select name="sex" value={formData.sex} onChange={handleChange} required><option value="">Select Sex</option><option value="Male">Male</option><option value="Female">Female</option><option value="Other">Other</option></Form.Select></Form.Group></Col>
                            <Col md={6}><Form.Group className="mb-3"><Form.Label>Gender</Form.Label><Form.Select name="gender" value={formData.gender} onChange={handleChange} required><option value="">Select Gender</option><option value="Man">Man</option><option value="Woman">Woman</option><option value="Other">Other</option></Form.Select></Form.Group></Col>
                            <Col md={6}><Form.Group className="mb-3"><Form.Label>Country</Form.Label><Form.Select name="country" value={formData.country} onChange={handleChange} required><option value="">Select Country</option>{countries.map(c => <option key={c.isoCode} value={c.isoCode}>{c.name}</option>)}</Form.Select></Form.Group></Col>
                            <Col md={6}><Form.Group className="mb-3"><Form.Label>State</Form.Label><Form.Select name="state" value={formData.state} onChange={handleChange} required disabled={!selectedCountry}><option value="">Select State</option>{states.map(s => <option key={s.isoCode} value={s.isoCode}>{s.name}</option>)}</Form.Select></Form.Group></Col>
                            
                            {['religion', 'ethnicity', 'pincode', 'city', 'district', 'nationality'].map(key => (
                                <Col md={4} key={key}>
                                    <Form.Group className="mb-3">
                                        <Form.Label>{key.charAt(0).toUpperCase() + key.slice(1)}</Form.Label>
                                        <Form.Control type="text" name={key} placeholder={`Enter ${key}`} value={formData[key as keyof typeof formData]} onChange={handleChange} required={['pincode', 'city', 'district', 'nationality'].includes(key)} />
                                    </Form.Group>
                                </Col>
                            ))}
                        </Row>
                        <Button variant="primary" type="submit" className="w-100 mt-3">
                            Create Identity & Register
                        </Button>
                    </Form>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default RegistrationPage;
