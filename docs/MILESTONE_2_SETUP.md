# Milestone 2: Tauri v2 + React + TypeScript Setup

## Overview
This milestone sets up the frontend application using Tauri v2 with React and TypeScript.

## CLI Commands Used

```bash
# Install create-tauri-app globally
npm install -g create-tauri-app@latest

# Create Tauri app with React + TypeScript template
create-tauri-app frontend --template react-ts --manager npm --identifier ai.editflow.frontend --yes

# Install dependencies
cd frontend
npm install
```

## Directory Structure

```
frontend/
├── .gitignore              # Git ignore for Node.js/Tauri
├── .vscode/                # VS Code settings
│   └── extensions.json     # Recommended extensions
├── index.html              # Entry HTML file
├── package.json            # Node.js dependencies & scripts
├── public/                 # Static assets
│   ├── tauri.svg           # Tauri logo
│   └── vite.svg            # Vite logo
├── src/                    # React source code
│   ├── App.css             # App styles
│   ├── App.tsx             # Main React component
│   ├── assets/             # React & other assets
│   ├── main.tsx            # React entry point
│   └── vite-env.d.ts       # Vite type declarations
├── src-tauri/              # Rust backend for Tauri
│   ├── .gitignore          # Rust/Cargo ignore
│   ├── Cargo.toml          # Rust dependencies
│   ├── build.rs            # Build script
│   ├── capabilities/       # Tauri permissions
│   │   └── default.json    # Default capability config
│   ├── icons/              # App icons (various sizes)
│   ├── src/
│   │   ├── lib.rs          # Rust library (Tauri commands)
│   │   └── main.rs         # Rust entry point
│   └── tauri.conf.json     # Tauri configuration
├── tsconfig.json           # TypeScript config
├── tsconfig.node.json      # TypeScript Node config
└── vite.config.ts          # Vite bundler config
```

## Key Configuration Files

### package.json
- **Name**: editflow-frontend
- **Dependencies**: React 19, @tauri-apps/api v2
- **Dev Dependencies**: TypeScript 5.8, Vite 7, @tauri-apps/cli v2

### tauri.conf.json
- **Product Name**: EditFlow AI
- **Identifier**: ai.editflow.frontend
- **Window Size**: 1200x800 (resizable)
- **Build Commands**: 
  - Dev: `npm run dev` (Vite dev server on port 1420)
  - Build: `npm run build`

### src-tauri/src/lib.rs
Rust backend with Tauri commands:
- `greet(name: &str)` - Returns greeting message
- `get_app_version()` - Returns app version from Cargo.toml

## Available Scripts

```bash
# Development mode (runs Vite + Tauri)
npm run tauri dev

# Build for production
npm run tauri build

# Frontend only (without Tauri)
npm run dev        # Start Vite dev server
npm run build      # Build frontend
npm run preview    # Preview production build
```

## Prerequisites

Before running Tauri, ensure you have:

1. **Rust**: https://www.rust-lang.org/tools/install
2. **System Dependencies** (Linux):
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget \
     libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev \
     libsoup-3.0-dev libjavascriptcoregtk-4.1-dev
   ```

## Verification

To verify the setup is working:

1. Check that all files exist in the structure above
2. Run `npm install` successfully
3. (Optional) If Rust is installed, run `npm run tauri dev`

## Next Steps

- **Milestone 3**: Set up FastAPI Backend Skeleton
- **Milestone 4**: Connect Frontend to Backend (Hello World)

## Troubleshooting

### Missing Rust
```
Error: system is missing dependencies: Rust
```
Solution: Install Rust from https://rustup.rs/

### Missing webkit2gtk (Linux)
```
Error: system is missing dependencies: webkit2gtk & rsvg2
```
Solution: Install system dependencies as shown in Prerequisites above.

### Port Already in Use
If port 1420 is busy, edit `tauri.conf.json` and change `devUrl`.
