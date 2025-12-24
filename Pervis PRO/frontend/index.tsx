import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { Loader2, AlertTriangle, RefreshCw } from 'lucide-react';
import { LanguageProvider } from './components/LanguageContext';
import { initDB } from './services/db';
import App from './App'; // Static Synchronous Import

// --- 1. Immediate DOM Check ---
const rootElement = document.getElementById('root');
if (!rootElement) {
    document.body.innerHTML = '<div style="color:red; padding:20px; font-family:sans-serif;"><h1>FATAL ERROR</h1><p>Root element #root not found in index.html</p></div>';
    throw new Error("Root element not found");
}

// --- 2. Error Screen Component ---
const ErrorScreen = ({ error }: { error: any }) => (
    <div className="flex flex-col items-center justify-center h-screen bg-zinc-950 text-red-500 p-8 font-mono">
        <AlertTriangle size={48} className="mb-4" />
        <h1 className="text-xl font-bold mb-2">System Critical Error</h1>
        <p className="text-sm text-zinc-500 mb-6 text-center">
            The application encountered an error during the boot sequence.
        </p>
        <pre className="bg-black/50 p-4 rounded border border-red-900/30 text-xs w-full max-w-2xl overflow-auto text-zinc-300 mb-6">
            {error?.toString() || "Unknown Error"}
        </pre>
        <button 
            onClick={() => {
                if(confirm("This will reset local configurations (assets are preserved in DB). Continue?")) {
                    localStorage.clear();
                    window.location.reload();
                }
            }}
            className="flex items-center gap-2 px-6 py-2 bg-red-900/20 hover:bg-red-900/40 border border-red-900/50 rounded text-red-200 transition-colors cursor-pointer"
        >
            <RefreshCw size={14} /> Emergency Reset & Reload
        </button>
    </div>
);

// --- 3. Loading Screen Component ---
const LoadingScreen = ({ message }: { message: string }) => (
    <div className="flex flex-col items-center justify-center h-screen bg-zinc-950 text-yellow-500 font-mono">
        <Loader2 size={32} className="animate-spin mb-4" />
        <div className="text-xs font-bold uppercase tracking-widest mb-1">PREVIS PRO</div>
        <div className="text-[10px] text-zinc-500">{message}</div>
    </div>
);

// --- 4. Bootstrap Component ---
const Bootstrap: React.FC = () => {
    const [isReady, setIsReady] = useState(false);
    const [initError, setInitError] = useState<any>(null);

    useEffect(() => {
        const boot = async () => {
            try {
                console.log("[Boot] Starting System...");
                
                // Initialize IndexedDB
                console.log("[Boot] Initializing Asset Database...");
                await initDB();
                
                // Artificial delay to prevent flash and ensure styles load
                await new Promise(resolve => setTimeout(resolve, 500));
                
                console.log("[Boot] System Ready.");
                setIsReady(true);
            } catch (e) {
                console.error("[Boot] Initialization Failed:", e);
                setInitError(e);
            }
        };
        boot();
    }, []);

    if (initError) {
        return <ErrorScreen error={initError} />;
    }

    if (!isReady) {
        return <LoadingScreen message="Initializing Asset Engine..." />;
    }

    return (
        <React.StrictMode>
            <LanguageProvider>
                <App />
            </LanguageProvider>
        </React.StrictMode>
    );
};

// --- 5. Mount ---
try {
    const root = ReactDOM.createRoot(rootElement);
    root.render(<Bootstrap />);
    console.log("[Boot] React Root Mounted.");
} catch (e) {
    console.error("[Boot] React Mount Failed:", e);
    rootElement.innerHTML = `<div style="color:red; padding:20px;"><h1>REACT MOUNT FAILED</h1><pre>${e}</pre></div>`;
}