import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNav from './TopNav';

const AppLayout = ({ user, memberships, onLogout }) => {
  return (
    <div className="flex h-screen bg-background overflow-hidden text-gray-200 font-sans selection:bg-primary/30">
      {/* Background ambient glow */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/5 blur-[120px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent/5 blur-[120px]" />
      </div>

      <Sidebar user={user} memberships={memberships} onLogout={onLogout} />
      
      <div className="flex-1 flex flex-col h-full overflow-hidden relative z-0">
        <TopNav user={user} />
        <main className="flex-1 overflow-y-auto p-8 animate-fade-in">
          <Outlet context={{ user, memberships }} />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
