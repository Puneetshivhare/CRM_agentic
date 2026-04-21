"use client";

export default function TestPage() {
  return (
    <div style={{
      background: "#050505",
      color: "#f0f0f0",
      minHeight: "100vh",
      padding: "40px",
      fontFamily: "system-ui, sans-serif"
    }}>
      <h1 style={{ fontSize: "32px", marginBottom: "20px" }}>✅ Frontend Works!</h1>

      <div style={{ marginBottom: "30px" }}>
        <p>If you see this page, Next.js build is working.</p>
        <p>Current time: {new Date().toLocaleTimeString()}</p>
      </div>

      <button
        onClick={() => alert("✅ Button click works!")}
        style={{
          background: "#00f2ff",
          color: "#050505",
          padding: "12px 24px",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          fontSize: "16px",
          fontWeight: "bold",
          marginRight: "10px"
        }}
      >
        Click Me Test
      </button>

      <button
        onClick={() => {
          fetch('http://localhost:8005/api/health')
            .then(r => r.json())
            .then(d => alert("✅ Backend connected: " + JSON.stringify(d)))
            .catch(e => alert("❌ Backend error: " + e.message))
        }}
        style={{
          background: "#bfff00",
          color: "#050505",
          padding: "12px 24px",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          fontSize: "16px",
          fontWeight: "bold"
        }}
      >
        Test Backend Connection
      </button>

      <div style={{ marginTop: "40px", fontSize: "14px", color: "#f0f0f0aa" }}>
        <p>Try:</p>
        <ul>
          <li>Click "Click Me Test" - should show alert</li>
          <li>Click "Test Backend Connection" - should test API</li>
          <li>Open DevTools (F12) → Console for errors</li>
        </ul>
      </div>
    </div>
  );
}
