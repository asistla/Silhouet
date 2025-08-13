
import { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../config';

interface PollingHook<T> {
  data: T[];
  isLoading: boolean;
  error: Error | null;
}

export function usePolling<T>(endpoint: string, pollInterval: number = 5000): PollingHook<T> {
  const [data, setData] = useState<T[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  
  // Use a ref to store the latest data to avoid stale closures in the polling callback
  const dataRef = useRef(data);
  dataRef.current = data;

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Construct the full URL
        const url = `${API_BASE_URL}${endpoint}`;
        
        // Fetch the data
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const newItem = await response.json();

        // Add the new item to the list if it's not null or empty
        if (newItem) {
          // Using the ref to get the current state
          setData(prevData => [...prevData, newItem]);
        }

      } catch (e) {
        if (e instanceof Error) {
          setError(e);
        }
      } finally {
        setIsLoading(false);
      }
    };

    // Initial fetch
    fetchData();

    // Set up the polling interval
    const intervalId = setInterval(fetchData, pollInterval);

    // Clean up the interval on component unmount
    return () => clearInterval(intervalId);
  }, [endpoint, pollInterval]);

  return { data, isLoading, error };
}
