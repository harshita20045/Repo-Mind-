import React from 'react';
import LoginForm from '../components/LoginForm';

export default function LoginPage({ onLoginSuccess }) {
  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4 relative overflow-hidden font-sans">
      {/* Ambient background glow */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent/10 blur-[120px] pointer-events-none" />
      
      <div className="mb-8 text-center z-10 animate-fade-in">
        <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70 tracking-tight">RepoMind 2.0</h1>
        <p className="text-gray-400 text-sm mt-2 font-medium">Engineering Intelligence & PR Risk Assessment</p>
      </div>
      <LoginForm onLoginSuccess={onLoginSuccess} />
    </div>
  );
}
