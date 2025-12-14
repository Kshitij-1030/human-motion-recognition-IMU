"use client";
import { useEffect, useState } from "react";

export default function Home() {
  const [data, setData] = useState({ x: 0, y: 0, z: 0, timestamp: 0 });

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch("http://localhost:8000/api/sensor");
        const newData = await response.json();
        setData(newData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    }, 100); // Update every 100ms

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "20px", fontFamily: "monospace" }}>
      <h1>Acceleration Data</h1>
      <div style={{ fontSize: "24px" }}>
        <p>X: {data.x.toFixed(2)} m/s²</p>
        <p>Y: {data.y.toFixed(2)} m/s²</p>
        <p>Z: {data.z.toFixed(2)} m/s²</p>
        <p>Time: {data.timestamp.toFixed(2)} s</p>
      </div>
    </div>
  );
}
