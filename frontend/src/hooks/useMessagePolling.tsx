// src/hooks/useMessagePolling.ts
import { useEffect, useState } from "react";
import axios from "axios";

export default function useMessagePolling(type: "ad" | "insight", intervalMs = 10000) {
  const [message, setMessage] = useState(null);

  useEffect(() => {
    const fetchMessage = async () => {
      try {
        const res = await axios.get(`/serve`, { params: { type } });
        if (res.data) {
          setMessage(res.data);
        }
      } catch (err) {
        console.error(`Error fetching ${type}:`, err);
      }
    };

    fetchMessage(); // initial fetch
    const id = setInterval(fetchMessage, intervalMs);
    return () => clearInterval(id);
  }, [type, intervalMs]);

  return message;
}
