// src/components/ui/FilterPanel.tsx
import React from 'react';
import { Form } from 'react-bootstrap';
import { StyledButton } from '../StyledComponents';

interface FilterPanelProps {
  filters: Record<string, string | number>;
  onChange: React.ChangeEventHandler<HTMLInputElement>;
  onApply: () => void;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({ filters, onChange, onApply }) => (
  <>
    <h2>Filters</h2>
    <Form>
      {Object.keys(filters).map(key => (
        <Form.Group key={key} className="filter-group">
          <Form.Label>{key.replace(/_/g, ' ')}</Form.Label>
          <Form.Control
            type={key.includes('age') ? 'number' : 'text'}
            name={key}
            value={filters[key]}
            onChange={onChange}
            size="sm"
          />
        </Form.Group>
      ))}
    </Form>
    <StyledButton onClick={onApply} style={{ width: '100%', marginTop: 'auto' }}>
      Apply Filters
    </StyledButton>
  </>
);
