import React, { useState, useMemo } from 'react';
import { Row, Col, Alert, Form } from 'react-bootstrap';
import { Country, State } from 'country-state-city';
import { ICountry } from 'country-state-city/lib/interface';
import { generateKeyPair, encryptPrivateKey } from './crypto';
import { encodeBase64 } from 'tweetnacl-util';
import { AuthContainer, StyledButton } from './components/StyledComponents';

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
            const keyPair = generateKeyPair();
            const publicKeyB64 = encodeBase64(keyPair.publicKey);
            
            const encryptedPrivateKeyB64 = encryptPrivateKey(keyPair.secretKey, formData.passphrase);

            localStorage.setItem(`user_pk_${publicKeyB64}`, encryptedPrivateKeyB64);
            localStorage.setItem('last_user_pk', publicKeyB64);

            const { passphrase, confirmPassphrase, ...submissionData } = formData;
            const finalData = {
                ...submissionData,
                public_key: publicKeyB64,
                country: selectedCountry?.name,
                state: State.getStateByCodeAndCountry(formData.state, selectedCountry!.isoCode)?.name
            };
            
            onRegister(finalData);

        } catch (err) {
            console.error("Registration error:", err);
            setError("An unexpected error occurred during key generation. Please try again.");
        }
    };

    return (
        <AuthContainer style={{ maxWidth: '60rem' }}>
            <h2 style={{ textAlign: 'center', fontFamily: 'Garamond, serif', color: '#c5b358', marginBottom: '2rem' }}>
                Create Your Anonymous Identity
            </h2>
            {error && <Alert variant="danger">{error}</Alert>}
            <Form onSubmit={handleSubmit}>
                <p style={{ textAlign: 'center', marginBottom: '2rem', opacity: 0.8 }}>
                    Your identity is protected by a cryptographic key pair. Your passphrase encrypts this key in your browser. It is never sent to us.
                </p>
                <Row>
                    <Col md={6}><Form.Group className="mb-3">
                        <Form.Label>Passphrase</Form.Label>
                        <Form.Control type="password" name="passphrase" value={formData.passphrase} onChange={handleChange} required />
                        <Form.Text>At least 8 characters. You must remember this.</Form.Text>
                    </Form.Group></Col>
                    <Col md={6}><Form.Group className="mb-3">
                        <Form.Label>Confirm Passphrase</Form.Label>
                        <Form.Control type="password" name="confirmPassphrase" value={formData.confirmPassphrase} onChange={handleChange} required />
                    </Form.Group></Col>
                    
                    <Col md={12}><hr style={{ margin: '2rem 0', borderColor: '#4b3832' }} /></Col>

                    <Col md={6}><Form.Group className="mb-3"><Form.Label>Age</Form.Label><Form.Control type="number" name="age" value={formData.age} onChange={handleChange} required /></Form.Group></Col>
                    <Col md={6}><Form.Group className="mb-3"><Form.Label>Sex</Form.Label><Form.Select name="sex" value={formData.sex} onChange={handleChange} required><option value="">Select...</option><option value="Male">Male</option><option value="Female">Female</option><option value="Other">Other</option></Form.Select></Form.Group></Col>
                    <Col md={6}><Form.Group className="mb-3"><Form.Label>Gender</Form.Label><Form.Select name="gender" value={formData.gender} onChange={handleChange} required><option value="">Select...</option><option value="Man">Man</option><option value="Woman">Woman</option><option value="Other">Other</option></Form.Select></Form.Group></Col>
                    <Col md={6}><Form.Group className="mb-3"><Form.Label>Country</Form.Label><Form.Select name="country" value={formData.country} onChange={handleChange} required><option value="">Select...</option>{countries.map(c => <option key={c.isoCode} value={c.isoCode}>{c.name}</option>)}</Form.Select></Form.Group></Col>
                    <Col md={6}><Form.Group className="mb-3"><Form.Label>State</Form.Label><Form.Select name="state" value={formData.state} onChange={handleChange} required disabled={!selectedCountry}><option value="">Select...</option>{states.map(s => <option key={s.isoCode} value={s.isoCode}>{s.name}</option>)}</Form.Select></Form.Group></Col>
                    
                    {['religion', 'ethnicity', 'pincode', 'city', 'district', 'nationality'].map(key => (
                        <Col md={4} key={key}>
                            <Form.Group className="mb-3">
                                <Form.Label>{key.charAt(0).toUpperCase() + key.slice(1)}</Form.Label>
                                <Form.Control type="text" name={key} value={formData[key as keyof typeof formData]} onChange={handleChange} required={['pincode', 'city', 'district', 'nationality'].includes(key)} />
                            </Form.Group>
                        </Col>
                    ))}
                </Row>
                <StyledButton type="submit" style={{ width: '100%', marginTop: '2rem' }}>
                    Create Identity & Register
                </StyledButton>
            </Form>
        </AuthContainer>
    );
};

export default RegistrationPage;