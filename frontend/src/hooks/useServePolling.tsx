// src/hooks/useServePolling.ts
import { useEffect, useState } from "react";
import axios from "axios";

export default function useServePolling(intervalMs = 10000) {
  const [adMessage, setAdMessage] = useState(null);
  const [insightMessage, setInsightMessage] = useState(null);

  useEffect(() => {
    const fetchMessage = async () => {
      try {
        const res = await axios.get("/serve");
        if (res.data) {
          if (res.data.target) {
            setAdMessage(res.data);
          } else {
            setInsightMessage(res.data);
          }
        }
      } catch (err) {
        console.error("Error fetching serve message:", err);
      }
    };

    fetchMessage(); // initial pull
    const id = setInterval(fetchMessage, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return { adMessage, insightMessage };
}
