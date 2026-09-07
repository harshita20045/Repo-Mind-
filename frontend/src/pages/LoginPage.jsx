import React from 'react';
import LoginForm from '../components/LoginForm';

export default function LoginPage({ onLoginSuccess }) {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
      <div className="mb-6 text-center">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">RepoMind</h1>
        <p className="text-slate-400 text-sm mt-1">Autonomous Grounded PR Review & Risk Intelligence</p>
      </div>
      <LoginForm onLoginSuccess={onLoginSuccess} />
    </div>
  );
}
