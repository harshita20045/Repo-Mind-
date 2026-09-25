import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNav from './TopNav';

const AppLayout = ({ user, memberships, onLogout }) => {
  return (
    <div className="flex h-screen overflow-hidden bg-background text-text-primary font-sans antialiased">
      {/* Sidebar */}
      <Sidebar user={user} memberships={memberships} onLogout={onLogout} />

      {/* Main content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0 bg-background relative">
        <TopNav user={user} />
        
        <main
          className="flex-1 overflow-y-auto"
          id="main-content"
          tabIndex={-1}
          aria-label="Main content"
        >
          <div className="p-6 lg:p-8 max-w-screen-2xl mx-auto animate-fade-in pb-16">
            <Outlet context={{ user, memberships }} />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
