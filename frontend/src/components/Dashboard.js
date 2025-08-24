import { useEffect, useState } from "react";
import API from "../services/api";

export default function Dashboard() {
  const [status, setStatus] = useState("");

  useEffect(() => {
    API.get("/health")
      .then((res) => setStatus(res.data.status))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      <p>API Status: {status}</p>
    </div>
  );
}
