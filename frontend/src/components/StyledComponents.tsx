
import React from 'react';

export const MainContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{
        display: 'flex',
        height: '100vh',
        backgroundColor: '#2d2d2d',
        color: '#e8e4d5',
        fontFamily: 'Georgia, serif',
    }}>
        {children}
    </div>
);

export const LeftPanel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{
        width: '20%', // Adjusted for better usability
        padding: '2rem',
        borderRight: '1px solid #4b3832',
        boxShadow: '5px 0 15px -5px rgba(0,0,0,0.5)',
        overflowY: 'auto'
    }}>
        {children}
    </div>
);

export const CenterPanel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{
        width: '50%', // Adjusted
        padding: '2rem',
        display: 'flex',
        flexDirection: 'column',
    }}>
        {children}
    </div>
);

export const RightPanel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <div style={{
        width: '30%',
        padding: '2rem',
        borderLeft: '1px solid #4b3832',
        backgroundColor: '#352a25', // Slightly different shade for depth
        overflowY: 'auto'
    }}>
        {children}
    </div>
);

export const TextArea: React.FC<any> = (props) => (
    <textarea {...props} style={{
        flexGrow: 1,
        width: '100%',
        backgroundColor: '#f5f5dc',
        color: '#3d3d3d',
        border: '1px solid #c5b358',
        borderRadius: '4px',
        padding: '1rem',
        fontFamily: 'Georgia, serif',
        fontSize: '1.1rem',
        lineHeight: 1.7,
        boxShadow: 'inset 0 0 10px rgba(0,0,0,0.2)',
        resize: 'none',
        outline: 'none'
    }} />
);

export const StyledButton: React.FC<any> = (props) => (
    <button {...props} style={{
        backgroundColor: '#b87333',
        color: '#f5f5dc',
        border: 'none',
        padding: '8px 16px',
        borderRadius: '4px',
        cursor: 'pointer',
        fontFamily: 'Garamond, serif',
        fontSize: '0.9rem',
        textTransform: 'uppercase',
        letterSpacing: '1px',
        boxShadow: '0 2px 5px rgba(0,0,0,0.3)',
        transition: 'background-color 0.3s ease',
        ...props.style
    }} onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#c5b358'}
       onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#b87333'}
    />
);

export const AuthContainer: React.FC<{ children: React.ReactNode, style?: React.CSSProperties }> = ({ children, style }) => (
    <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#2d2d2d',
        padding: '2rem',
        fontFamily: 'Georgia, serif',
    }}>
        <div style={{
            width: '100%',
            maxWidth: '40rem',
            padding: '3rem',
            backgroundColor: '#352a25',
            borderRadius: '8px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
            border: '1px solid #4b3832',
            color: '#e8e4d5',
            ...style
        }}>
            {children}
        </div>
    </div>
);
