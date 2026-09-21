import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNav from './TopNav';

const AppLayout = ({ user, memberships, onLogout }) => {
  return (
    <div className="flex h-screen overflow-hidden bg-background text-text-primary font-sans">
      {/* Subtle ambient background */}
      <div className="fixed inset-0 pointer-events-none -z-10" aria-hidden="true">
        <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full bg-primary/[0.04] blur-[100px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 rounded-full bg-accent/[0.03] blur-[100px]" />
      </div>

      {/* Sidebar */}
      <Sidebar user={user} memberships={memberships} onLogout={onLogout} />

      {/* Main content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0">
        <TopNav user={user} />
        <main
          className="flex-1 overflow-y-auto"
          id="main-content"
          tabIndex={-1}
          aria-label="Main content"
        >
          <div className="p-6 lg:p-8 max-w-screen-2xl mx-auto animate-fade-in">
            <Outlet context={{ user, memberships }} />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
