import { useState } from "react";
import reactLogo from "./assets/react.svg";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";

function App() {
  const [greetMsg, setGreetMsg] = useState("");
  const [name, setName] = useState("");
  const [appVersion, setAppVersion] = useState("");

  async function greet() {
    setGreetMsg(await invoke("greet", { name }));
  }

  async function loadVersion() {
    try {
      const version = await invoke("get_app_version");
      setAppVersion(version);
    } catch (e) {
      console.error("Failed to load version:", e);
    }
  }

  return (
    <main className="container">
      <h1>Welcome to EditFlow AI</h1>
      <p className="version-badge">v{appVersion || "loading..."}</p>

      <div className="row">
        <a href="https://vite.dev" target="_blank">
          <img src="/vite.svg" className="logo vite" alt="Vite logo" />
        </a>
        <a href="https://tauri.app" target="_blank">
          <img src="/tauri.svg" className="logo tauri" alt="Tauri logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <p>Click on the Tauri, Vite, and React logos to learn more.</p>

      <div className="info-box">
        <h2>Milestone 2: Tauri v2 + React + TypeScript Setup Complete</h2>
        <p>This is the foundation for your AI-powered video editor.</p>
      </div>

      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          greet();
        }}
      >
        <input
          id="greet-input"
          onChange={(e) => setName(e.currentTarget.value)}
          placeholder="Enter a name..."
        />
        <button type="submit" onClick={loadVersion}>Greet</button>
      </form>
      <p>{greetMsg}</p>
    </main>
  );
}

export default App;
